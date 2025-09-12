import os
import logging
import requests
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OSMOverpassService:
    """
    Сервис для работы с OpenStreetMap Overpass API
    Получение детальных данных об объектах, зданиях, дорогах и инфраструктуре
    """
    
    def __init__(self):
        self.base_url = "https://overpass-api.de/api/interpreter"
        self.backup_urls = [
            "https://overpass.kumi.systems/api/interpreter",
            "https://overpass.openstreetmap.ru/api/interpreter"
        ]
        
        # Кэш для запросов
        self.cache = {}
        self.cache_ttl = 3600  # 1 час
        
        # Ограничения запросов
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 секунда между запросами
        
        logger.info("🗺️ OSM Overpass Service initialized")

    def search_nearby_objects(self, latitude: float, longitude: float, 
                            radius: int = 500, object_types: List[str] = None) -> Dict[str, Any]:
        """
        Поиск объектов рядом с указанными координатами
        
        Args:
            latitude: Широта
            longitude: Долгота  
            radius: Радиус поиска в метрах
            object_types: Типы объектов для поиска
        """
        try:
            if object_types is None:
                object_types = ['building', 'amenity', 'shop', 'tourism', 'highway']
            
            # Создаем Overpass QL запрос
            query = self._build_nearby_query(latitude, longitude, radius, object_types)
            
            # Выполняем запрос
            result = self._execute_query(query)
            
            if result and 'elements' in result:
                objects = self._process_osm_elements(result['elements'])
                
                return {
                    'success': True,
                    'objects': objects,
                    'total_count': len(objects),
                    'coordinates': {'latitude': latitude, 'longitude': longitude},
                    'radius': radius,
                    'query_types': object_types
                }
            
            return {
                'success': False,
                'objects': [],
                'error': 'No objects found'
            }
            
        except Exception as e:
            logger.error(f"Error searching nearby objects: {e}")
            return {
                'success': False,
                'objects': [],
                'error': str(e)
            }

    def get_address_details(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Получение детальной информации об адресе по координатам
        """
        try:
            query = f"""
            [out:json][timeout:25];
            (
              way(around:50,{latitude},{longitude})["addr:street"];
              way(around:50,{latitude},{longitude})["addr:housenumber"];
              relation(around:100,{latitude},{longitude})["addr:city"];
              relation(around:100,{latitude},{longitude})["addr:postcode"];
            );
            out geom;
            """
            
            result = self._execute_query(query)
            
            if result and 'elements' in result:
                address_info = self._extract_address_info(result['elements'])
                
                return {
                    'success': True,
                    'address': address_info,
                    'coordinates': {'latitude': latitude, 'longitude': longitude}
                }
            
            return {
                'success': False,
                'address': {},
                'error': 'No address information found'
            }
            
        except Exception as e:
            logger.error(f"Error getting address details: {e}")
            return {
                'success': False,
                'address': {},
                'error': str(e)
            }

    def search_buildings(self, latitude: float, longitude: float, 
                        radius: int = 200) -> Dict[str, Any]:
        """
        Поиск зданий в указанном радиусе
        """
        try:
            query = f"""
            [out:json][timeout:25];
            (
              way["building"](around:{radius},{latitude},{longitude});
              relation["building"](around:{radius},{latitude},{longitude});
            );
            out geom;
            """
            
            result = self._execute_query(query)
            
            if result and 'elements' in result:
                buildings = []
                for element in result['elements']:
                    building_info = self._process_building_element(element)
                    if building_info:
                        buildings.append(building_info)
                
                return {
                    'success': True,
                    'buildings': buildings,
                    'total_count': len(buildings),
                    'search_radius': radius
                }
            
            return {
                'success': False,
                'buildings': [],
                'error': 'No buildings found'
            }
            
        except Exception as e:
            logger.error(f"Error searching buildings: {e}")
            return {
                'success': False,
                'buildings': [],
                'error': str(e)
            }

    def get_road_network(self, latitude: float, longitude: float, 
                        radius: int = 300) -> Dict[str, Any]:
        """
        Получение информации о дорожной сети
        """
        try:
            query = f"""
            [out:json][timeout:25];
            (
              way["highway"](around:{radius},{latitude},{longitude});
            );
            out geom;
            """
            
            result = self._execute_query(query)
            
            if result and 'elements' in result:
                roads = []
                for element in result['elements']:
                    road_info = self._process_road_element(element)
                    if road_info:
                        roads.append(road_info)
                
                return {
                    'success': True,
                    'roads': roads,
                    'total_count': len(roads),
                    'search_radius': radius
                }
            
            return {
                'success': False,
                'roads': [],
                'error': 'No roads found'
            }
            
        except Exception as e:
            logger.error(f"Error getting road network: {e}")
            return {
                'success': False,
                'roads': [],
                'error': str(e)
            }

    def search_by_name(self, name: str, latitude: float = None, 
                      longitude: float = None, radius: int = 5000) -> Dict[str, Any]:
        """
        Поиск объектов по названию
        """
        try:
            if latitude and longitude:
                # Поиск в определенном радиусе
                query = f"""
                [out:json][timeout:25];
                (
                  nwr["name"~"{name}",i](around:{radius},{latitude},{longitude});
                );
                out geom;
                """
            else:
                # Глобальный поиск
                query = f"""
                [out:json][timeout:25];
                (
                  nwr["name"~"{name}",i];
                );
                out geom;
                """
            
            result = self._execute_query(query)
            
            if result and 'elements' in result:
                objects = self._process_osm_elements(result['elements'])
                
                return {
                    'success': True,
                    'objects': objects,
                    'total_count': len(objects),
                    'search_name': name
                }
            
            return {
                'success': False,
                'objects': [],
                'error': f'No objects found with name: {name}'
            }
            
        except Exception as e:
            logger.error(f"Error searching by name: {e}")
            return {
                'success': False,
                'objects': [],
                'error': str(e)
            }

    def _build_nearby_query(self, lat: float, lon: float, radius: int, 
                           object_types: List[str]) -> str:
        """Построение Overpass QL запроса для поиска объектов рядом"""
        
        type_queries = []
        for obj_type in object_types:
            if obj_type == 'building':
                type_queries.append(f'way["building"](around:{radius},{lat},{lon});')
                type_queries.append(f'relation["building"](around:{radius},{lat},{lon});')
            elif obj_type == 'amenity':
                type_queries.append(f'nwr["amenity"](around:{radius},{lat},{lon});')
            elif obj_type == 'shop':
                type_queries.append(f'nwr["shop"](around:{radius},{lat},{lon});')
            elif obj_type == 'tourism':
                type_queries.append(f'nwr["tourism"](around:{radius},{lat},{lon});')
            elif obj_type == 'highway':
                type_queries.append(f'way["highway"](around:{radius},{lat},{lon});')
        
        query = f"""
        [out:json][timeout:25];
        (
          {chr(10).join(type_queries)}
        );
        out geom;
        """
        
        return query

    def _execute_query(self, query: str) -> Optional[Dict]:
        """Выполнение Overpass запроса с обработкой ошибок и кэшированием"""
        
        # Проверяем кэш
        cache_key = hash(query)
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.info("Using cached OSM data")
                return cached_data
        
        # Ограничение частоты запросов
        current_time = time.time()
        if current_time - self.last_request_time < self.min_request_interval:
            time.sleep(self.min_request_interval - (current_time - self.last_request_time))
        
        urls_to_try = [self.base_url] + self.backup_urls
        
        for url in urls_to_try:
            try:
                logger.info(f"Executing OSM Overpass query to {url}")
                
                response = requests.post(
                    url,
                    data=query,
                    headers={'Content-Type': 'text/plain; charset=utf-8'},
                    timeout=30
                )
                
                self.last_request_time = time.time()
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Кэшируем результат
                    self.cache[cache_key] = (result, time.time())
                    
                    logger.info(f"OSM query successful, found {len(result.get('elements', []))} elements")
                    return result
                else:
                    logger.warning(f"OSM API returned status {response.status_code}: {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout for OSM API: {url}")
                continue
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error for OSM API {url}: {e}")
                continue
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error for OSM API {url}: {e}")
                continue
        
        logger.error("All OSM Overpass APIs failed")
        return None

    def _process_osm_elements(self, elements: List[Dict]) -> List[Dict]:
        """Обработка элементов OSM в удобный формат"""
        processed = []
        
        for element in elements:
            try:
                obj_info = {
                    'id': element.get('id'),
                    'type': element.get('type'),
                    'tags': element.get('tags', {}),
                    'coordinates': None,
                    'name': element.get('tags', {}).get('name'),
                    'category': self._determine_category(element.get('tags', {}))
                }
                
                # Извлекаем координаты
                if element['type'] == 'node':
                    obj_info['coordinates'] = {
                        'latitude': element.get('lat'),
                        'longitude': element.get('lon')
                    }
                elif element['type'] in ['way', 'relation'] and 'geometry' in element:
                    # Берем центральную точку геометрии
                    geometry = element['geometry']
                    if geometry:
                        center_lat = sum(point['lat'] for point in geometry) / len(geometry)
                        center_lon = sum(point['lon'] for point in geometry) / len(geometry)
                        obj_info['coordinates'] = {
                            'latitude': center_lat,
                            'longitude': center_lon
                        }
                
                processed.append(obj_info)
                
            except Exception as e:
                logger.warning(f"Error processing OSM element: {e}")
                continue
        
        return processed

    def _process_building_element(self, element: Dict) -> Optional[Dict]:
        """Обработка элемента здания"""
        tags = element.get('tags', {})
        
        building_info = {
            'id': element.get('id'),
            'name': tags.get('name'),
            'building_type': tags.get('building'),
            'address': {
                'street': tags.get('addr:street'),
                'housenumber': tags.get('addr:housenumber'),
                'city': tags.get('addr:city'),
                'postcode': tags.get('addr:postcode')
            },
            'levels': tags.get('building:levels'),
            'height': tags.get('height'),
            'coordinates': None
        }
        
        # Извлекаем координаты центра здания
        if element['type'] == 'way' and 'geometry' in element:
            geometry = element['geometry']
            if geometry:
                center_lat = sum(point['lat'] for point in geometry) / len(geometry)
                center_lon = sum(point['lon'] for point in geometry) / len(geometry)
                building_info['coordinates'] = {
                    'latitude': center_lat,
                    'longitude': center_lon
                }
        
        return building_info

    def _process_road_element(self, element: Dict) -> Optional[Dict]:
        """Обработка элемента дороги"""
        tags = element.get('tags', {})
        
        road_info = {
            'id': element.get('id'),
            'name': tags.get('name'),
            'highway_type': tags.get('highway'),
            'surface': tags.get('surface'),
            'maxspeed': tags.get('maxspeed'),
            'lanes': tags.get('lanes'),
            'oneway': tags.get('oneway') == 'yes',
            'coordinates': []
        }
        
        # Извлекаем координаты дороги
        if 'geometry' in element:
            road_info['coordinates'] = [
                {'latitude': point['lat'], 'longitude': point['lon']}
                for point in element['geometry']
            ]
        
        return road_info

    def _extract_address_info(self, elements: List[Dict]) -> Dict[str, str]:
        """Извлечение информации об адресе из элементов OSM"""
        address = {}
        
        for element in elements:
            tags = element.get('tags', {})
            
            if 'addr:street' in tags:
                address['street'] = tags['addr:street']
            if 'addr:housenumber' in tags:
                address['housenumber'] = tags['addr:housenumber']
            if 'addr:city' in tags:
                address['city'] = tags['addr:city']
            if 'addr:postcode' in tags:
                address['postcode'] = tags['addr:postcode']
            if 'addr:country' in tags:
                address['country'] = tags['addr:country']
        
        return address

    def _determine_category(self, tags: Dict[str, str]) -> str:
        """Определение категории объекта по тегам"""
        if 'building' in tags:
            return 'building'
        elif 'amenity' in tags:
            return f"amenity_{tags['amenity']}"
        elif 'shop' in tags:
            return f"shop_{tags['shop']}"
        elif 'tourism' in tags:
            return f"tourism_{tags['tourism']}"
        elif 'highway' in tags:
            return f"highway_{tags['highway']}"
        else:
            return 'other'

    def get_service_status(self) -> Dict[str, Any]:
        """Получение статуса сервиса"""
        return {
            'service_name': 'OSM Overpass API',
            'base_url': self.base_url,
            'backup_urls': self.backup_urls,
            'cache_size': len(self.cache),
            'last_request': self.last_request_time,
            'available': True
        }
