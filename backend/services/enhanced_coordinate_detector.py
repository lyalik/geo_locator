import os
import logging
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
from PIL import Image
import cv2
import exifread
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import requests
import json
from datetime import datetime

# Import AI services
from .mistral_ocr_service import MistralOCRService
from .panorama_analyzer_service import PanoramaAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedCoordinateDetector:
    """
    Улучшенный детектор координат с более точной логикой определения местоположения
    и устранением проблемы с дефолтными координатами Пекина
    """
    
    def __init__(self):
        self.geocoder = Nominatim(user_agent="geo_locator_enhanced")
        
        # Initialize AI services
        self.mistral_ocr = MistralOCRService()
        self.panorama_analyzer = PanoramaAnalyzer()
        
        # Приоритетные регионы для России
        self.russia_bounds = {
            'min_lat': 41.0,  # Южная граница России
            'max_lat': 82.0,  # Северная граница России  
            'min_lon': 19.0,  # Западная граница России
            'max_lon': 180.0  # Восточная граница России
        }
        
        # Дефолтные координаты для разных регионов (вместо Пекина)
        self.regional_defaults = {
            'russia': {'lat': 55.7558, 'lon': 37.6176, 'name': 'Москва, Россия'},
            'europe': {'lat': 50.8503, 'lon': 4.3517, 'name': 'Брюссель, Европа'},
            'asia': {'lat': 35.6762, 'lon': 139.6503, 'name': 'Токио, Азия'},
            'america': {'lat': 40.7128, 'lon': -74.0060, 'name': 'Нью-Йорк, США'},
            'global': {'lat': 0.0, 'lon': 0.0, 'name': 'Экватор'}
        }
        
        # Весовые коэффициенты для разных источников координат
        self.source_weights = {
            'gps_exif': 1.0,           # GPS из EXIF - максимальный приоритет
            'panorama_analysis': 0.95,  # Анализ панорам - очень высокий приоритет
            'location_hint': 0.9,       # Подсказка пользователя
            'yandex_maps': 0.85,        # Яндекс Карты
            'mistral_ocr': 0.8,         # Mistral AI OCR
            'dgis': 0.8,               # 2GIS
            'nominatim': 0.7,          # OpenStreetMap Nominatim
            'image_similarity': 0.6,    # Сходство изображений
            'object_detection': 0.5,    # Детекция объектов
            'fallback': 0.1            # Резервный вариант
        }

    def detect_coordinates_enhanced(self, image_path: str, location_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Улучшенное определение координат с множественными источниками и валидацией
        """
        logger.info(f"🔍 Enhanced coordinate detection for: {image_path}")
        logger.info(f"📍 Location hint: {location_hint}")
        
        coordinate_candidates = []
        
        try:
            # 1. Извлечение GPS из EXIF (высший приоритет)
            gps_coords = self._extract_gps_from_exif(image_path)
            if gps_coords:
                coordinate_candidates.append({
                    'coordinates': gps_coords,
                    'source': 'gps_exif',
                    'confidence': 0.95,
                    'weight': self.source_weights['gps_exif']
                })
                logger.info(f"✅ GPS from EXIF: {gps_coords}")
            
            # 2. Обработка подсказки местоположения
            if location_hint:
                hint_coords = self._geocode_location_hint(location_hint)
                if hint_coords:
                    coordinate_candidates.append({
                        'coordinates': hint_coords,
                        'source': 'location_hint',
                        'confidence': 0.8,
                        'weight': self.source_weights['location_hint']
                    })
                    logger.info(f"✅ Location hint geocoded: {hint_coords}")
            
            # 3. Анализ изображения для извлечения текстовых подсказок с Mistral AI
            mistral_coords = self._extract_coordinates_with_mistral(image_path)
            if mistral_coords:
                coordinate_candidates.append({
                    'coordinates': mistral_coords,
                    'source': 'mistral_ocr',
                    'confidence': 0.75,
                    'weight': self.source_weights['mistral_ocr']
                })
                logger.info(f"✅ Coordinates from Mistral OCR: {mistral_coords}")
            
            # 4. Анализ панорам (если есть примерные координаты)
            if coordinate_candidates:
                # Берем лучший кандидат для поиска панорам
                temp_best = max(coordinate_candidates, key=lambda x: x['confidence'] * x['weight'])
                panorama_coords = self._analyze_with_panoramas(image_path, temp_best['coordinates'])
                if panorama_coords:
                    coordinate_candidates.append({
                        'coordinates': panorama_coords,
                        'source': 'panorama_analysis',
                        'confidence': 0.85,
                        'weight': self.source_weights['panorama_analysis']
                    })
                    logger.info(f"✅ Coordinates from panorama analysis: {panorama_coords}")
            
            # 5. Определение региона по объектам на изображении
            region_coords = self._detect_region_from_objects(image_path, location_hint)
            if region_coords:
                coordinate_candidates.append({
                    'coordinates': region_coords,
                    'source': 'object_detection',
                    'confidence': 0.6,
                    'weight': self.source_weights['object_detection']
                })
                logger.info(f"✅ Region from objects: {region_coords}")
            
            # 6. Выбор лучшего кандидата
            if coordinate_candidates:
                best_candidate = self._select_best_candidate(coordinate_candidates, location_hint)
                
                # Валидация координат
                if self._validate_coordinates(best_candidate['coordinates'], location_hint):
                    result = {
                        'success': True,
                        'coordinates': best_candidate['coordinates'],
                        'source': best_candidate['source'],
                        'confidence': best_candidate['confidence'],
                        'all_candidates': coordinate_candidates,
                        'validation_passed': True
                    }
                    logger.info(f"🎯 Final coordinates: {best_candidate['coordinates']} from {best_candidate['source']}")
                    return result
            
            # 6. Если координаты не найдены - НЕ возвращаем дефолтные координаты
            logger.warning("⚠️ No valid coordinates found - returning None instead of default")
            return {
                'success': False,
                'message': 'No valid coordinates found from any source',
                'candidates_tried': len(coordinate_candidates) if coordinate_candidates else 0,
                'validation_failed': True
            }
            
        except Exception as e:
            logger.error(f"❌ Error in enhanced coordinate detection: {e}")
            return {
                'success': False,
                'coordinates': None,
                'source': 'error',
                'confidence': 0.0,
                'error': str(e)
            }

    def _extract_gps_from_exif(self, image_path: str) -> Optional[Dict[str, float]]:
        """Извлечение GPS координат из EXIF данных"""
        try:
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f)
                
                gps_latitude = tags.get('GPS GPSLatitude')
                gps_latitude_ref = tags.get('GPS GPSLatitudeRef')
                gps_longitude = tags.get('GPS GPSLongitude')
                gps_longitude_ref = tags.get('GPS GPSLongitudeRef')
                
                if all([gps_latitude, gps_latitude_ref, gps_longitude, gps_longitude_ref]):
                    lat = self._convert_to_degrees(gps_latitude)
                    lon = self._convert_to_degrees(gps_longitude)
                    
                    if str(gps_latitude_ref) == 'S':
                        lat = -lat
                    if str(gps_longitude_ref) == 'W':
                        lon = -lon
                    
                    return {'latitude': lat, 'longitude': lon}
        except Exception as e:
            logger.error(f"Error extracting GPS from EXIF: {e}")
        return None

    def _convert_to_degrees(self, value):
        """Конвертация GPS координат в десятичные градусы"""
        d = float(value.values[0].num) / float(value.values[0].den)
        m = float(value.values[1].num) / float(value.values[1].den)
        s = float(value.values[2].num) / float(value.values[2].den)
        return d + (m / 60.0) + (s / 3600.0)

    def _geocode_location_hint(self, location_hint: str) -> Optional[Dict[str, float]]:
        """Геокодирование подсказки местоположения"""
        try:
            # Добавляем "Россия" если не указана страна
            if location_hint and 'россия' not in location_hint.lower() and 'russia' not in location_hint.lower():
                enhanced_hint = f"{location_hint}, Россия"
            else:
                enhanced_hint = location_hint
            
            location = self.geocoder.geocode(enhanced_hint, timeout=10)
            if location:
                return {
                    'latitude': location.latitude,
                    'longitude': location.longitude
                }
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding error: {e}")
        return None

    def _extract_coordinates_from_image_text(self, image_path: str) -> Optional[Dict[str, float]]:
        """Извлечение координат из текста на изображении (OCR)"""
        try:
            # Простая проверка на наличие координат в тексте
            # В реальной реализации здесь был бы OCR
            import re
            
            # Паттерны для поиска координат в тексте
            coord_patterns = [
                r'(\d{1,2}[.,]\d+)[°\s]*[NS]?\s*[,\s]\s*(\d{1,3}[.,]\d+)[°\s]*[EW]?',
                r'lat[:\s]*(\d{1,2}[.,]\d+).*lon[:\s]*(\d{1,3}[.,]\d+)',
                r'(\d{1,2}[.,]\d+)[,\s]+(\d{1,3}[.,]\d+)'
            ]
            
            # Здесь должен быть реальный OCR, пока возвращаем None
            return None
            
        except Exception as e:
            logger.error(f"Error extracting coordinates from image text: {e}")
        return None

    def _detect_region_from_objects(self, image_path: str, location_hint: Optional[str]) -> Optional[Dict[str, float]]:
        """Определение региона по объектам на изображении"""
        try:
            # НЕ возвращаем координаты по умолчанию только по названию города
            # Это должно происходить только после реального анализа изображения
            logger.info("🚫 Skipping default city coordinates - need real image analysis")
            
            # TODO: Здесь должен быть реальный анализ объектов на изображении
            # с помощью YOLO или других детекторов для определения региона
            
            return None  # Не возвращаем координаты без реального анализа
            
        except Exception as e:
            logger.error(f"Error detecting region from objects: {e}")
        return None

    def _select_best_candidate(self, candidates: List[Dict], location_hint: Optional[str]) -> Dict:
        """Выбор лучшего кандидата координат"""
        if not candidates:
            return None
        
        # Вычисляем взвешенную оценку для каждого кандидата
        for candidate in candidates:
            score = candidate['confidence'] * candidate['weight']
            
            # Бонус за соответствие подсказке местоположения
            if location_hint and candidate['source'] == 'location_hint':
                score *= 1.2
            
            # Бонус за российские координаты если подсказка содержит российский город
            if location_hint and any(city in location_hint.lower() 
                                   for city in ['россия', 'russia', 'москва', 'краснодар', 'санкт-петербург']):
                coords = candidate['coordinates']
                if self._is_in_russia(coords['latitude'], coords['longitude']):
                    score *= 1.1
            
            candidate['final_score'] = score
        
        # Возвращаем кандидата с максимальной оценкой
        return max(candidates, key=lambda x: x['final_score'])

    def _validate_coordinates(self, coordinates: Dict[str, float], location_hint: Optional[str]) -> bool:
        """Валидация координат"""
        if not coordinates:
            return False
        
        lat, lon = coordinates['latitude'], coordinates['longitude']
        
        # Проверка на валидные диапазоны
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return False
        
        # Проверка на нулевые координаты (часто ошибочные)
        if lat == 0.0 and lon == 0.0:
            return False
        
        # Проверка на координаты Пекина (проблемные дефолтные значения)
        if abs(lat - 39.9042) < 0.1 and abs(lon - 116.4074) < 0.1:
            logger.warning("🚫 Detected Beijing coordinates - likely default values, rejecting")
            return False
        
        # Если есть подсказка с российским городом, проверяем соответствие
        if location_hint and any(city in location_hint.lower() 
                               for city in ['россия', 'russia', 'москва', 'краснодар']):
            if not self._is_in_russia(lat, lon):
                logger.warning(f"🚫 Coordinates {lat}, {lon} not in Russia despite Russian location hint")
                return False
        
        return True

    def _is_in_russia(self, lat: float, lon: float) -> bool:
        """Проверка, находятся ли координаты в России"""
        return (self.russia_bounds['min_lat'] <= lat <= self.russia_bounds['max_lat'] and
                self.russia_bounds['min_lon'] <= lon <= self.russia_bounds['max_lon'])

    def get_smart_fallback_coordinates(self, location_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Получение умных резервных координат вместо дефолтных координат Пекина
        """
        if location_hint:
            hint_lower = location_hint.lower()
            
            # Российские города
            if any(city in hint_lower for city in ['россия', 'russia', 'москва', 'краснодар', 'санкт-петербург']):
                return {
                    'coordinates': self.regional_defaults['russia'],
                    'source': 'smart_fallback_russia',
                    'confidence': 0.3,
                    'message': 'Использованы координаты центра России'
                }
            
            # Европейские города
            elif any(city in hint_lower for city in ['европа', 'europe', 'берлин', 'париж', 'лондон']):
                return {
                    'coordinates': self.regional_defaults['europe'],
                    'source': 'smart_fallback_europe',
                    'confidence': 0.3,
                    'message': 'Использованы координаты центра Европы'
                }
        
        # Если нет подсказки или она не распознана - НЕ возвращаем координаты
        return {
            'coordinates': None,
            'source': 'no_fallback',
            'confidence': 0.0,
            'message': 'Координаты не определены. Добавьте подсказку местоположения для улучшения точности.'
        }
    
    def _analyze_with_panoramas(self, image_path: str, approximate_coords: Dict[str, float]) -> Optional[Dict[str, float]]:
        """
        Анализ изображения с использованием панорам для уточнения координат
        """
        try:
            from .panorama_analyzer_service import PanoramaAnalyzer
            from .yandex_maps_service import YandexMapsService
            
            # Инициализируем сервисы
            yandex_service = YandexMapsService()
            panorama_analyzer = PanoramaAnalyzer(yandex_service)
            
            # Анализируем с панорамами
            result = panorama_analyzer.analyze_location_with_panoramas(
                image_path,
                approximate_coords['latitude'],
                approximate_coords['longitude'],
                search_radius=300
            )
            
            if result.get('success') and result.get('coordinates'):
                logger.info(f"🎯 Panorama analysis successful: confidence {result.get('confidence', 0):.2f}")
                return result['coordinates']
            else:
                logger.info(f"📸 Panorama analysis failed: {result.get('message', 'Unknown error')}")
                return None
                
        except ImportError as e:
            logger.warning(f"Panorama analyzer not available: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in panorama analysis: {e}")
            return None
    
    def _extract_coordinates_with_mistral(self, image_path: str) -> Optional[Dict[str, float]]:
        """
        Извлечение координат из изображения с помощью Mistral AI OCR
        """
        try:
            logger.info("🤖 Analyzing image with Mistral AI OCR...")
            
            # Используем Mistral OCR для извлечения адресной информации
            ocr_result = self.mistral_ocr.extract_text_and_addresses(image_path)
            
            if not ocr_result.get('success'):
                logger.info(f"Mistral OCR failed: {ocr_result.get('error', 'Unknown error')}")
                return None
            
            # Извлекаем адресную информацию
            address_info = ocr_result.get('address_info', {})
            
            # Пробуем найти координаты в извлеченной информации
            coordinates = address_info.get('coordinates')
            if coordinates and coordinates.get('latitude') and coordinates.get('longitude'):
                logger.info(f"✅ Found coordinates in Mistral OCR: {coordinates}")
                return {
                    'latitude': float(coordinates['latitude']),
                    'longitude': float(coordinates['longitude'])
                }
            
            # Если прямых координат нет, пробуем геокодировать адрес
            full_address = address_info.get('full_address')
            if full_address:
                logger.info(f"🔍 Geocoding address from Mistral OCR: {full_address}")
                geocoded = self._geocode_location_hint(full_address)
                if geocoded:
                    logger.info(f"✅ Geocoded Mistral address: {geocoded}")
                    return geocoded
            
            # Пробуем отдельные компоненты адреса
            address_components = []
            if address_info.get('street'):
                address_components.append(address_info['street'])
            if address_info.get('city'):
                address_components.append(address_info['city'])
            if address_info.get('region'):
                address_components.append(address_info['region'])
            
            if address_components:
                combined_address = ', '.join(address_components)
                logger.info(f"🔍 Geocoding combined address: {combined_address}")
                geocoded = self._geocode_location_hint(combined_address)
                if geocoded:
                    logger.info(f"✅ Geocoded combined address: {geocoded}")
                    return geocoded
            
            logger.info("No usable address information found in Mistral OCR result")
            return None
            
        except Exception as e:
            logger.error(f"Error in Mistral OCR coordinate extraction: {e}")
            return None
