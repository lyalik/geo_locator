"""
2GIS Panorama Service для получения панорам и анализа объектов
"""

import logging
import requests
from typing import Dict, List, Any, Optional
import os

logger = logging.getLogger(__name__)

class DGISPanoramaService:
    """
    Сервис для работы с панорамами 2GIS
    """
    
    def __init__(self):
        self.api_key = os.getenv('DGIS_API_KEY')
        self.base_url = "https://catalog.api.2gis.com"
        
        if not self.api_key:
            logger.warning("DGIS_API_KEY not found in environment variables")
        else:
            logger.info(f"🗺️ 2GIS Panorama service initialized")
    
    def get_panorama_nearby(self, lat: float, lon: float, radius: int = 200) -> Dict[str, Any]:
        """
        Поиск панорам 2GIS рядом с указанными координатами
        """
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'error': '2GIS API key not configured',
                    'source': '2gis_panorama'
                }
            
            # 2GIS API для поиска панорам
            url = f"{self.base_url}/3.0/items"
            params = {
                'key': self.api_key,
                'q': 'panorama',
                'point': f"{lon},{lat}",
                'radius': radius,
                'type': 'geo',
                'fields': 'items.point,items.name,items.address_name,items.photos',
                'limit': 10
            }
            
            logger.info(f"🔍 Searching 2GIS panoramas near {lat}, {lon} within {radius}m")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            panoramas = []
            
            if 'result' in data and 'items' in data['result']:
                for item in data['result']['items']:
                    # Проверяем наличие фото/панорам
                    if item.get('photos') and len(item['photos']) > 0:
                        point = item.get('point', {})
                        if point.get('lat') and point.get('lon'):
                            pano_info = {
                                'id': item.get('id', ''),
                                'latitude': float(point['lat']),
                                'longitude': float(point['lon']),
                                'name': item.get('name', ''),
                                'address': item.get('address_name', ''),
                                'photos': item.get('photos', []),
                                'image_url': item['photos'][0].get('url', '') if item['photos'] else '',
                                'distance': self._calculate_distance(lat, lon, float(point['lat']), float(point['lon'])),
                                'source': '2gis'
                            }
                            panoramas.append(pano_info)
            
            # Сортируем по расстоянию
            panoramas.sort(key=lambda x: x['distance'])
            
            logger.info(f"✅ Found {len(panoramas)} 2GIS panoramas")
            return {
                'success': True,
                'source': '2gis_panorama',
                'count': len(panoramas),
                'panoramas': panoramas[:5]  # Ограничиваем до 5
            }
            
        except requests.RequestException as e:
            logger.error(f"2GIS panorama search error: {e}")
            return {
                'success': False,
                'error': str(e),
                'source': '2gis_panorama'
            }
        except Exception as e:
            logger.error(f"Unexpected error in 2GIS panorama search: {e}")
            return {
                'success': False,
                'error': str(e),
                'source': '2gis_panorama'
            }
    
    def get_street_view_images(self, lat: float, lon: float, radius: int = 100) -> Dict[str, Any]:
        """
        Получение изображений уличного вида от 2GIS
        """
        try:
            # Альтернативный API для получения изображений улиц
            url = f"{self.base_url}/3.0/items/geocode"
            params = {
                'key': self.api_key,
                'lat': lat,
                'lon': lon,
                'fields': 'items.photos,items.street_view',
                'radius': radius
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            images = []
            
            if 'result' in data and 'items' in data['result']:
                for item in data['result']['items']:
                    if item.get('photos'):
                        for photo in item['photos']:
                            images.append({
                                'url': photo.get('url', ''),
                                'width': photo.get('width', 0),
                                'height': photo.get('height', 0),
                                'source': '2gis_street_view'
                            })
            
            return {
                'success': True,
                'source': '2gis_street_view',
                'images': images[:10]  # Ограничиваем до 10 изображений
            }
            
        except Exception as e:
            logger.error(f"Error getting 2GIS street view: {e}")
            return {
                'success': False,
                'error': str(e),
                'source': '2gis_street_view'
            }
    
    def search_places_with_photos(self, query: str, lat: float, lon: float, radius: int = 1000) -> Dict[str, Any]:
        """
        Поиск мест с фотографиями по запросу
        """
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'error': '2GIS API key not configured'
                }
            
            url = f"{self.base_url}/3.0/items"
            params = {
                'key': self.api_key,
                'q': query,
                'point': f"{lon},{lat}",
                'radius': radius,
                'fields': 'items.point,items.name,items.address_name,items.photos,items.rubrics',
                'limit': 20
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            places = []
            
            if 'result' in data and 'items' in data['result']:
                for item in data['result']['items']:
                    if item.get('photos') and len(item['photos']) > 0:
                        point = item.get('point', {})
                        if point.get('lat') and point.get('lon'):
                            place_info = {
                                'id': item.get('id', ''),
                                'name': item.get('name', ''),
                                'address': item.get('address_name', ''),
                                'latitude': float(point['lat']),
                                'longitude': float(point['lon']),
                                'photos': item.get('photos', []),
                                'categories': [rubric.get('name', '') for rubric in item.get('rubrics', [])],
                                'distance': self._calculate_distance(lat, lon, float(point['lat']), float(point['lon']))
                            }
                            places.append(place_info)
            
            places.sort(key=lambda x: x['distance'])
            
            return {
                'success': True,
                'source': '2gis_places',
                'places': places[:10]
            }
            
        except Exception as e:
            logger.error(f"Error searching 2GIS places: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Вычисление расстояния между двумя точками в метрах
        """
        import math
        
        R = 6371000  # Радиус Земли в метрах
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
