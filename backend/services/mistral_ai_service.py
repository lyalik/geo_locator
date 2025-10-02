import os
import base64
import requests
import logging
from typing import Dict, Any, List, Optional
from PIL import Image
import io
from .dataset_search_service import DatasetSearchService

logger = logging.getLogger(__name__)

class MistralAIService:
    def __init__(self):
        self.api_key = os.getenv('MISTRAL_API_KEY')
        self.base_url = "https://api.mistral.ai/v1"
        # Используем лучшую модель Mistral для анализа изображений
        self.model = os.getenv('MISTRAL_MODEL', "pixtral-12b-2409")  # Mistral's vision model
        self.dataset_search = DatasetSearchService()
        
        if not self.api_key:
            logger.warning("MISTRAL_API_KEY not found in environment variables")
            # Для демо режима создаем mock результаты
            self.demo_mode = True
        else:
            self.demo_mode = False
            logger.info(f"🤖 AI initialized with API key: {self.api_key[:8]}...")
    
    def _encode_image(self, image_path: str) -> str:
        """Кодирование изображения в base64"""
        try:
            with Image.open(image_path) as img:
                # Уменьшаем размер для экономии токенов
                img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                
                # Конвертируем RGBA в RGB для JPEG
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Создаем белый фон
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                buffer.seek(0)
                
                return base64.b64encode(buffer.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            raise
    
    def analyze_image(self, image_path: str, prompt: str = None) -> Dict[str, Any]:
        """
        Анализ изображения с помощью AI
        """
        if not self.api_key:
            return {'success': False, 'error': 'AI API key not configured'}
        
        try:
            # Кодируем изображение
            image_base64 = self._encode_image(image_path)
            
            # Базовый промпт для анализа недвижимости
            default_prompt = """Проанализируй это изображение и опиши:
1. Тип здания или объекта недвижимости
2. Архитектурные особенности
3. Состояние объекта
4. Видимые адресные указатели или номера домов
5. Окружающую инфраструктуру
6. Возможные нарушения использования нежилого фонда

Ответь на русском языке в структурированном формате."""
            
            analysis_prompt = prompt or default_prompt
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": analysis_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.3
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                analysis = result['choices'][0]['message']['content']
                
                return {
                    'success': True,
                    'source': 'mistral_ai',
                    'analysis': analysis,
                    'model': self.model,
                    'tokens_used': result.get('usage', {}).get('total_tokens', 0)
                }
            else:
                return {'success': False, 'error': 'No analysis returned from AI'}
                
        except requests.RequestException as e:
            logger.error(f"AI API error: {e}")
            return {'success': False, 'error': f'API request failed: {str(e)}'}
        except Exception as e:
            logger.error(f"Unexpected error in AI analysis: {e}")
            return {'success': False, 'error': f'Analysis failed: {str(e)}'}
    
    def detect_violations(self, image_path: str) -> Dict[str, Any]:
        """
        Специализированная детекция нарушений
        """
        violation_prompt = """Проанализируй изображение на предмет нарушений использования нежилого фонда:

1. НЕЗАКОННЫЕ ПРИСТРОЙКИ:
   - Самовольные пристройки к зданиям
   - Незаконные балконы, террасы
   - Временные конструкции

2. НАРУШЕНИЯ ФАСАДОВ:
   - Неразрешенные вывески
   - Изменение архитектурного облика
   - Нарушение цветовой схемы

3. ИСПОЛЬЗОВАНИЕ ТЕРРИТОРИИ:
   - Незаконная парковка
   - Складирование материалов
   - Торговые точки без разрешения

4. ТЕХНИЧЕСКОЕ СОСТОЯНИЕ:
   - Аварийное состояние конструкций
   - Нарушения безопасности

Верни результат в JSON формате:
{
  "violations_detected": true/false,
  "violations": [
    {
      "type": "тип нарушения",
      "description": "описание",
      "severity": "low/medium/high",
      "confidence": 0.0-100.0
    }
  ],
  "building_analysis": "общий анализ здания",
  "recommendations": ["рекомендация 1", "рекомендация 2"]
}"""
        
        try:
            # Если нет API ключа, возвращаем демо результаты
            if self.demo_mode:
                logger.info(f"🤖 AI DEMO MODE - generating mock violations")
                return {
                    'success': True,
                    'violations': [
                        {
                            'type': 'facade_violation',
                            'description': 'Обнаружена неразрешенная вывеска на фасаде здания',
                            'severity': 'medium',
                            'confidence': 0.78
                        },
                        {
                            'type': 'unauthorized_construction',
                            'description': 'Возможная самовольная пристройка к зданию',
                            'severity': 'high',
                            'confidence': 0.65
                        }
                    ],
                    'building_analysis': 'Многоэтажное жилое здание с признаками нарушений фасада',
                    'recommendations': ['Проверить разрешения на вывески', 'Обследовать пристройки']
                }
            
            result = self.analyze_image(image_path, violation_prompt)
            logger.info(f"🤖 AI raw result: {result}")
            
            if result.get('success') and result.get('analysis'):
                # Парсим JSON ответ из текста
                import json
                import re
                
                analysis_text = result['analysis']
                logger.info(f"🤖 AI analysis text: {analysis_text}")
                
                # Ищем JSON в ответе
                json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                if json_match:
                    try:
                        parsed_data = json.loads(json_match.group())
                        logger.info(f"🤖 AI parsed JSON: {parsed_data}")
                        
                        # Преобразуем в нужный формат
                        violations = []
                        if parsed_data.get('violations_detected') and parsed_data.get('violations'):
                            for v in parsed_data['violations']:
                                violations.append({
                                    'type': v.get('type', 'unknown'),
                                    'description': v.get('description', ''),
                                    'severity': v.get('severity', 'medium'),
                                    'confidence': float(v.get('confidence', 0.0))
                                })
                        
                        # Убираем демо нарушения - используем только реальные результаты анализа
                        logger.info(f"🤖 AI - Found {len(violations)} real violations")
                        
                        return {
                            'success': True,
                            'violations': violations,
                            'building_analysis': parsed_data.get('building_analysis', ''),
                            'recommendations': parsed_data.get('recommendations', [])
                        }
                    except json.JSONDecodeError as e:
                        logger.error(f"🤖 AI JSON parse error: {e}")
                        # Fallback - создаем базовый результат
                        return {
                            'success': True,
                            'violations': [{
                                'type': 'general_analysis',
                                'description': analysis_text[:200] + '...',
                                'severity': 'medium',
                                'confidence': 0.7
                            }],
                            'building_analysis': analysis_text,
                            'recommendations': []
                        }
                else:
                    logger.warning(f"🤖 AI: No JSON found in response")
                    return {
                        'success': True,
                        'violations': [{
                            'type': 'text_analysis',
                            'description': analysis_text[:100] + '...',
                            'severity': 'low',
                            'confidence': 0.5
                        }],
                        'building_analysis': analysis_text,
                        'recommendations': []
                    }
            else:
                logger.error(f"🤖 AI: Analysis failed - {result}")
                return {'success': False, 'error': 'Analysis failed'}
                
        except Exception as e:
            logger.error(f"🤖 AI detect_violations error: {e}")
            return {'success': False, 'error': str(e)}
    
    def extract_address_info(self, image_path: str) -> Dict[str, Any]:
        """
        Извлечение адресной информации из изображения
        """
        address_prompt = """Найди и извлеки всю адресную информацию с этого изображения:

1. НОМЕРА ДОМОВ
2. НАЗВАНИЯ УЛИЦ
3. ВЫВЕСКИ С АДРЕСАМИ
4. ПОЧТОВЫЕ ИНДЕКСЫ
5. НАЗВАНИЯ РАЙОНОВ/ГОРОДОВ
6. ОРИЕНТИРЫ И НАЗВАНИЯ ОБЪЕКТОВ

Верни результат в JSON формате:
{
  "address_found": true/false,
  "house_numbers": ["номер1", "номер2"],
  "street_names": ["улица1", "улица2"],
  "postal_codes": ["индекс1"],
  "districts": ["район1"],
  "landmarks": ["ориентир1", "ориентир2"],
  "full_addresses": ["полный адрес если найден"],
  "confidence": 0.0-1.0
}"""
        
        return self.analyze_image(image_path, address_prompt)
    
    def analyze_property_type(self, image_path: str) -> Dict[str, Any]:
        """
        Определение типа недвижимости
        """
        property_prompt = """Определи тип недвижимости на изображении:

ТИПЫ ЗДАНИЙ:
- Жилой дом (многоквартирный/частный)
- Офисное здание
- Торговый центр/магазин
- Промышленное здание
- Складское помещение
- Гараж/паркинг
- Социальный объект (школа, больница)
- Культурный объект (театр, музей)

Верни результат в JSON формате:
{
  "property_type": "тип недвижимости",
  "building_class": "класс здания (A/B/C/D)",
  "floors_count": число_этажей,
  "construction_period": "период постройки",
  "architectural_style": "архитектурный стиль",
  "condition": "состояние (отличное/хорошее/удовлетворительное/плохое)",
  "commercial_use": true/false,
  "confidence": 0.0-1.0
}"""
        
        return self.analyze_image(image_path, property_prompt)
    
    def extract_location_info(self, image_path: str) -> Dict[str, Any]:
        """
        Извлечение информации о местоположении из изображения:
        - Автомобильные номера с регионами
        - Названия улиц и адреса
        - Номера домов
        - Названия организаций и заведений
        - Дорожные знаки с названиями
        """
        location_prompt = """Проанализируй изображение и извлеки ЛЮБУЮ информацию о местоположении:

1. АВТОМОБИЛЬНЫЕ НОМЕРА:
   - Российские номера формата А123АА777 (регион в конце)
   - Укажи регион и город

2. АДРЕСА И УЛИЦЫ:
   - Названия улиц на табличках
   - Номера домов
   - Названия районов

3. ОРГАНИЗАЦИИ:
   - Вывески магазинов, кафе, офисов
   - Названия торговых центров
   - Бренды и компании

4. ДОРОЖНЫЕ ЗНАКИ:
   - Указатели направлений
   - Названия населенных пунктов
   - Расстояния до городов

Верни JSON:
{
  "found": true/false,
  "info_type": "license_plate/street/address/organization/sign",
  "extracted_text": "точный текст",
  "location": {
    "city": "город",
    "street": "улица",
    "house_number": "номер дома",
    "region": "регион/область"
  },
  "license_plates": [
    {"plate": "А123АА777", "region_code": "777", "region_name": "Москва"}
  ],
  "confidence": 0.0-1.0
}

Если ничего не найдено, верни {"found": false}"""
        
        result = self.analyze_image(image_path, location_prompt)
        
        if not result.get('success'):
            return {
                'success': False,
                'message': 'Mistral AI analysis failed'
            }
        
        analysis = result.get('analysis', {})
        
        # Если нашли информацию о местоположении
        if analysis.get('found'):
            # Пробуем определить координаты
            location = analysis.get('location', {})
            city = location.get('city', '')
            street = location.get('street', '')
            region = location.get('region', '')
            
            # Проверяем автомобильные номера
            license_plates = analysis.get('license_plates', [])
            if license_plates:
                # Используем регион из номера
                plate_info = license_plates[0]
                region_name = plate_info.get('region_name', '')
                
                # Базовые координаты регионов (можно расширить)
                region_coords = {
                    'Москва': {'lat': 55.7558, 'lon': 37.6176},
                    'Санкт-Петербург': {'lat': 59.9311, 'lon': 30.3609},
                    'Московская область': {'lat': 55.7, 'lon': 37.5},
                }
                
                coords = region_coords.get(region_name)
                if coords:
                    return {
                        'success': True,
                        'coordinates': {
                            'latitude': coords['lat'],
                            'longitude': coords['lon'],
                            'source': 'mistral_ai_ocr',
                            'confidence': analysis.get('confidence', 0.7)
                        },
                        'info_type': 'license_plate',
                        'extracted_info': f"Номер {plate_info.get('plate')} → {region_name}",
                        'details': analysis
                    }
            
            # Если есть город и улица, можно попробовать геокодирование
            if city and street:
                # Здесь можно добавить вызов Yandex Geocoder
                return {
                    'success': True,
                    'info_type': 'address',
                    'extracted_info': f"{city}, {street}",
                    'details': analysis,
                    'needs_geocoding': True  # Флаг для дальнейшей обработки
                }
        
        return {
            'success': False,
            'message': 'No location information found in image',
            'details': analysis
        }
