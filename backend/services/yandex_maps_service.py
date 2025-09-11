#!/usr/bin/env python3
"""
Yandex Maps API Service для геолокации и поиска объектов
"""
import os
import logging
import requests
import json
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class YandexMapsService:
    """
    Сервис для работы с Yandex Maps API
    - Поиск объектов и адресов
    - Получение панорам
    - Геокодирование и обратное геокодирование
    - Статические карты
    """
    
    def __init__(self):
        self.api_key = os.getenv('YANDEX_API_KEY')
        self.base_url = 'https://search-maps.yandex.ru'
        self.geocoder_url = 'https://geocode-maps.yandex.ru/1.x/'
        self.static_url = 'https://static-maps.yandex.ru/1.x/'
        self.panorama_url = 'https://api-maps.yandex.ru/services/panoramas/1.x/'
        
        if not self.api_key:
            logger.warning("YANDEX_API_KEY not found in environment variables")
    
    def search_places(self, query: str, lat: Optional[float] = None, lon: Optional[float] = None, radius: int = 5000) -> Dict[str, Any]:
        """
        Поиск мест и объектов через Yandex Geocoder API (используем работающий API)
        
        Args:
            query: Поисковый запрос
            lat, lon: Координаты центра поиска
            radius: Радиус поиска в метрах
        """
        try:
            # Проверяем валидность запроса
            if not query or query.strip() == "" or query.lower() in ['detected objects', 'none', 'null']:
                logger.warning(f"Invalid search query: '{query}', using fallback")
                query = "достопримечательность"
            
            # Используем работающий Geocoder API вместо Search API
            params = {
                'apikey': self.api_key,
                'geocode': query.strip(),
                'format': 'json',
                'results': 10,
                'lang': 'ru_RU'
            }
            
            # Добавляем ограничение по области поиска если есть координаты
            if lat and lon:
                # Создаем bbox для ограничения области поиска
                delta = radius / 111000  # Примерное преобразование метров в градусы
                bbox = f"{lon-delta},{lat-delta}~{lon+delta},{lat+delta}"
                params['bbox'] = bbox
            
            response = requests.get(self.geocoder_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Обработка результатов Geocoder API
            results = {
                'success': True,
                'source': 'yandex_maps',
                'query': query,
                'total_found': 0,
                'places': []
            }
            
            # Geocoder API возвращает структуру с GeoObjectCollection
            geo_objects = data.get('response', {}).get('GeoObjectCollection', {}).get('featureMember', [])
            results['total_found'] = len(geo_objects)
            
            for member in geo_objects:
                geo_object = member.get('GeoObject', {})
                metadata = geo_object.get('metaDataProperty', {}).get('GeocoderMetaData', {})
                
                # Извлекаем координаты
                point = geo_object.get('Point', {})
                pos = point.get('pos', '').split()
                coordinates = [float(pos[0]), float(pos[1])] if len(pos) == 2 else []
                
                # Преобразуем координаты в правильный формат
                coords_dict = None
                if len(coordinates) == 2:
                    coords_dict = {
                        'latitude': coordinates[1],   # lat - второй элемент
                        'longitude': coordinates[0]   # lon - первый элемент
                    }
                
                place = {
                    'name': geo_object.get('name', ''),
                    'description': geo_object.get('description', ''),
                    'coordinates': coords_dict,
                    'address': metadata.get('text', ''),
                    'category': [metadata.get('kind', '')],
                    'phone': [],
                    'url': '',
                    'hours': {},
                    'precision': metadata.get('precision', ''),
                    'type': metadata.get('kind', 'place')
                }
                results['places'].append(place)
            
            return results
            
        except requests.RequestException as e:
            logger.error(f"Yandex Maps search error: {e}")
            return {'success': False, 'error': str(e), 'source': 'yandex_maps'}
        except Exception as e:
            logger.error(f"Unexpected error in Yandex search: {e}")
            return {'success': False, 'error': str(e), 'source': 'yandex_maps'}
    
    def geocode(self, address: str) -> Dict[str, Any]:
        """
        Геокодирование - получение координат по адресу
        """
        try:
            params = {
                'apikey': self.api_key,
                'geocode': address,
                'format': 'json',
                'results': 1,
                'lang': 'ru_RU'
            }
            
            response = requests.get(self.geocoder_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Извлечение координат
            geo_objects = data.get('response', {}).get('GeoObjectCollection', {}).get('featureMember', [])
            if not geo_objects:
                return {'success': False, 'error': 'Address not found', 'source': 'yandex_geocoder'}
            
            geo_object = geo_objects[0]['GeoObject']
            coordinates = geo_object['Point']['pos'].split()
            
            # Формируем результат в ожидаемом формате
            formatted_address = geo_object.get('metaDataProperty', {}).get('GeocoderMetaData', {}).get('text', address)
            kind = geo_object.get('metaDataProperty', {}).get('GeocoderMetaData', {}).get('kind', 'place')
            
            result = {
                'success': True,
                'source': 'yandex_geocoder',
                'results': [{
                    'formatted_address': formatted_address,
                    'latitude': float(coordinates[1]),
                    'longitude': float(coordinates[0]),
                    'type': kind,
                    'confidence': 0.9,
                    'precision': geo_object.get('metaDataProperty', {}).get('GeocoderMetaData', {}).get('precision', ''),
                    'area': 'Не указано',
                    'permitted_use': 'Не указано',
                    'owner_type': 'Не указано',
                    'registration_date': 'Не указано',
                    'cadastral_value': 'Не указано'
                }]
            }
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"Yandex geocoding error: {e}")
            return {'success': False, 'error': str(e), 'source': 'yandex_geocoder'}
        except Exception as e:
            logger.error(f"Unexpected error in Yandex geocoding: {e}")
            return {'success': False, 'error': str(e), 'source': 'yandex_geocoder'}
    
    def search(self, query: str) -> Dict[str, Any]:
        """
        Универсальный поиск (включая кадастровые номера)
        """
        try:
            # Проверяем, является ли запрос кадастровым номером
            is_cadastral = ':' in query and len(query.split(':')) >= 3
            
            if is_cadastral:
                # Для кадастровых номеров используем специальный поиск
                params = {
                    'apikey': self.api_key,
                    'text': f"кадастровый номер {query}",
                    'lang': 'ru_RU',
                    'results': 5,
                    'format': 'json',
                    'type': 'biz'
                }
            else:
                params = {
                    'apikey': self.api_key,
                    'text': query,
                    'lang': 'ru_RU',
                    'results': 10,
                    'format': 'json'
                }
            
            response = requests.get(f"{self.base_url}/search/v1/", params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get('features', []):
                properties = item.get('properties', {})
                geometry = item.get('geometry', {})
                coords = geometry.get('coordinates', [])
                
                if coords:
                    result_data = {
                        'formatted_address': properties.get('description', query),
                        'latitude': coords[1],
                        'longitude': coords[0],
                        'type': properties.get('CompanyMetaData', {}).get('Categories', [{}])[0].get('name', 'place'),
                        'confidence': 0.8
                    }
                    
                    # Для кадастровых номеров добавляем дополнительные поля
                    if is_cadastral:
                        result_data.update({
                            'cadastral_number': query,
                            'area': properties.get('area', 'Не указано'),
                            'permitted_use': properties.get('permitted_use', 'Не указано'),
                            'owner_type': properties.get('owner_type', 'Не указано'),
                            'registration_date': properties.get('registration_date', 'Не указано'),
                            'cadastral_value': properties.get('cadastral_value', 'Не указано')
                        })
                    
                    results.append(result_data)
            
            return {
                'success': True,
                'source': 'yandex_search',
                'results': results
            }
            
        except requests.RequestException as e:
            logger.error(f"Yandex search error: {e}")
            return {'success': False, 'error': str(e), 'source': 'yandex_search'}
        except Exception as e:
            logger.error(f"Unexpected error in Yandex search: {e}")
            return {'success': False, 'error': str(e), 'source': 'yandex_search'}
    
    def reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Обратное геокодирование - получение адреса по координатам
        """
        try:
            params = {
                'apikey': self.api_key,
                'geocode': f"{lon},{lat}",
                'format': 'json',
                'results': 1,
                'lang': 'ru_RU'
            }
            
            response = requests.get(self.geocoder_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            geo_objects = data.get('response', {}).get('GeoObjectCollection', {}).get('featureMember', [])
            if not geo_objects:
                return {'success': False, 'error': 'Location not found', 'source': 'yandex_geocoder'}
            
            geo_object = geo_objects[0]['GeoObject']
            
            formatted_address = geo_object.get('metaDataProperty', {}).get('GeocoderMetaData', {}).get('text', '')
            kind = geo_object.get('metaDataProperty', {}).get('GeocoderMetaData', {}).get('kind', 'place')
            
            result = {
                'success': True,
                'source': 'yandex_geocoder',
                'results': [{
                    'formatted_address': formatted_address,
                    'latitude': lat,
                    'longitude': lon,
                    'type': kind,
                    'confidence': 0.9,
                    'precision': geo_object.get('metaDataProperty', {}).get('GeocoderMetaData', {}).get('precision', ''),
                    'area': 'Не указано',
                    'permitted_use': 'Не указано',
                    'owner_type': 'Не указано',
                    'registration_date': 'Не указано',
                    'cadastral_value': 'Не указано'
                }]
            }
            
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"Yandex reverse geocoding error: {e}")
            return {'success': False, 'error': str(e), 'source': 'yandex_geocoder'}
        except Exception as e:
            logger.error(f"Unexpected error in Yandex reverse geocoding: {e}")
            return {'success': False, 'error': str(e), 'source': 'yandex_geocoder'}
    
    def get_static_map(self, lat: float, lon: float, zoom: int = 15, 
                      width: int = 600, height: int = 400) -> Dict[str, Any]:
        """
        Получение статической карты
        """
        try:
            params = {
                'll': f"{lon},{lat}",
                'z': zoom,
                'size': f"{width},{height}",
                'l': 'map',
                'pt': f"{lon},{lat},pm2rdm",  # Красная метка
                'apikey': self.api_key
            }
            
            response = requests.get(self.static_url, params=params, timeout=15)
            response.raise_for_status()
            
            return {
                'success': True,
                'source': 'yandex_static_map',
                'image_data': response.content,
                'content_type': response.headers.get('content-type', 'image/png'),
                'coordinates': {'latitude': lat, 'longitude': lon},
                'zoom': zoom,
                'size': {'width': width, 'height': height}
            }
            
        except requests.RequestException as e:
            logger.error(f"Yandex static map error: {e}")
            return {'success': False, 'error': str(e), 'source': 'yandex_static_map'}
        except Exception as e:
            logger.error(f"Unexpected error getting Yandex static map: {e}")
            return {'success': False, 'error': str(e), 'source': 'yandex_static_map'}
    
    def get_panorama(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Поиск и получение панорамы для указанных координат
        """
        try:
            # Поиск ближайшей панорамы
            search_url = f"{self.panorama_url}?ll={lon},{lat}&apikey={self.api_key}"
            
            response = requests.get(search_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or 'panorama' not in data:
                return {'success': False, 'error': 'No panorama found', 'source': 'yandex_panorama'}
            
            panorama_id = data['panorama']['id']
            
            # Получение URL панорамы
            panorama_url = f"https://panoramas.api-maps.yandex.ru/get-panorama?panorama_id={panorama_id}&size=1024x512"
            
            return {
                'success': True,
                'source': 'yandex_panorama',
                'panorama_id': panorama_id,
                'panorama_url': panorama_url,
                'coordinates': {'latitude': lat, 'longitude': lon},
                'found_coordinates': {
                    'latitude': data['panorama']['lat'],
                    'longitude': data['panorama']['lon']
                }
            }
            
        except requests.RequestException as e:
            logger.error(f"Yandex panorama error: {e}")
            return {'success': False, 'error': str(e), 'source': 'yandex_panorama'}
        except Exception as e:
            logger.error(f"Unexpected error getting Yandex panorama: {e}")
            return {'success': False, 'error': str(e), 'source': 'yandex_panorama'}
    
    def find_similar_places(self, image_description: str, lat: float, lon: float, 
                           radius: int = 5000) -> Dict[str, Any]:
        """
        Поиск похожих мест на основе описания изображения
        """
        try:
            # Извлекаем ключевые слова из описания
            keywords = self._extract_keywords(image_description)
            
            results = []
            for keyword in keywords:
                search_result = self.search_places(keyword, lat, lon, radius)
                if search_result.get('success') and search_result.get('places'):
                    results.extend(search_result['places'])
            
            # Удаляем дубликаты и сортируем по релевантности
            unique_places = []
            seen_names = set()
            
            for place in results:
                name = place.get('name', '').lower()
                if name and name not in seen_names:
                    seen_names.add(name)
                    unique_places.append(place)
            
            return {
                'success': True,
                'source': 'yandex_maps',
                'description': image_description,
                'keywords': keywords,
                'total_found': len(unique_places),
                'places': unique_places[:10]  # Топ 10 результатов
            }
            
        except Exception as e:
            logger.error(f"Error finding similar places: {e}")
            return {'success': False, 'error': str(e), 'source': 'yandex_maps'}
    
    def _extract_keywords(self, description: str) -> List[str]:
        """
        Извлечение ключевых слов из описания изображения
        """
        # Простой алгоритм извлечения ключевых слов
        # В реальном проекте можно использовать NLP библиотеки
        
        building_keywords = ['здание', 'дом', 'офис', 'магазин', 'ресторан', 'кафе', 'банк', 'аптека']
        landmark_keywords = ['памятник', 'церковь', 'собор', 'музей', 'театр', 'парк', 'площадь']
        transport_keywords = ['метро', 'станция', 'остановка', 'вокзал', 'аэропорт']
        
        keywords = []
        description_lower = description.lower()
        
        # Поиск ключевых слов в описании
        for keyword_list in [building_keywords, landmark_keywords, transport_keywords]:
            for keyword in keyword_list:
                if keyword in description_lower:
                    keywords.append(keyword)
        
        # Если не найдено специфичных ключевых слов, используем общие
        if not keywords:
            keywords = ['достопримечательность', 'объект', 'место']
        
        return keywords[:5]  # Максимум 5 ключевых слов


# Пример использования
if __name__ == "__main__":
    service = YandexMapsService()
    
    # Тест поиска
    result = service.search_places("кафе", 55.7558, 37.6176)  # Москва, Красная площадь
    print("Search result:", json.dumps(result, indent=2, ensure_ascii=False))
    
    # Тест геокодирования
    geocode_result = service.geocode("Москва, Красная площадь")
    print("Geocode result:", json.dumps(geocode_result, indent=2, ensure_ascii=False))
