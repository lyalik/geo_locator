#!/usr/bin/env python3
"""
2GIS API Service для геолокации и поиска объектов
"""
import os
import logging
import requests
import json
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class DGISService:
    """
    Сервис для работы с 2GIS API
    - Поиск организаций и объектов
    - Получение детальной информации
    - Маршруты и навигация
    - Фотографии и панорамы
    """
    
    def __init__(self):
        self.api_key = os.getenv('DGIS_API_KEY')
        self.base_url = 'https://catalog.api.2gis.com'
        self.geo_url = 'https://catalog.api.2gis.ru/3.0'
        
        if not self.api_key:
            logger.warning("DGIS_API_KEY not found in environment variables")
    
    def search_places(self, query: str, lat: float = None, lon: float = None, 
                     radius: int = 1000, region_id: int = None) -> Dict[str, Any]:
        """
        Поиск мест и организаций через 2GIS Catalog API
        
        Args:
            query: Поисковый запрос
            lat, lon: Координаты центра поиска
            radius: Радиус поиска в метрах
            region_id: ID региона (например, 1 для Москвы)
        """
        try:
            url = f"{self.base_url}/3.0/items"
            params = {
                'key': self.api_key,
                'q': query,
                'page_size': 20,
                'fields': 'items.point,items.adm_div,items.address,items.contact_groups,items.rubrics,items.reviews,items.photos'
            }
            
            if lat and lon:
                params['point'] = f"{lon},{lat}"
                params['radius'] = radius
            
            # ОГРАНИЧЕНИЕ ДЛЯ ЛЦТ 2025: Принудительно ограничиваем поиск Москвой и МО
            if region_id:
                # Проверяем, что region_id соответствует Москве или МО
                if region_id not in [1, 2]:  # 1 - Москва, 2 - Московская область
                    logger.warning(f"Region ID {region_id} outside Moscow region, forcing Moscow")
                    region_id = 1
                params['region_id'] = region_id
            else:
                # ОБЯЗАТЕЛЬНОЕ ОГРАНИЧЕНИЕ: Принудительно устанавливаем Москву
                params['region_id'] = 1  # Москва
                logger.info("Forcing search region to Moscow for project requirements")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            results = {
                'success': True,
                'source': '2gis',
                'query': query,
                'total_found': data.get('meta', {}).get('total', 0),
                'places': []
            }
            
            for item in data.get('result', {}).get('items', []):
                place = {
                    'id': item.get('id'),
                    'name': item.get('name', ''),
                    'address': self._format_address(item.get('address_name', '')),
                    'coordinates': self._extract_coordinates(item.get('point', {})),
                    'rubrics': [rubric.get('name', '') for rubric in item.get('rubrics', [])],
                    'phone': self._extract_phone(item.get('contact_groups', [])),
                    'website': self._extract_website(item.get('contact_groups', [])),
                    'rating': item.get('reviews', {}).get('rating', 0),
                    'reviews_count': item.get('reviews', {}).get('count', 0),
                    'photos_count': len(item.get('photos', [])),
                    'working_hours': self._extract_working_hours(item.get('schedule', {})),
                    'region': item.get('adm_div', [{}])[0].get('name', '') if item.get('adm_div') else ''
                }
                results['places'].append(place)
            
            return results
            
        except requests.RequestException as e:
            logger.error(f"2GIS search error: {e}")
            return {'success': False, 'error': str(e), 'source': '2gis'}
        except Exception as e:
            logger.error(f"Unexpected error in 2GIS search: {e}")
            return {'success': False, 'error': str(e), 'source': '2gis'}
    
    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """
        Получение детальной информации о месте
        """
        try:
            url = f"{self.base_url}/3.0/items/byid"
            params = {
                'key': self.api_key,
                'id': place_id,
                'fields': 'items.point,items.adm_div,items.address,items.contact_groups,items.rubrics,items.reviews,items.photos,items.schedule,items.attributes'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            items = data.get('result', {}).get('items', [])
            
            if not items:
                return {'success': False, 'error': 'Place not found', 'source': '2gis'}
            
            item = items[0]
            
            result = {
                'success': True,
                'source': '2gis',
                'id': item.get('id'),
                'name': item.get('name', ''),
                'full_name': item.get('full_name', ''),
                'address': self._format_address(item.get('address_name', '')),
                'coordinates': self._extract_coordinates(item.get('point', {})),
                'rubrics': [rubric.get('name', '') for rubric in item.get('rubrics', [])],
                'contacts': self._extract_all_contacts(item.get('contact_groups', [])),
                'rating': item.get('reviews', {}).get('rating', 0),
                'reviews_count': item.get('reviews', {}).get('count', 0),
                'photos': self._extract_photos(item.get('photos', [])),
                'working_hours': self._extract_working_hours(item.get('schedule', {})),
                'attributes': self._extract_attributes(item.get('attributes', [])),
                'region': item.get('adm_div', [{}])[0].get('name', '') if item.get('adm_div') else ''
            }
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"2GIS place details error: {e}")
            return {'success': False, 'error': str(e), 'source': '2gis'}
        except Exception as e:
            logger.error(f"Unexpected error getting 2GIS place details: {e}")
            return {'success': False, 'error': str(e), 'source': '2gis'}
    
    def geocode(self, address: str, region_id: int = 1) -> Dict[str, Any]:
        """
        Геокодирование адреса
        """
        try:
            url = f"{self.base_url}/3.0/items"
            params = {
                'key': self.api_key,
                'q': address,
                'region_id': region_id,
                'fields': 'items.point,items.adm_div,items.address',
                'page_size': 10
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            items = data.get('result', {}).get('items', [])
            
            if not items:
                return {'success': False, 'error': 'Address not found', 'source': '2gis'}
            
            # Возвращаем результаты в формате, совместимом с фронтендом
            results = []
            seen_addresses = set()  # Для устранения дубликатов
            
            for item in items:
                coordinates = self._extract_coordinates(item.get('point', {}))
                if coordinates:
                    item_address = item.get('address_name', item.get('name', address))
                    # Создаем уникальный ключ для адреса
                    address_key = f"{item_address}_{coordinates['latitude']:.4f}_{coordinates['longitude']:.4f}"
                    
                    if address_key not in seen_addresses:
                        seen_addresses.add(address_key)
                        results.append({
                            'formatted_address': item_address,
                            'latitude': coordinates['latitude'],
                            'longitude': coordinates['longitude'],
                            'type': item.get('type', 'place'),
                            'confidence': 0.8,
                            'region': item.get('adm_div', [{}])[0].get('name', '') if item.get('adm_div') else ''
                        })
            
            return {
                'success': True,
                'source': '2gis',
                'results': results
            }
            
        except requests.RequestException as e:
            logger.error(f"2GIS geocoding error: {e}")
            return {'success': False, 'error': str(e), 'source': '2gis'}
        except Exception as e:
            logger.error(f"Unexpected error in 2GIS geocoding: {e}")
            return {'success': False, 'error': str(e), 'source': '2gis'}
    
    def reverse_geocode(self, lat: float, lon: float, radius: int = 100) -> Dict[str, Any]:
        """
        Обратное геокодирование - поиск адреса по координатам
        """
        try:
            # Используем API геокодирования 2ГИС
            url = f"{self.base_url}/4.0/geocoder"
            params = {
                'key': self.api_key,
                'point': f"{lon},{lat}",
                'radius': radius,
                'fields': 'items.point,items.adm_div,items.full_address_name,items.address_components'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            items = data.get('result', {}).get('items', [])
            
            if not items:
                # Fallback - поиск ближайших объектов
                return self._search_nearby_objects(lat, lon, radius)
            
            # Возвращаем результаты в формате, совместимом с фронтендом
            results = []
            for item in items:
                address_components = item.get('address_components', {})
                full_address = item.get('full_address_name', '')
                
                if not full_address and address_components:
                    # Собираем адрес из компонентов
                    parts = []
                    if address_components.get('street'):
                        parts.append(address_components['street'])
                    if address_components.get('number'):
                        parts.append(address_components['number'])
                    full_address = ', '.join(parts) if parts else 'Неизвестный адрес'
                
                results.append({
                    'formatted_address': full_address or 'Неизвестный адрес',
                    'latitude': lat,
                    'longitude': lon,
                    'type': item.get('type', 'address'),
                    'confidence': 0.8,
                    'region': item.get('adm_div', [{}])[0].get('name', '') if item.get('adm_div') else '',
                    'area': 'Не указано',
                    'permitted_use': 'Не указано',
                    'owner_type': 'Не указано',
                    'registration_date': 'Не указано',
                    'cadastral_value': 'Не указано'
                })
            
            return {
                'success': True,
                'source': '2gis',
                'results': results
            }
            
        except requests.RequestException as e:
            logger.error(f"2GIS reverse geocoding error: {e}")
            return {'success': False, 'error': str(e), 'source': '2gis'}
        except Exception as e:
            logger.error(f"Unexpected error in 2GIS reverse geocoding: {e}")
            return {'success': False, 'error': str(e), 'source': '2gis'}
    
    def _search_nearby_objects(self, lat: float, lon: float, radius: int = 100) -> Dict[str, Any]:
        """
        Поиск ближайших объектов как fallback для reverse geocoding
        """
        try:
            url = f"{self.base_url}/3.0/items"
            params = {
                'key': self.api_key,
                'point': f"{lon},{lat}",
                'radius': radius,
                'fields': 'items.point,items.adm_div,items.address',
                'page_size': 3
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            items = data.get('result', {}).get('items', [])
            
            if not items:
                return {'success': False, 'error': 'No nearby objects found', 'source': '2gis'}
            
            results = []
            for item in items:
                results.append({
                    'formatted_address': item.get('address_name', item.get('name', f'Объект рядом с {lat:.4f}, {lon:.4f}')),
                    'latitude': lat,
                    'longitude': lon,
                    'type': item.get('type', 'nearby_object'),
                    'confidence': 0.6,
                    'region': item.get('adm_div', [{}])[0].get('name', '') if item.get('adm_div') else '',
                    'area': 'Не указано',
                    'permitted_use': 'Не указано',
                    'owner_type': 'Не указано',
                    'registration_date': 'Не указано',
                    'cadastral_value': 'Не указано'
                })
            
            return {
                'success': True,
                'source': '2gis',
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Nearby objects search failed: {e}")
            return {'success': False, 'error': str(e), 'source': '2gis'}
    
    def search(self, query: str, region_id: int = 1) -> Dict[str, Any]:
        """
        Универсальный поиск (включая кадастровые номера)
        """
        try:
            # Проверяем, является ли запрос кадастровым номером
            is_cadastral = ':' in query and len(query.split(':')) >= 3
            
            url = f"{self.base_url}/3.0/items"
            params = {
                'key': self.api_key,
                'q': query,
                'region_id': region_id,
                'fields': 'items.point,items.adm_div,items.address,items.attributes',
                'page_size': 10
            }
            
            # Для кадастровых номеров добавляем специальные параметры
            if is_cadastral:
                params['type'] = 'building'
                params['q'] = f"кадастровый номер {query}"
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            items = data.get('result', {}).get('items', [])
            
            if not items and is_cadastral:
                # Если кадастровый номер не найден, создаем заглушку с базовой информацией
                return {
                    'success': True,
                    'source': '2gis',
                    'results': [{
                        'formatted_address': f'Объект с кадастровым номером {query}',
                        'latitude': 55.7558,  # Координаты Красной площади по умолчанию
                        'longitude': 37.6176,
                        'type': 'building',
                        'confidence': 0.5,
                        'cadastral_number': query,
                        'area': 'Требует уточнения',
                        'permitted_use': 'Требует уточнения',
                        'owner_type': 'Требует уточнения',
                        'registration_date': 'Требует уточнения',
                        'cadastral_value': 'Требует уточнения'
                    }]
                }
            
            if not items:
                return {'success': False, 'error': 'No results found', 'source': '2gis'}
            
            results = []
            for item in items:
                coordinates = self._extract_coordinates(item.get('point', {}))
                if coordinates:
                    result_data = {
                        'formatted_address': item.get('address_name', item.get('name', query)),
                        'latitude': coordinates['latitude'],
                        'longitude': coordinates['longitude'],
                        'type': item.get('type', 'place'),
                        'confidence': 0.7,
                        'region': item.get('adm_div', [{}])[0].get('name', '') if item.get('adm_div') else ''
                    }
                    
                    # Для кадастровых номеров добавляем дополнительные поля
                    if is_cadastral:
                        attributes = item.get('attributes', [])
                        result_data.update({
                            'cadastral_number': query,
                            'area': self._extract_attribute(attributes, 'area') or 'Не указано',
                            'permitted_use': self._extract_attribute(attributes, 'use') or 'Не указано',
                            'owner_type': self._extract_attribute(attributes, 'owner') or 'Не указано',
                            'registration_date': self._extract_attribute(attributes, 'date') or 'Не указано',
                            'cadastral_value': self._extract_attribute(attributes, 'value') or 'Не указано'
                        })
                    
                    results.append(result_data)
            
            return {
                'success': True,
                'source': '2gis',
                'results': results
            }
            
        except requests.RequestException as e:
            logger.error(f"2GIS search error: {e}")
            return {'success': False, 'error': str(e), 'source': '2gis'}
        except Exception as e:
            logger.error(f"Unexpected error in 2GIS search: {e}")
            return {'success': False, 'error': str(e), 'source': '2gis'}
    
    def find_nearby_places(self, lat: float, lon: float, category: str = None, 
                          radius: int = 1000) -> Dict[str, Any]:
        """
        Поиск ближайших мест определенной категории
        """
        try:
            url = f"{self.base_url}/3.0/items"
            params = {
                'key': self.api_key,
                'point': f"{lon},{lat}",
                'radius': radius,
                'fields': 'items.point,items.adm_div,items.address,items.contact_groups,items.rubrics,items.reviews',
                'page_size': 20
            }
            
            if category:
                params['rubric_id'] = self._get_rubric_id(category)
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            results = {
                'success': True,
                'source': '2gis',
                'center_coordinates': {'latitude': lat, 'longitude': lon},
                'category': category,
                'radius': radius,
                'total_found': data.get('meta', {}).get('total', 0),
                'places': []
            }
            
            for item in data.get('result', {}).get('items', []):
                place_coords = self._extract_coordinates(item.get('point', {}))
                distance = self._calculate_distance(lat, lon, 
                                                  place_coords['latitude'], 
                                                  place_coords['longitude'])
                
                place = {
                    'id': item.get('id'),
                    'name': item.get('name', ''),
                    'address': self._format_address(item.get('address_name', '')),
                    'coordinates': place_coords,
                    'distance': round(distance, 0),
                    'rubrics': [rubric.get('name', '') for rubric in item.get('rubrics', [])],
                    'rating': item.get('reviews', {}).get('rating', 0),
                    'reviews_count': item.get('reviews', {}).get('count', 0)
                }
                results['places'].append(place)
            
            # Сортируем по расстоянию
            results['places'].sort(key=lambda x: x['distance'])
            
            return results
            
        except requests.RequestException as e:
            logger.error(f"2GIS nearby places error: {e}")
            return {'success': False, 'error': str(e), 'source': '2gis'}
        except Exception as e:
            logger.error(f"Unexpected error finding nearby places: {e}")
            return {'success': False, 'error': str(e), 'source': '2gis'}
    
    def _extract_coordinates(self, point: Dict) -> Dict[str, float]:
        """Извлечение координат из объекта point"""
        if not point:
            return {'latitude': 0.0, 'longitude': 0.0}
        
        return {
            'latitude': point.get('lat', 0.0),
            'longitude': point.get('lon', 0.0)
        }
    
    def _format_address(self, address: str) -> str:
        """Форматирование адреса"""
        return address.strip() if address else ''
    
    def _extract_phone(self, contact_groups: List) -> str:
        """Извлечение телефона из контактных групп"""
        for group in contact_groups:
            for contact in group.get('contacts', []):
                if contact.get('type') == 'phone':
                    return contact.get('value', '')
        return ''
    
    def _extract_website(self, contact_groups: List) -> str:
        """Извлечение веб-сайта из контактных групп"""
        for group in contact_groups:
            for contact in group.get('contacts', []):
                if contact.get('type') == 'website':
                    return contact.get('value', '')
        return ''
    
    def _extract_all_contacts(self, contact_groups: List) -> Dict[str, List]:
        """Извлечение всех контактов"""
        contacts = {'phones': [], 'websites': [], 'emails': []}
        
        for group in contact_groups:
            for contact in group.get('contacts', []):
                contact_type = contact.get('type', '')
                value = contact.get('value', '')
                
                if contact_type == 'phone' and value:
                    contacts['phones'].append(value)
                elif contact_type == 'website' and value:
                    contacts['websites'].append(value)
                elif contact_type == 'email' and value:
                    contacts['emails'].append(value)
        
        return contacts
    
    def _extract_photos(self, photos: List) -> List[Dict]:
        """Извлечение фотографий"""
        result = []
        for photo in photos:
            result.append({
                'url': photo.get('url', ''),
                'preview_url': photo.get('preview_url', ''),
                'width': photo.get('width', 0),
                'height': photo.get('height', 0)
            })
        return result
    
    def _extract_working_hours(self, schedule: Dict) -> Dict:
        """Извлечение рабочих часов"""
        if not schedule:
            return {}
        
        return {
            'is_24x7': schedule.get('is_24x7', False),
            'working_hours': schedule.get('working_hours', []),
            'tz_offset': schedule.get('tz_offset', 0)
        }
    
    def _extract_attributes(self, attributes: List) -> Dict:
        """Извлечение атрибутов места"""
        result = {}
        for attr in attributes:
            result[attr.get('name', '')] = attr.get('value', '')
        return result
    
    def _get_rubric_id(self, category: str) -> str:
        """Получение ID рубрики по категории"""
        # Маппинг популярных категорий на ID рубрик 2GIS
        category_mapping = {
            'кафе': '30',
            'ресторан': '31',
            'магазин': '1',
            'аптека': '184',
            'банк': '361',
            'заправка': '127',
            'больница': '185',
            'школа': '141',
            'парк': '372'
        }
        
        return category_mapping.get(category.lower(), '')
    
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
    
    def _extract_attribute(self, attributes: List, attr_type: str) -> str:
        """Извлечение конкретного атрибута из списка атрибутов"""
        for attr in attributes:
            name = attr.get('name', '').lower()
            if attr_type in name:
                return attr.get('value', '')
        return ''
    
    def get_satellite_layer(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Получение спутникового слоя 2GIS для указанных координат
        
        Args:
            lat: Широта
            lon: Долгота
        
        Returns:
            Dict с информацией о спутниковом снимке
        """
        try:
            # 2GIS предоставляет спутниковые слои через Static API
            # Формируем URL для получения спутникового изображения
            zoom = 16
            size = "512,512"
            
            # URL для спутникового слоя 2GIS
            satellite_url = f"https://tile2.maps.2gis.com/1.0?request=GetMap&layers=sat&srs=EPSG:3857&format=image/png&bbox={lon-0.01},{lat-0.01},{lon+0.01},{lat+0.01}&width=512&height=512"
            
            # Альтернативный URL через статические карты
            static_url = f"https://static.maps.2gis.com/1.0?center={lon},{lat}&zoom={zoom}&size={size}&format=png&markers={lon},{lat}"
            
            return {
                'success': True,
                'image_url': static_url,
                'satellite_url': satellite_url,
                'source': 'dgis',
                'coordinates': {
                    'latitude': lat,
                    'longitude': lon
                },
                'zoom_level': zoom,
                'image_size': size,
                'format': 'png'
            }
            
        except Exception as e:
            logger.error(f"Error getting 2GIS satellite layer: {e}")
            return {
                'success': False,
                'error': str(e),
                'source': 'dgis'
            }


# Пример использования
if __name__ == "__main__":
    service = DGISService()
    
    # Тест поиска
    result = service.search_places("пиццерия", 55.7558, 37.6176)  # Москва
    print("Search result:", json.dumps(result, indent=2, ensure_ascii=False))
    
    # Тест поиска ближайших мест
    nearby = service.find_nearby_places(55.7558, 37.6176, "кафе", 500)
    print("Nearby places:", json.dumps(nearby, indent=2, ensure_ascii=False))
