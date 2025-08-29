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
        self.base_url = 'https://api-maps.yandex.ru'
        self.geocoder_url = 'https://geocode-maps.yandex.ru/1.x/'
        self.static_url = 'https://static-maps.yandex.ru/1.x/'
        self.panorama_url = 'https://api-maps.yandex.ru/services/panoramas/1.x/'
        
        if not self.api_key:
            logger.warning("YANDEX_API_KEY not found in environment variables")
    
    def search_places(self, query: str, lat: float = None, lon: float = None, 
                     radius: int = 1000) -> Dict[str, Any]:
        """
        Поиск мест и объектов через Yandex Search API
        
        Args:
            query: Поисковый запрос
            lat, lon: Координаты центра поиска
            radius: Радиус поиска в метрах
        """
        try:
            url = f"{self.base_url}/search/v1/"
            params = {
                'apikey': self.api_key,
                'text': query,
                'lang': 'ru_RU',
                'results': 10,
                'format': 'json'
            }
            
            if lat and lon:
                params['ll'] = f"{lon},{lat}"
                params['spn'] = f"{radius/111000},{radius/111000}"  # Примерное преобразование метров в градусы
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Обработка результатов поиска
            results = {
                'success': True,
                'source': 'yandex_maps',
                'query': query,
                'total_found': len(data.get('features', [])),
                'places': []
            }
            
            for feature in data.get('features', []):
                place = {
                    'name': feature.get('properties', {}).get('name', ''),
                    'description': feature.get('properties', {}).get('description', ''),
                    'coordinates': feature.get('geometry', {}).get('coordinates', []),
                    'address': feature.get('properties', {}).get('CompanyMetaData', {}).get('address', ''),
                    'category': feature.get('properties', {}).get('CompanyMetaData', {}).get('Categories', []),
                    'phone': feature.get('properties', {}).get('CompanyMetaData', {}).get('Phones', []),
                    'url': feature.get('properties', {}).get('CompanyMetaData', {}).get('url', ''),
                    'hours': feature.get('properties', {}).get('CompanyMetaData', {}).get('Hours', {})
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
            
            result = {
                'success': True,
                'source': 'yandex_geocoder',
                'address': address,
                'coordinates': {
                    'latitude': float(coordinates[1]),
                    'longitude': float(coordinates[0])
                },
                'formatted_address': geo_object.get('metaDataProperty', {}).get('GeocoderMetaData', {}).get('text', ''),
                'precision': geo_object.get('metaDataProperty', {}).get('GeocoderMetaData', {}).get('precision', ''),
                'kind': geo_object.get('metaDataProperty', {}).get('GeocoderMetaData', {}).get('kind', '')
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
            # Для кадастровых номеров используем поиск организаций
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
            for feature in data.get('features', []):
                coords = feature.get('geometry', {}).get('coordinates', [])
                if len(coords) >= 2:
                    results.append({
                        'formatted_address': feature.get('properties', {}).get('name', '') + ', ' + 
                                           feature.get('properties', {}).get('description', ''),
                        'latitude': coords[1],
                        'longitude': coords[0],
                        'type': 'organization',
                        'confidence': 0.7
                    })
            
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
            
            result = {
                'success': True,
                'source': 'yandex_geocoder',
                'coordinates': {'latitude': lat, 'longitude': lon},
                'formatted_address': geo_object.get('metaDataProperty', {}).get('GeocoderMetaData', {}).get('text', ''),
                'components': {},
                'precision': geo_object.get('metaDataProperty', {}).get('GeocoderMetaData', {}).get('precision', ''),
                'kind': geo_object.get('metaDataProperty', {}).get('GeocoderMetaData', {}).get('kind', '')
            }
            
            # Парсинг компонентов адреса
            address_details = geo_object.get('metaDataProperty', {}).get('GeocoderMetaData', {}).get('AddressDetails', {})
            if address_details:
                country = address_details.get('Country', {})
                result['components']['country'] = country.get('CountryName', '')
                
                admin_area = country.get('AdministrativeArea', {})
                result['components']['region'] = admin_area.get('AdministrativeAreaName', '')
                
                locality = admin_area.get('Locality', {}) or admin_area.get('SubAdministrativeArea', {}).get('Locality', {})
                result['components']['city'] = locality.get('LocalityName', '')
                
                thoroughfare = locality.get('Thoroughfare', {})
                result['components']['street'] = thoroughfare.get('ThoroughfareName', '')
                result['components']['house'] = thoroughfare.get('Premise', {}).get('PremiseNumber', '')
            
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
