"""
Yandex Vision API Service для определения координат
Использует Yandex Cloud Vision для:
- OCR (распознавание текста на русском)
- Классификация объектов и сцен
- Определение типа местности
"""

import logging
import os
import base64
import requests
from typing import Dict, List, Any, Optional
import re

logger = logging.getLogger(__name__)


class YandexVisionService:
    """
    Сервис для работы с Yandex Cloud Vision API
    """
    
    def __init__(self):
        """Инициализация сервиса"""
        self.api_key = os.getenv('YANDEX_VISION_API_KEY') or os.getenv('YANDEX_API_KEY')
        self.folder_id = os.getenv('YANDEX_FOLDER_ID', '')
        self.vision_url = 'https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze'
        
        if not self.api_key:
            logger.warning("⚠️ YANDEX_VISION_API_KEY not found in environment")
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Полный анализ изображения через Yandex Vision
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Результаты анализа с текстом, классификацией и координатами
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'Yandex Vision API key not configured'
            }
        
        try:
            # Читаем изображение и кодируем в base64
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Формируем запрос для всех типов анализа
            request_data = {
                "folderId": self.folder_id,
                "analyze_specs": [
                    {
                        "content": image_data,
                        "features": [
                            {
                                "type": "TEXT_DETECTION",  # OCR
                                "text_detection_config": {
                                    "language_codes": ["ru", "en"]
                                }
                            },
                            {
                                "type": "CLASSIFICATION"  # Классификация сцены
                            }
                        ]
                    }
                ]
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Api-Key {self.api_key}"
            }
            
            response = requests.post(
                self.vision_url,
                json=request_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Yandex Vision API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"API returned status {response.status_code}"
                }
            
            result_data = response.json()
            
            # Обрабатываем результаты
            processed_result = self._process_vision_results(result_data)
            processed_result['success'] = True
            
            logger.info(f"✅ Yandex Vision analysis completed")
            return processed_result
            
        except Exception as e:
            logger.error(f"Error analyzing image with Yandex Vision: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_vision_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка результатов от Yandex Vision API
        
        Args:
            data: Сырые данные от API
            
        Returns:
            Обработанные результаты
        """
        result = {
            'text_detected': [],
            'addresses': [],
            'phone_numbers': [],
            'postal_codes': [],
            'scene_classification': [],
            'coordinates_hints': []
        }
        
        try:
            results = data.get('results', [])
            if not results:
                return result
            
            first_result = results[0]
            
            # Обработка текста (OCR)
            text_annotation = first_result.get('results', [])
            for item in text_annotation:
                if item.get('textDetection'):
                    text_detection = item['textDetection']
                    pages = text_detection.get('pages', [])
                    
                    for page in pages:
                        blocks = page.get('blocks', [])
                        for block in blocks:
                            lines = block.get('lines', [])
                            for line in lines:
                                words = line.get('words', [])
                                line_text = ' '.join([
                                    word.get('text', '') for word in words
                                ])
                                
                                if line_text.strip():
                                    result['text_detected'].append(line_text.strip())
                                    
                                    # Пытаемся извлечь полезную информацию
                                    self._extract_location_info(line_text, result)
                
                # Обработка классификации
                if item.get('classification'):
                    classification = item['classification']
                    properties = classification.get('properties', [])
                    
                    for prop in properties:
                        name = prop.get('name', '')
                        probability = prop.get('probability', 0)
                        
                        if probability > 0.5:  # Только уверенные результаты
                            result['scene_classification'].append({
                                'name': name,
                                'probability': probability
                            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing vision results: {e}")
            return result
    
    def _extract_location_info(self, text: str, result: Dict[str, Any]):
        """
        Извлечение информации о местоположении из текста
        
        Args:
            text: Распознанный текст
            result: Словарь для сохранения результатов
        """
        # Поиск адресов (упрощенный паттерн)
        address_patterns = [
            r'(?:ул\.|улица)\s+[\w\s]+,?\s*\d+',
            r'(?:пр-т|проспект)\s+[\w\s]+,?\s*\d+',
            r'(?:пер\.|переулок)\s+[\w\s]+,?\s*\d+',
            r'[\w\s]+,\s*д\.\s*\d+',
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            result['addresses'].extend(matches)
        
        # Поиск телефонных номеров
        phone_pattern = r'\+?7[\s\-]?\(?(\d{3})\)?[\s\-]?(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})'
        phones = re.findall(phone_pattern, text)
        if phones:
            for phone in phones:
                area_code = phone[0]
                result['phone_numbers'].append({
                    'full': f"+7 ({area_code}) {phone[1]}-{phone[2]}-{phone[3]}",
                    'area_code': area_code
                })
        
        # Поиск почтовых индексов
        postal_pattern = r'\b\d{6}\b'
        postal_codes = re.findall(postal_pattern, text)
        result['postal_codes'].extend(postal_codes)
    
    def get_coordinates_from_analysis(self, analysis_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Определение координат на основе анализа Yandex Vision
        
        Args:
            analysis_result: Результаты анализа изображения
            
        Returns:
            Координаты с метаданными или None
        """
        if not analysis_result.get('success'):
            return None
        
        # Проверяем телефонные коды для определения региона
        phone_numbers = analysis_result.get('phone_numbers', [])
        for phone in phone_numbers:
            area_code = phone.get('area_code', '')
            coordinates = self._get_coordinates_from_phone_code(area_code)
            if coordinates:
                coordinates['detected_by'] = 'yandex_vision_phone'
                coordinates['confidence'] = 0.8
                logger.info(f"📱 Координаты определены по телефонному коду: {area_code}")
                return coordinates
        
        # Проверяем почтовые индексы
        postal_codes = analysis_result.get('postal_codes', [])
        for postal_code in postal_codes:
            coordinates = self._get_coordinates_from_postal_code(postal_code)
            if coordinates:
                coordinates['detected_by'] = 'yandex_vision_postal'
                coordinates['confidence'] = 0.85
                logger.info(f"📮 Координаты определены по индексу: {postal_code}")
                return coordinates
        
        return None
    
    def _get_coordinates_from_phone_code(self, area_code: str) -> Optional[Dict[str, Any]]:
        """Определение координат по телефонному коду"""
        # База телефонных кодов городов России
        phone_codes = {
            '495': {'city': 'Москва', 'lat': 55.7558, 'lon': 37.6176},
            '499': {'city': 'Москва', 'lat': 55.7558, 'lon': 37.6176},
            '812': {'city': 'Санкт-Петербург', 'lat': 59.9343, 'lon': 30.3351},
            '343': {'city': 'Екатеринбург', 'lat': 56.8389, 'lon': 60.6057},
            '383': {'city': 'Новосибирск', 'lat': 55.0084, 'lon': 82.9357},
            '846': {'city': 'Самара', 'lat': 53.2001, 'lon': 50.15},
            '861': {'city': 'Краснодар', 'lat': 45.0355, 'lon': 38.9753},
            '843': {'city': 'Казань', 'lat': 55.8304, 'lon': 49.0661},
            '342': {'city': 'Пермь', 'lat': 58.0105, 'lon': 56.2502},
        }
        
        city_data = phone_codes.get(area_code)
        if city_data:
            return {
                'latitude': city_data['lat'],
                'longitude': city_data['lon'],
                'source': f"phone_code_{area_code}",
                'city': city_data['city']
            }
        return None
    
    def _get_coordinates_from_postal_code(self, postal_code: str) -> Optional[Dict[str, Any]]:
        """Определение координат по почтовому индексу"""
        # База почтовых индексов (примеры для Москвы и МО)
        postal_codes = {
            # Москва
            '101000': {'city': 'Москва (Центр)', 'lat': 55.7558, 'lon': 37.6176},
            '103132': {'city': 'Москва (Центр)', 'lat': 55.7558, 'lon': 37.6176},
            '119333': {'city': 'Москва (Юго-Запад)', 'lat': 55.7, 'lon': 37.5},
            '125009': {'city': 'Москва (Север)', 'lat': 55.8, 'lon': 37.6},
            # Московская область
            '140000': {'city': 'Люберцы', 'lat': 55.6769, 'lon': 37.8931},
            '141000': {'city': 'Мытищи', 'lat': 55.9116, 'lon': 37.7308},
        }
        
        # Проверяем диапазоны индексов
        if postal_code.startswith('10') or postal_code.startswith('11') or postal_code.startswith('12'):
            # Москва (101000-129999)
            return {
                'latitude': 55.7558,
                'longitude': 37.6176,
                'source': f"postal_code_{postal_code}",
                'city': 'Москва'
            }
        elif postal_code.startswith('14'):
            # Московская область (140000-149999)
            return {
                'latitude': 55.7,
                'longitude': 37.5,
                'source': f"postal_code_{postal_code}",
                'city': 'Московская область'
            }
        
        # Точное совпадение
        city_data = postal_codes.get(postal_code)
        if city_data:
            return {
                'latitude': city_data['lat'],
                'longitude': city_data['lon'],
                'source': f"postal_code_{postal_code}",
                'city': city_data['city']
            }
        
        return None
