"""
Mistral AI Service для анализа изображений и текста
"""
import os
import base64
import requests
import logging
from typing import Dict, Any, List, Optional
from PIL import Image
import io

logger = logging.getLogger(__name__)

class MistralAIService:
    def __init__(self):
        self.api_key = os.getenv('MISTRAL_API_KEY')
        self.base_url = "https://api.mistral.ai/v1"
        self.model = "pixtral-12b-2409"  # Mistral's vision model
        
        if not self.api_key:
            logger.warning("MISTRAL_API_KEY not found in environment variables")
    
    def _encode_image(self, image_path: str) -> str:
        """Кодирование изображения в base64"""
        try:
            with Image.open(image_path) as img:
                # Уменьшаем размер для экономии токенов
                img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                buffer.seek(0)
                
                return base64.b64encode(buffer.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            raise
    
    def analyze_image(self, image_path: str, prompt: str = None) -> Dict[str, Any]:
        """
        Анализ изображения с помощью Mistral AI
        """
        if not self.api_key:
            return {'success': False, 'error': 'Mistral API key not configured'}
        
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
                return {'success': False, 'error': 'No analysis returned from Mistral AI'}
                
        except requests.RequestException as e:
            logger.error(f"Mistral AI API error: {e}")
            return {'success': False, 'error': f'API request failed: {str(e)}'}
        except Exception as e:
            logger.error(f"Unexpected error in Mistral AI analysis: {e}")
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
      "confidence": 0.0-1.0
    }
  ],
  "building_analysis": "общий анализ здания",
  "recommendations": ["рекомендация 1", "рекомендация 2"]
}"""
        
        return self.analyze_image(image_path, violation_prompt)
    
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
