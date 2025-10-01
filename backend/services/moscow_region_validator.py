#!/usr/bin/env python3
"""
Валидатор для ограничения поиска Москвой и Московской областью
Требование ЛЦТ 2025: все результаты должны быть в пределах Москвы и МО
"""
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class MoscowRegionValidator:
    """
    Валидатор для ограничения результатов поиска Москвой и Московской областью
    """
    
    # Границы Москвы и Московской области
    MOSCOW_REGION_BOUNDS = {
        'min_lat': 54.0,
        'max_lat': 57.0,
        'min_lon': 35.0,
        'max_lon': 40.5
    }
    
    # Центр Москвы (Красная площадь)
    MOSCOW_CENTER = {
        'lat': 55.7558,
        'lon': 37.6176
    }
    
    @classmethod
    def is_in_moscow_region(cls, lat: float, lon: float) -> bool:
        """
        Проверяет, находятся ли координаты в пределах Москвы и МО
        
        Args:
            lat: Широта
            lon: Долгота
            
        Returns:
            bool: True если координаты в пределах Москвы и МО
        """
        return (cls.MOSCOW_REGION_BOUNDS['min_lat'] <= lat <= cls.MOSCOW_REGION_BOUNDS['max_lat'] and
                cls.MOSCOW_REGION_BOUNDS['min_lon'] <= lon <= cls.MOSCOW_REGION_BOUNDS['max_lon'])
    
    @classmethod
    def filter_coordinates(cls, coordinates: Dict[str, float]) -> Optional[Dict[str, float]]:
        """
        Фильтрует координаты, оставляя только те, что в Москве и МО
        
        Args:
            coordinates: Словарь с координатами {'latitude': float, 'longitude': float}
            
        Returns:
            Dict или None если координаты вне региона
        """
        if not coordinates or 'latitude' not in coordinates or 'longitude' not in coordinates:
            return None
            
        lat = coordinates['latitude']
        lon = coordinates['longitude']
        
        if cls.is_in_moscow_region(lat, lon):
            return coordinates
        else:
            logger.warning(f"Coordinates {lat}, {lon} outside Moscow region, filtering out")
            return None
    
    @classmethod
    def filter_results_list(cls, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Фильтрует список результатов, оставляя только те, что в Москве и МО
        
        Args:
            results: Список результатов с координатами
            
        Returns:
            Отфильтрованный список результатов
        """
        filtered_results = []
        
        for result in results:
            # Проверяем разные возможные ключи для координат
            lat, lon = None, None
            
            if 'latitude' in result and 'longitude' in result:
                lat, lon = result['latitude'], result['longitude']
            elif 'lat' in result and 'lon' in result:
                lat, lon = result['lat'], result['lon']
            elif 'coordinates' in result:
                coords = result['coordinates']
                if isinstance(coords, dict):
                    lat = coords.get('latitude') or coords.get('lat')
                    lon = coords.get('longitude') or coords.get('lon')
                elif isinstance(coords, list) and len(coords) >= 2:
                    lat, lon = coords[1], coords[0]  # GeoJSON format [lon, lat]
            elif 'point' in result and 'lat' in result['point'] and 'lon' in result['point']:
                lat, lon = result['point']['lat'], result['point']['lon']
            
            if lat is not None and lon is not None:
                if cls.is_in_moscow_region(lat, lon):
                    filtered_results.append(result)
                else:
                    logger.debug(f"Filtered out result with coordinates {lat}, {lon} (outside Moscow region)")
            else:
                # Если координат нет, оставляем результат (может быть полезен для других целей)
                filtered_results.append(result)
        
        logger.info(f"Filtered {len(results)} results to {len(filtered_results)} within Moscow region")
        return filtered_results
    
    @classmethod
    def get_moscow_bbox(cls) -> str:
        """
        Возвращает bbox для Москвы и МО в формате для API запросов
        
        Returns:
            str: Bbox в формате "min_lon,min_lat~max_lon,max_lat"
        """
        return f"{cls.MOSCOW_REGION_BOUNDS['min_lon']},{cls.MOSCOW_REGION_BOUNDS['min_lat']}~{cls.MOSCOW_REGION_BOUNDS['max_lon']},{cls.MOSCOW_REGION_BOUNDS['max_lat']}"
    
    @classmethod
    def get_moscow_center(cls) -> Tuple[float, float]:
        """
        Возвращает координаты центра Москвы
        
        Returns:
            Tuple[float, float]: (latitude, longitude)
        """
        return cls.MOSCOW_CENTER['lat'], cls.MOSCOW_CENTER['lon']
    
    @classmethod
    def enhance_query_for_moscow(cls, query: str) -> str:
        """
        Улучшает поисковый запрос, добавляя указание на Москву
        
        Args:
            query: Исходный поисковый запрос
            
        Returns:
            str: Улучшенный запрос с указанием на Москву
        """
        moscow_keywords = ['москва', 'московская область', 'мо', 'moscow']
        
        # Проверяем, есть ли уже указание на Москву в запросе
        if any(keyword in query.lower() for keyword in moscow_keywords):
            return query
        
        # Добавляем "Москва" к запросу
        enhanced_query = f"{query}, Москва"
        logger.info(f"Enhanced query for Moscow region: '{query}' -> '{enhanced_query}'")
        return enhanced_query
    
    @classmethod
    def validate_and_log_coordinates(cls, coordinates: Dict[str, float], source: str = "unknown") -> bool:
        """
        Валидирует координаты и логирует результат
        
        Args:
            coordinates: Координаты для проверки
            source: Источник координат для логирования
            
        Returns:
            bool: True если координаты валидны
        """
        if not coordinates:
            return False
            
        lat = coordinates.get('latitude') or coordinates.get('lat')
        lon = coordinates.get('longitude') or coordinates.get('lon')
        
        if lat is None or lon is None:
            logger.warning(f"Invalid coordinates from {source}: missing lat/lon")
            return False
        
        is_valid = cls.is_in_moscow_region(lat, lon)
        
        if is_valid:
            logger.info(f"✅ Valid Moscow region coordinates from {source}: {lat}, {lon}")
        else:
            logger.warning(f"❌ Coordinates from {source} outside Moscow region: {lat}, {lon}")
        
        return is_valid
