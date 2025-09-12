"""
Mistral AI OCR Service для извлечения адресов и текста из изображений
"""

import logging
from typing import Dict, Any, List, Optional
from .mistral_ai_service import MistralAIService
import json
import re

logger = logging.getLogger(__name__)

class MistralOCRService:
    """
    OCR сервис на базе Mistral AI для извлечения адресной информации
    """
    
    def __init__(self):
        self.mistral_service = MistralAIService()
        
    def extract_text_and_addresses(self, image_path: str) -> Dict[str, Any]:
        """
        Извлечение всего текста и адресной информации из изображения
        """
        try:
            ocr_prompt = """Внимательно проанализируй изображение и извлеки ВСЮ текстовую информацию:

1. АДРЕСНАЯ ИНФОРМАЦИЯ:
   - Номера домов (любые цифры на табличках, зданиях)
   - Названия улиц (полностью, включая сокращения)
   - Названия районов, городов
   - Почтовые индексы
   - Координаты (если есть)

2. ВЫВЕСКИ И ТАБЛИЧКИ:
   - Названия организаций
   - Рекламные вывески
   - Информационные таблички
   - Указатели направлений

3. ЛЮБОЙ ДРУГОЙ ТЕКСТ:
   - Надписи на транспорте
   - Граффити с текстом
   - Номерные знаки
   - Любые видимые буквы и цифры

ВАЖНО: Извлекай даже частично видимый или нечеткий текст. Укажи уровень уверенности для каждого элемента.

Верни результат в JSON формате:
{
  "text_found": true/false,
  "addresses": {
    "house_numbers": ["номер1", "номер2"],
    "street_names": ["улица Ленина", "проспект Мира"],
    "districts": ["Центральный район"],
    "cities": ["Краснодар"],
    "postal_codes": ["350000"],
    "full_addresses": ["ул. Ленина 123"]
  },
  "signs_and_text": [
    {
      "text": "извлеченный текст",
      "type": "вывеска/табличка/граффити/другое",
      "confidence": 0.0-1.0
    }
  ],
  "coordinates_found": ["координаты если есть"],
  "overall_confidence": 0.0-1.0
}"""
            
            logger.info(f"🔍 Extracting text from image: {image_path}")
            result = self.mistral_service.analyze_image(image_path, ocr_prompt)
            
            if result.get('success') and result.get('analysis'):
                return self._parse_ocr_result(result['analysis'])
            else:
                logger.error(f"Mistral OCR failed: {result}")
                return {
                    'success': False,
                    'error': result.get('error', 'OCR analysis failed')
                }
                
        except Exception as e:
            logger.error(f"Error in Mistral OCR: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_ocr_result(self, analysis_text: str) -> Dict[str, Any]:
        """
        Парсинг результата OCR анализа
        """
        try:
            # Ищем JSON в ответе
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group())
                logger.info(f"✅ Mistral OCR parsed: {parsed_data}")
                
                # Извлекаем адресную информацию
                addresses = parsed_data.get('addresses', {})
                signs_text = parsed_data.get('signs_and_text', [])
                
                # Собираем все найденные адреса
                all_addresses = []
                if addresses.get('full_addresses'):
                    all_addresses.extend(addresses['full_addresses'])
                
                # Формируем адреса из компонентов
                street_names = addresses.get('street_names', [])
                house_numbers = addresses.get('house_numbers', [])
                
                for street in street_names:
                    for house in house_numbers:
                        combined_address = f"{street} {house}"
                        if combined_address not in all_addresses:
                            all_addresses.append(combined_address)
                
                # Извлекаем все тексты для дополнительного анализа
                all_text = []
                for sign in signs_text:
                    if isinstance(sign, dict) and sign.get('text'):
                        all_text.append(sign['text'])
                
                return {
                    'success': True,
                    'source': 'mistral_ocr',
                    'addresses_found': all_addresses,
                    'street_names': street_names,
                    'house_numbers': house_numbers,
                    'districts': addresses.get('districts', []),
                    'cities': addresses.get('cities', []),
                    'all_text': all_text,
                    'coordinates': parsed_data.get('coordinates_found', []),
                    'confidence': parsed_data.get('overall_confidence', 0.7),
                    'raw_analysis': analysis_text
                }
            else:
                # Если JSON не найден, пытаемся извлечь адреса из текста
                logger.warning("No JSON found, trying text extraction")
                return self._extract_from_text(analysis_text)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return self._extract_from_text(analysis_text)
        except Exception as e:
            logger.error(f"Error parsing OCR result: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """
        Извлечение адресов из обычного текста (fallback)
        """
        try:
            # Простые регулярные выражения для поиска адресов
            street_patterns = [
                r'ул\.?\s*([А-Яа-я\s]+)',
                r'улица\s+([А-Яа-я\s]+)',
                r'проспект\s+([А-Яа-я\s]+)',
                r'пр\.?\s*([А-Яа-я\s]+)',
                r'переулок\s+([А-Яа-я\s]+)',
                r'пер\.?\s*([А-Яа-я\s]+)'
            ]
            
            house_patterns = [
                r'дом\s+(\d+[а-я]?)',
                r'д\.?\s*(\d+[а-я]?)',
                r'№\s*(\d+[а-я]?)',
                r'\b(\d{1,4}[а-я]?)\b'
            ]
            
            streets = []
            houses = []
            
            for pattern in street_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                streets.extend([match.strip() for match in matches])
            
            for pattern in house_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                houses.extend([match.strip() for match in matches])
            
            # Удаляем дубликаты
            streets = list(set(streets))
            houses = list(set(houses))
            
            logger.info(f"Text extraction found: streets={streets}, houses={houses}")
            
            return {
                'success': True,
                'source': 'mistral_ocr_text',
                'addresses_found': [],
                'street_names': streets,
                'house_numbers': houses,
                'districts': [],
                'cities': [],
                'all_text': [text],
                'coordinates': [],
                'confidence': 0.5,
                'raw_analysis': text
            }
            
        except Exception as e:
            logger.error(f"Error in text extraction: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def extract_coordinates_from_text(self, image_path: str) -> Optional[Dict[str, float]]:
        """
        Извлечение координат из текста на изображении
        """
        try:
            result = self.extract_text_and_addresses(image_path)
            
            if result.get('success') and result.get('coordinates'):
                # Парсим координаты из текста
                for coord_text in result['coordinates']:
                    coords = self._parse_coordinates(coord_text)
                    if coords:
                        return coords
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting coordinates: {e}")
            return None
    
    def _parse_coordinates(self, coord_text: str) -> Optional[Dict[str, float]]:
        """
        Парсинг координат из текста
        """
        try:
            # Паттерны для координат
            patterns = [
                r'(\d+\.?\d*)[°\s]*[NS]?\s*[,\s]\s*(\d+\.?\d*)[°\s]*[EW]?',
                r'lat[:\s]*(\d+\.?\d*)[,\s]*lon[:\s]*(\d+\.?\d*)',
                r'(\d{2}\.\d+)[,\s]+(\d{2}\.\d+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, coord_text, re.IGNORECASE)
                if match:
                    lat, lon = float(match.group(1)), float(match.group(2))
                    
                    # Проверяем разумность координат для России
                    if 41 <= lat <= 82 and 19 <= lon <= 180:
                        return {'latitude': lat, 'longitude': lon}
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing coordinates: {e}")
            return None
