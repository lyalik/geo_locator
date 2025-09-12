#!/usr/bin/env python3
"""
Главный сервис агрегации геолокации
Объединяет все источники данных для максимально точного определения местоположения
"""
import os
import logging
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import json

from .yandex_maps_service import YandexMapsService
from .dgis_service import DGISService
from .roscosmos_satellite_service import RoscosmosService
from .yandex_satellite_service import YandexSatelliteService
from .osm_overpass_service import OSMOverpassService
from .image_database_service import ImageDatabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Circular import fix - import GeoLocationService only when needed

class GeoAggregatorService:
    """
    Главный сервис геолокации, объединяющий все источники данных:
    - EXIF данные из фотографий
    - Yandex Maps API
    - 2GIS API  
    - OpenStreetMap API (для точности определения застроек)
    - Роскосмос спутниковые снимки
    - Яндекс Спутник API
    - Собственная база данных изображений
    - Алгоритмы сопоставления изображений
    """
    
    def __init__(self):
        self.yandex_service = YandexMapsService()
        self.dgis_service = DGISService()
        self.roscosmos_service = RoscosmosService()
        self.yandex_satellite_service = YandexSatelliteService()
        self.image_db_service = ImageDatabaseService()
        self.osm_service = OSMOverpassService()
        # Lazy import to avoid circular dependency
        self.geo_service = None
        
        # Веса для различных источников данных
        self.source_weights = {
            'exif_gps': 1.0,        # Наивысший приоритет - GPS из EXIF
            'image_match': 0.9,     # Сопоставление с базой изображений
            'satellite_match': 0.8, # Сопоставление со спутниковыми снимками
            'osm_buildings': 0.75,  # OpenStreetMap данные о зданиях
            'yandex_search': 0.7,   # Поиск через Yandex Maps
            'dgis_search': 0.7,     # Поиск через 2GIS
            'osm_geocoding': 0.65,  # OpenStreetMap геокодирование
            'manual_input': 0.6     # Ручной ввод пользователя
        }
    
    def locate_image(self, image_path: str, location_hint: str = None, 
                    user_description: str = None) -> Dict[str, Any]:
        """
        Главная функция определения местоположения изображения
        
        Args:
            image_path: Путь к изображению
            location_hint: Подсказка о местоположении (например, "Москва, Красная площадь")
            user_description: Описание того, что изображено
        """
        results = {
            'success': False,
            'final_location': None,
            'confidence_score': 0.0,
            'sources_used': [],
            'all_results': {},
            'recommendations': []
        }
        
        try:
            logger.info(f"Starting geolocation for image: {image_path}")
            
            # 1. Извлечение EXIF GPS данных
            exif_result = self._extract_exif_location(image_path)
            if exif_result['success']:
                results['all_results']['exif'] = exif_result
                results['sources_used'].append('exif_gps')
                logger.info("GPS coordinates found in EXIF data")
            
            # 2. Поиск в собственной базе изображений
            db_result = self._search_image_database(image_path, exif_result)
            if db_result['success']:
                results['all_results']['image_database'] = db_result
                results['sources_used'].append('image_match')
                logger.info(f"Found {len(db_result.get('similar_images', []))} similar images in database")
            
            # 3. Поиск через внешние API (если есть подсказка о местоположении)
            if location_hint:
                api_results = self._search_external_apis(location_hint, user_description)
                results['all_results']['external_apis'] = api_results
                logger.info(f"API results: {api_results}")
                if api_results['yandex']['success']:
                    results['sources_used'].append('yandex_search')
                    logger.info(f"Yandex places found: {len(api_results['yandex'].get('places', []))}")
                if api_results['dgis']['success']:
                    results['sources_used'].append('dgis_search')
            
            # 4. Сопоставление со спутниковыми снимками
            if exif_result['success'] or (location_hint and results['all_results'].get('external_apis')):
                satellite_result = self._match_with_satellite(image_path, results['all_results'])
                if satellite_result['success']:
                    results['all_results']['satellite'] = satellite_result
                    results['sources_used'].append('satellite_match')
                    logger.info(f"Satellite match score: {satellite_result.get('match_score', 0)}")
            
            # 5. Агрегация результатов и выбор лучшего
            logger.info(f"All results before aggregation: {results['all_results']}")
            
            # Детальная диагностика external_apis
            if 'external_apis' in results['all_results']:
                ext_apis = results['all_results']['external_apis']
                logger.info(f"External APIs details:")
                for api_name, api_data in ext_apis.items():
                    logger.info(f"  {api_name}: success={api_data.get('success')}, places_count={len(api_data.get('places', []))}")
                    if api_data.get('places'):
                        first_place = api_data['places'][0]
                        logger.info(f"    First place coordinates: {first_place.get('coordinates')}")
            
            final_location = self._aggregate_results(results['all_results'])
            logger.info(f"Final location after aggregation: {final_location}")
            if final_location:
                results['success'] = True
                results['final_location'] = final_location
                results['confidence_score'] = final_location['confidence']
                
                # Добавляем изображение в базу данных
                self._add_to_database(image_path, final_location, user_description)
            
            # 6. Генерация рекомендаций
            results['recommendations'] = self._generate_recommendations(results)
            
            logger.info(f"Geolocation completed. Success: {results['success']}, "
                       f"Confidence: {results['confidence_score']:.2f}")
            
        except Exception as e:
            logger.error(f"Error in geolocation process: {e}")
            results['error'] = str(e)
        
        return results
    
    def _extract_exif_location(self, image_path: str) -> Dict[str, Any]:
        """Извлечение GPS координат из EXIF данных"""
        try:
            # Lazy import to avoid circular dependency
            if self.geo_service is None:
                from .geolocation_service import GeoLocationService
                self.geo_service = GeoLocationService()
            
            result = self.geo_service.process_image(image_path)
            if result['success'] and result['has_gps']:
                return {
                    'success': True,
                    'source': 'exif_gps',
                    'coordinates': result['coordinates'],
                    'address': result.get('address'),
                    'confidence': 1.0  # Максимальная уверенность для EXIF GPS
                }
        except Exception as e:
            logger.error(f"Error extracting EXIF location: {e}")
        
        return {'success': False, 'source': 'exif_gps'}
    
    def _search_image_database(self, image_path: str, exif_result: Dict) -> Dict[str, Any]:
        """Поиск похожих изображений в собственной базе"""
        try:
            # Если есть GPS координаты, ищем рядом
            if exif_result.get('success'):
                coords = exif_result['coordinates']
                similar_images = self.image_db_service.find_similar_images(
                    coords['latitude'], coords['longitude'], radius=1000
                )
            else:
                # Поиск по визуальному сходству (упрощенная версия)
                similar_images = []
            
            if similar_images:
                # Берем ближайшее изображение как основу
                best_match = similar_images[0]
                return {
                    'success': True,
                    'source': 'image_database',
                    'coordinates': best_match['coordinates'],
                    'similar_images': similar_images,
                    'confidence': max(0.5, 1.0 - (best_match['distance'] / 1000))  # Чем ближе, тем выше уверенность
                }
        except Exception as e:
            logger.error(f"Error searching image database: {e}")
        
        return {'success': False, 'source': 'image_database'}
    
    def _search_external_apis(self, location_hint: str, user_description: str = None) -> Dict[str, Any]:
        """Поиск через внешние API сервисы"""
        results = {
            'yandex': {'success': False},
            'dgis': {'success': False},
            'osm': {'success': False}
        }
        
        # Валидация и очистка location_hint
        if not location_hint or location_hint.strip() == "" or location_hint.lower() in ['detected objects', 'none', 'null']:
            logger.warning(f"Invalid location hint: '{location_hint}', skipping external API search")
            return results
        
        try:
            # Yandex Maps поиск
            yandex_result = self.yandex_service.search_places(location_hint.strip())
            if yandex_result.get('success'):
                results['yandex'] = yandex_result
                logger.info(f"Yandex found {yandex_result.get('total_found', 0)} places")
        except Exception as e:
            logger.error(f"Yandex search failed: {e}")
            results['yandex']['error'] = str(e)
        
        try:
            # 2GIS поиск
            dgis_result = self.dgis_service.search_places(location_hint.strip())
            if dgis_result.get('success') and dgis_result.get('places'):
                place = dgis_result['places'][0]
                if place.get('coordinates'):
                    results['dgis'] = {
                        'success': True,
                        'source': 'dgis',
                        'coordinates': place['coordinates'],
                        'place_info': place,
                        'confidence': 0.7
                    }
                    logger.info(f"2GIS found place: {place.get('name', 'Unknown')}")
        except Exception as e:
            logger.error(f"2GIS search failed: {e}")
            results['dgis']['error'] = str(e)
        
        try:
            # OpenStreetMap Overpass поиск по названию
            osm_result = self.osm_service.search_by_name(location_hint.strip())
            if osm_result.get('success') and osm_result.get('objects'):
                # Берем первый найденный объект с координатами
                for obj in osm_result['objects']:
                    if obj.get('coordinates'):
                        coords = obj['coordinates']
                        results['osm'] = {
                            'success': True,
                            'source': 'osm_overpass',
                            'coordinates': {
                                'latitude': coords['lat'],
                                'longitude': coords['lon']
                            },
                            'place_info': {
                                'name': obj.get('name', 'Unknown OSM Object'),
                                'type': obj.get('type', 'unknown'),
                                'tags': obj.get('tags', {})
                            },
                            'confidence': 0.65
                        }
                        logger.info(f"OSM found object: {obj.get('name', 'Unknown')}")
                        break
        except Exception as e:
            logger.error(f"OSM Overpass search failed: {e}")
            results['osm'] = {'error': str(e)}
        
        return results
    
    def _match_with_satellite(self, image_path: str, all_results: Dict) -> Dict[str, Any]:
        """Сопоставление с спутниковыми снимками"""
        try:
            # Получаем координаты из лучшего доступного источника
            coordinates = None
            
            if all_results.get('exif', {}).get('success'):
                coordinates = all_results['exif'].get('coordinates')
            elif all_results.get('external_apis', {}).get('yandex', {}).get('success'):
                coordinates = all_results['external_apis']['yandex'].get('coordinates')
            elif all_results.get('external_apis', {}).get('dgis', {}).get('success'):
                coordinates = all_results['external_apis']['dgis'].get('coordinates')
            
            if not coordinates:
                return {'success': False, 'source': 'satellite'}
            
            # Получаем спутниковый снимок через российские сервисы
            satellite_image = self._get_best_satellite_image(
                coordinates['latitude'], 
                coordinates['longitude']
            )
            
            if satellite_image.get('success'):
                # Сравниваем изображения (упрощенная версия)
                match_score = self._compare_with_satellite(image_path, satellite_image)
                
                return {
                    'success': True,
                    'source': 'satellite',
                    'coordinates': coordinates,
                    'match_score': match_score,
                    'satellite_image': satellite_image,
                    'confidence': match_score / 100.0  # Преобразуем в диапазон 0-1
                }
        
        except Exception as e:
            logger.error(f"Error matching with satellite: {e}")
        
        return {'success': False, 'source': 'satellite'}
    
    def _compare_with_satellite(self, image_path: str, satellite_data: Dict) -> float:
        """Сравнение изображения со спутниковым снимком"""
        try:
            # Упрощенная версия сравнения
            # В реальном проекте здесь должен быть более сложный алгоритм
            # сравнения изображений с использованием CV и ML
            
            # Пока возвращаем случайный результат для демонстрации
            import random
            return random.uniform(30, 85)  # Имитация результата сравнения
            
        except Exception as e:
            logger.error(f"Error comparing with satellite: {e}")
            return 0.0
    
    def _aggregate_results(self, all_results: Dict) -> Optional[Dict[str, Any]]:
        """Агрегация результатов из всех источников"""
        try:
            candidates = []
            
            # Собираем всех кандидатов с их весами
            for source_type, data in all_results.items():
                if source_type == 'exif' and data.get('success'):
                    candidates.append({
                        'coordinates': data['coordinates'],
                        'source': 'exif_gps',
                        'weight': self.source_weights['exif_gps'],
                        'confidence': data.get('confidence', 1.0),
                        'address': data.get('address')
                    })
                
                elif source_type == 'image_database' and data.get('success'):
                    candidates.append({
                        'coordinates': data['coordinates'],
                        'source': 'image_match',
                        'weight': self.source_weights['image_match'],
                        'confidence': data.get('confidence', 0.8),
                        'similar_count': len(data.get('similar_images', []))
                    })
                
                elif source_type == 'external_apis':
                    for api_name, api_data in data.items():
                        if api_data.get('success'):
                            # Проверяем координаты в places массиве
                            places = api_data.get('places', [])
                            if places and len(places) > 0:
                                first_place = places[0]
                                coordinates = first_place.get('coordinates')
                                if coordinates:
                                    source_key = f"{api_name}_search"
                                    candidates.append({
                                        'coordinates': coordinates,
                                        'source': source_key,
                                        'weight': self.source_weights.get(source_key, 0.7),
                                        'confidence': api_data.get('confidence', 0.7),
                                        'place_info': first_place
                                    })
                                    logger.info(f"Added candidate from {api_name}: {coordinates}")
                            # Fallback: проверяем координаты напрямую в api_data
                            elif api_data.get('coordinates'):
                                source_key = f"{api_name}_search"
                                candidates.append({
                                    'coordinates': api_data.get('coordinates'),
                                    'source': source_key,
                                    'weight': self.source_weights.get(source_key, 0.7),
                                    'confidence': api_data.get('confidence', 0.7),
                                    'place_info': api_data.get('place_info')
                                })
                                logger.info(f"Added fallback candidate from {api_name}: {api_data.get('coordinates')}")
                
                elif source_type == 'satellite' and data.get('success'):
                    candidates.append({
                        'coordinates': data['coordinates'],
                        'source': 'satellite_match',
                        'weight': self.source_weights['satellite_match'],
                        'confidence': data.get('confidence', 0.8),
                        'match_score': data.get('match_score', 0)
                    })
            
            if not candidates:
                return None
            
            # Выбираем лучшего кандидата по взвешенной уверенности
            best_candidate = max(candidates, 
                               key=lambda x: x['weight'] * x['confidence'])
            
            # Если есть несколько близких кандидатов, усредняем координаты
            if len(candidates) > 1:
                close_candidates = [c for c in candidates 
                                 if self._calculate_distance(
                                     best_candidate['coordinates']['latitude'],
                                     best_candidate['coordinates']['longitude'],
                                     c['coordinates']['latitude'],
                                     c['coordinates']['longitude']
                                 ) < 500]  # В радиусе 500 метров
                
                if len(close_candidates) > 1:
                    # Усредняем координаты с учетом весов
                    total_weight = sum(c['weight'] * c['confidence'] for c in close_candidates)
                    avg_lat = sum(c['coordinates']['latitude'] * c['weight'] * c['confidence'] 
                                for c in close_candidates) / total_weight
                    avg_lon = sum(c['coordinates']['longitude'] * c['weight'] * c['confidence'] 
                                for c in close_candidates) / total_weight
                    
                    best_candidate['coordinates'] = {
                        'latitude': avg_lat,
                        'longitude': avg_lon
                    }
                    best_candidate['confidence'] = min(1.0, best_candidate['confidence'] + 0.1)
                    best_candidate['sources_combined'] = [c['source'] for c in close_candidates]
            
            return best_candidate
            
        except Exception as e:
            logger.error(f"Error aggregating results: {e}")
            return None
    
    def _add_to_database(self, image_path: str, location: Dict, description: str = None):
        """Добавление изображения в базу данных"""
        try:
            # Добавляем изображение в базу данных
            add_result = self.image_db_service.add_image(image_path, description)
            
            if add_result.get('success'):
                image_id = add_result['image_id']
                
                # Обновляем геолокацию, если она была определена не из EXIF
                if location['source'] != 'exif_gps':
                    self.image_db_service.update_location(
                        image_id,
                        location['coordinates']['latitude'],
                        location['coordinates']['longitude'],
                        location['source']
                    )
                
                logger.info(f"Image added to database with ID: {image_id}")
        
        except Exception as e:
            logger.error(f"Error adding image to database: {e}")
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Генерация рекомендаций для пользователя"""
        recommendations = []
        
        try:
            if not results['success']:
                recommendations.append("Не удалось определить местоположение автоматически")
                recommendations.append("Попробуйте указать примерное местоположение или описание")
                
                if not results['sources_used']:
                    recommendations.append("В изображении отсутствуют GPS данные")
                    recommendations.append("Рассмотрите возможность включения геотегов в настройках камеры")
            
            else:
                confidence = results['confidence_score']
                
                if confidence < 0.5:
                    recommendations.append("Низкая уверенность в определении местоположения")
                    recommendations.append("Рекомендуется проверить результат вручную")
                
                elif confidence < 0.8:
                    recommendations.append("Средняя уверенность в результате")
                    recommendations.append("Для повышения точности добавьте описание места")
                
                else:
                    recommendations.append("Высокая уверенность в определении местоположения")
                
                # Рекомендации по источникам данных
                if 'exif_gps' in results['sources_used']:
                    recommendations.append("Использованы GPS координаты из изображения")
                
                if 'image_match' in results['sources_used']:
                    recommendations.append("Найдены похожие изображения в базе данных")
                
                if len(results['sources_used']) > 2:
                    recommendations.append("Результат подтвержден несколькими источниками")
        
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        return recommendations
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Вычисление расстояния между двумя точками в метрах"""
        import math
        
        R = 6371000  # Радиус Земли в метрах
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) * math.sin(delta_lon / 2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _get_best_satellite_image(self, lat: float, lon: float, zoom: int = 16) -> Dict[str, Any]:
        """
        Получение лучшего доступного спутникового снимка из российских источников
        Приоритет: Роскосмос (основной) → Яндекс → 2ГИС → OSM (вспомогательные)
        """
        try:
            # 1. Основной источник - Роскосмос (максимальный приоритет)
            if self.roscosmos_service:
                try:
                    result = self.roscosmos_service.get_satellite_image(lat, lon, zoom)
                    if result.get('success') and result.get('image_url'):
                        logger.info(f"Successfully retrieved satellite image from Roscosmos (primary source)")
                        result['priority'] = 'primary'
                        result['quality_score'] = result.get('quality_score', 0.95)  # Высокое качество
                        return result
                except Exception as e:
                    logger.warning(f"Roscosmos service failed: {e}, trying fallback sources")
                    
            # 2. Вспомогательные сервисы (по приоритету)
            fallback_services = [
                {
                    'service': self.yandex_satellite_service,
                    'name': 'Яндекс Спутник',
                    'quality_score': 0.8
                },
                {
                    'service': self.dgis_service if hasattr(self.dgis_service, 'get_satellite_image') else None,
                    'name': '2ГИС',
                    'quality_score': 0.75
                }
            ]
            
            for fallback in fallback_services:
                if fallback['service']:
                    try:
                        result = fallback['service'].get_satellite_image(lat, lon, zoom)
                        if result.get('success') and result.get('image_url'):
                            logger.info(f"Retrieved satellite image from {fallback['name']} (fallback)")
                            result['priority'] = 'fallback'
                            result['quality_score'] = fallback['quality_score']
                            return result
                    except Exception as e:
                        logger.warning(f"{fallback['name']} service failed: {e}")
                        continue
                        
            # 3. Последняя заглушка (аварийный режим)
            logger.warning("Все спутниковые сервисы недоступны, используем аварийную заглушку")
            return {
                'success': True,
                'image_url': f'https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&z={zoom}&l=sat&size=650,450&format=png',
                'source': 'Аварийный режим (Яндекс)',
                'priority': 'emergency',
                'quality_score': 0.4
            }
            
        except Exception as e:
            logger.error(f"Critical error in satellite image retrieval: {e}")
            return {
                'success': False,
                'error': str(e),
                'priority': 'error'
            }
    
    def get_location_statistics(self) -> Dict[str, Any]:
        """Получение статистики по геолокации"""
        try:
            # Проверяем доступность базы данных
            if not self.image_db_service or not self.image_db_service.session:
                return {
                    'total_images': 0,
                    'images_with_gps': 0,
                    'gps_coverage': 0,
                    'available_services': {
                        'yandex_maps': hasattr(self.yandex_service, 'api_key') and bool(self.yandex_service.api_key),
                        'dgis': hasattr(self.dgis_service, 'api_key') and bool(self.dgis_service.api_key),
                        'roscosmos_satellite': True,  # Российские спутниковые данные
                        'yandex_satellite': hasattr(self.yandex_satellite_service, 'api_key') and bool(self.yandex_satellite_service.api_key),
                        'image_database': False
                    }
                }
            
            # Статистика из базы данных изображений (упрощенная версия)
            try:
                from .image_database_service import GeoImage
                images_with_gps = self.image_db_service.session.query(
                    GeoImage
                ).filter_by(has_gps=True).count()
                
                total_images = self.image_db_service.session.query(
                    GeoImage
                ).count()
            except Exception as db_error:
                logger.warning(f"Database query failed: {db_error}")
                images_with_gps = 0
                total_images = 0
            
            return {
                'total_images': total_images,
                'images_with_gps': images_with_gps,
                'gps_coverage': (images_with_gps / total_images * 100) if total_images > 0 else 0,
                'available_services': {
                    'yandex_maps': hasattr(self.yandex_service, 'api_key') and bool(self.yandex_service.api_key),
                    'dgis': hasattr(self.dgis_service, 'api_key') and bool(self.dgis_service.api_key),
                    'roscosmos_satellite': True,  # Российские спутниковые данные
                    'yandex_satellite': hasattr(self.yandex_satellite_service, 'api_key') and bool(self.yandex_satellite_service.api_key),
                    'osm_overpass': True,  # OpenStreetMap Overpass API
                    'image_database': True
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {'error': str(e)}


# Пример использования
if __name__ == "__main__":
    service = GeoAggregatorService()
    
    # Тест геолокации изображения
    result = service.locate_image(
        "/path/to/image.jpg",
        location_hint="Москва, Красная площадь",
        user_description="Фотография Кремля"
    )
    
    print("Geolocation result:", json.dumps(result, indent=2, ensure_ascii=False))
