"""
Google Vision и Gemini Service для анализа изображений и текста
"""
import os
import base64
import logging
from typing import Dict, Any, List, Optional
from PIL import Image
import io
import json
import google.generativeai as genai
from google.cloud import vision

logger = logging.getLogger(__name__)

class GoogleVisionService:
    def __init__(self):
        # Настройка Google Cloud Vision
        self.vision_client = None
        self.credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        # Настройка Gemini
        self.gemini_api_key = os.getenv('GOOGLE_API_KEY')
        self.gemini_model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
        
        # Инициализация Gemini
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel(self.gemini_model)
            logger.info(f"🤖 Gemini initialized with model: {self.gemini_model}")
        
        # Инициализация архивного сервиса для улучшения анализа
        try:
            from .archive_photo_service import ArchivePhotoService
            self.archive_service = ArchivePhotoService()
            logger.info("🏛️ Archive service integrated into Google Vision")
        except Exception as e:
            logger.warning(f"Archive service not available in Google Vision: {e}")
            self.archive_service = None
        else:
            logger.warning("GOOGLE_API_KEY not found in environment variables")
            self.model = None
        
        # Инициализация Google Cloud Vision
        if self.credentials_path and os.path.exists(self.credentials_path):
            try:
                self.vision_client = vision.ImageAnnotatorClient()
                logger.info("🔍 Google Cloud Vision initialized")
            except Exception as e:
                logger.warning(f"Google Cloud Vision initialization failed: {e}")
        else:
            logger.warning("Google Cloud Vision credentials not found")
    
    def _prepare_image(self, image_path: str) -> tuple:
        """Подготовка изображения для анализа"""
        try:
            with Image.open(image_path) as img:
                # Уменьшаем размер для экономии токенов
                img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                
                # Конвертируем RGBA в RGB для JPEG
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Сохраняем в буфер
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                buffer.seek(0)
                
                # Возвращаем данные для разных API
                image_data = buffer.getvalue()
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                return image_data, image_base64
        except Exception as e:
            logger.error(f"Error preparing image: {e}")
            raise
    
    def analyze_image_with_gemini(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Анализ изображения с помощью Gemini"""
        if not self.model:
            return {'success': False, 'error': 'Gemini API not configured'}
        
        try:
            image_data, _ = self._prepare_image(image_path)
            
            # Создаем объект изображения для Gemini
            image_part = {
                "mime_type": "image/jpeg",
                "data": image_data
            }
            
            # Отправляем запрос к Gemini
            response = self.model.generate_content([prompt, image_part])
            
            if response.text:
                return {
                    'success': True,
                    'source': 'gemini',
                    'analysis': response.text,
                    'model': self.gemini_model
                }
            else:
                return {'success': False, 'error': 'No response from Gemini'}
                
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return {'success': False, 'error': f'Gemini analysis failed: {str(e)}'}
    
    def extract_text_with_vision(self, image_path: str) -> Dict[str, Any]:
        """Извлечение текста с помощью Google Cloud Vision OCR"""
        if not self.vision_client:
            return {'success': False, 'error': 'Google Cloud Vision not configured'}
        
        try:
            image_data, _ = self._prepare_image(image_path)
            image = vision.Image(content=image_data)
            
            # Выполняем OCR
            response = self.vision_client.text_detection(image=image)
            texts = response.text_annotations
            
            if texts:
                full_text = texts[0].description
                text_blocks = []
                
                for text in texts[1:]:  # Пропускаем первый элемент (полный текст)
                    vertices = [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
                    text_blocks.append({
                        'text': text.description,
                        'confidence': getattr(text, 'confidence', 0.9),
                        'bounding_box': vertices
                    })
                
                return {
                    'success': True,
                    'source': 'google_vision',
                    'full_text': full_text,
                    'text_blocks': text_blocks
                }
            else:
                return {
                    'success': True,
                    'source': 'google_vision',
                    'full_text': '',
                    'text_blocks': []
                }
                
        except Exception as e:
            logger.error(f"Google Vision OCR error: {e}")
            return {'success': False, 'error': f'OCR failed: {str(e)}'}
    
    def analyze_image(self, image_path: str, prompt: str = None) -> Dict[str, Any]:
        """
        Общий анализ изображения
        """
        default_prompt = """Проанализируй это изображение и опиши:
1. Тип здания или объекта недвижимости
2. Архитектурные особенности
3. Состояние объекта
4. Видимые адресные указатели или номера домов
5. Окружающую инфраструктуру
6. Возможные нарушения использования нежилого фонда

Ответь на русском языке в структурированном формате."""
        
        analysis_prompt = prompt or default_prompt
        return self.analyze_image_with_gemini(image_path, analysis_prompt)
    
    def detect_violations(self, image_path: str) -> Dict[str, Any]:
        """
        Специализированная детекция нарушений с помощью Gemini
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
            result = self.analyze_image_with_gemini(image_path, violation_prompt)
            logger.info(f"🤖 Gemini raw result: {result}")
            
            if result.get('success') and result.get('analysis'):
                analysis_text = result['analysis']
                logger.info(f"🤖 Gemini analysis text: {analysis_text}")
                
                # Парсим JSON из ответа
                import re
                json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                if json_match:
                    try:
                        parsed_data = json.loads(json_match.group())
                        logger.info(f"🤖 Gemini parsed JSON: {parsed_data}")
                        
                        # Преобразуем в нужный формат
                        violations = []
                        if parsed_data.get('violations_detected') and parsed_data.get('violations'):
                            for v in parsed_data['violations']:
                                violations.append({
                                    'type': v.get('type', 'unknown'),
                                    'description': v.get('description', ''),
                                    'severity': v.get('severity', 'medium'),
                                    'confidence': float(v.get('confidence', 0.0)),
                                    'source': 'gemini'
                                })
                        
                        logger.info(f"🤖 Gemini - Found {len(violations)} violations")
                        
                        return {
                            'success': True,
                            'violations': violations,
                            'building_analysis': parsed_data.get('building_analysis', ''),
                            'recommendations': parsed_data.get('recommendations', []),
                            'source': 'gemini'
                        }
                    except json.JSONDecodeError as e:
                        logger.error(f"🤖 Gemini JSON parse error: {e}")
                        # Fallback - создаем базовый результат
                        return {
                            'success': True,
                            'violations': [{
                                'type': 'general_analysis',
                                'description': analysis_text[:200] + '...',
                                'severity': 'medium',
                                'confidence': 0.7,
                                'source': 'gemini'
                            }],
                            'building_analysis': analysis_text,
                            'recommendations': [],
                            'source': 'gemini'
                        }
                else:
                    logger.warning(f"🤖 Gemini: No JSON found in response")
                    return {
                        'success': True,
                        'violations': [{
                            'type': 'text_analysis',
                            'description': analysis_text[:100] + '...',
                            'severity': 'low',
                            'confidence': 0.5,
                            'source': 'gemini'
                        }],
                        'building_analysis': analysis_text,
                        'recommendations': [],
                        'source': 'gemini'
                    }
            else:
                logger.error(f"🤖 Gemini: Analysis failed - {result}")
                return {'success': False, 'error': 'Analysis failed'}
                
        except Exception as e:
            logger.error(f"Error in Gemini analysis: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_violations_with_archive_context(self, image_path: str, custom_prompt: str = None) -> Dict[str, Any]:
        """
        Анализ нарушений с использованием контекста из архивных фото.
        
        Args:
            image_path: Путь к изображению
            custom_prompt: Дополнительный промпт для анализа
            
        Returns:
            Результат анализа с архивным контекстом
        """
        try:
            result = {
                'success': True,
                'archive_context': None,
                'enhanced_analysis': None,
                'similar_buildings': []
            }
            
            # Получаем контекст из архивных фото
            if self.archive_service:
                # Ищем похожие здания в архиве
                similar_buildings = self.archive_service.find_similar_buildings(image_path, threshold=0.6)
                result['similar_buildings'] = similar_buildings
                
                if similar_buildings:
                    # Создаем контекст на основе архивных данных
                    archive_context = self._create_archive_context(similar_buildings)
                    result['archive_context'] = archive_context
                    
                    # Улучшенный промпт с архивным контекстом
                    enhanced_prompt = self._create_enhanced_violation_prompt(archive_context, custom_prompt)
                    
                    # Анализ с улучшенным промптом
                    enhanced_analysis = self.analyze_image_with_gemini(image_path, enhanced_prompt)
                    result['enhanced_analysis'] = enhanced_analysis
                    
                    logger.info(f"🏛️ Enhanced violation analysis with {len(similar_buildings)} archive matches")
                else:
                    # Обычный анализ без архивного контекста
                    standard_analysis = self.analyze_image_with_gemini(image_path, custom_prompt or self._get_default_violation_prompt())
                    result['enhanced_analysis'] = standard_analysis
                    logger.info("📋 Standard violation analysis (no archive matches)")
            else:
                # Архивный сервис недоступен
                standard_analysis = self.analyze_image_with_gemini(image_path, custom_prompt or self._get_default_violation_prompt())
                result['enhanced_analysis'] = standard_analysis
                logger.info("📋 Standard violation analysis (archive service unavailable)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in archive-enhanced violation analysis: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_archive_context(self, similar_buildings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Создает контекст на основе похожих зданий из архива."""
        try:
            context = {
                'building_types': [],
                'architectural_styles': [],
                'common_violations': [],
                'historical_info': [],
                'location_context': []
            }
            
            for building in similar_buildings[:3]:  # Берем топ-3 похожих
                metadata = building.get('metadata', {})
                
                # Типы зданий
                building_type = metadata.get('building_type')
                if building_type and building_type not in context['building_types']:
                    context['building_types'].append(building_type)
                
                # Архитектурные стили
                arch_style = metadata.get('architectural_style')
                if arch_style and arch_style not in context['architectural_styles']:
                    context['architectural_styles'].append(arch_style)
                
                # Историческая информация
                if metadata.get('construction_year'):
                    context['historical_info'].append({
                        'description': metadata.get('description', ''),
                        'year': metadata.get('construction_year'),
                        'address': metadata.get('address', '')
                    })
                
                # Контекст местоположения
                if metadata.get('address'):
                    context['location_context'].append(metadata['address'])
            
            return context
            
        except Exception as e:
            logger.error(f"Error creating archive context: {e}")
            return {}
    
    def _create_enhanced_violation_prompt(self, archive_context: Dict[str, Any], custom_prompt: str = None) -> str:
        """Создает улучшенный промпт с архивным контекстом."""
        try:
            base_prompt = custom_prompt or self._get_default_violation_prompt()
            
            context_info = []
            
            if archive_context.get('building_types'):
                context_info.append(f"Тип зданий в этом районе: {', '.join(archive_context['building_types'])}")
            
            if archive_context.get('architectural_styles'):
                context_info.append(f"Архитектурные стили: {', '.join(archive_context['architectural_styles'])}")
            
            if archive_context.get('historical_info'):
                historical = archive_context['historical_info'][0]  # Берем первое
                context_info.append(f"Историческая справка: {historical.get('description', '')} ({historical.get('year', 'неизвестно')})")
            
            if archive_context.get('location_context'):
                context_info.append(f"Район: {archive_context['location_context'][0]}")
            
            if context_info:
                enhanced_prompt = f"""КОНТЕКСТ ИЗ АРХИВНЫХ ДАННЫХ:
{chr(10).join(context_info)}

ОСНОВНОЙ АНАЛИЗ:
{base_prompt}

Учитывай архивный контекст при анализе нарушений и особенностей объекта."""
            else:
                enhanced_prompt = base_prompt
            
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Error creating enhanced prompt: {e}")
            return custom_prompt or self._get_default_violation_prompt()
    
    def _get_default_violation_prompt(self) -> str:
        """Возвращает стандартный промпт для анализа нарушений."""
        return """Проанализируй изображение и определи:

1. НАРУШЕНИЯ И ПРОБЛЕМЫ:
   - Архитектурные нарушения
   - Проблемы с фасадом
   - Нарушения благоустройства
   - Проблемы с инфраструктурой

2. ТЕХНИЧЕСКОЕ СОСТОЯНИЕ:
   - Состояние здания
   - Видимые повреждения
   - Необходимость ремонта

3. СООТВЕТСТВИЕ НОРМАМ:
   - Градостроительные нормы
   - Архитектурные требования
   - Безопасность

Верни результат в JSON формате с детальным описанием найденных проблем."""
    
    def extract_address_info(self, image_path: str) -> Dict[str, Any]:
        """
        Извлечение адресной информации из изображения
        Комбинирует OCR (Google Vision) и анализ (Gemini)
        """
        # Сначала извлекаем текст с помощью OCR
        ocr_result = self.extract_text_with_vision(image_path)
        
        # Затем анализируем с помощью Gemini
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
        
        gemini_result = self.analyze_image_with_gemini(image_path, address_prompt)
        
        # Комбинируем результаты
        combined_result = {
            'success': True,
            'ocr_text': ocr_result.get('full_text', '') if ocr_result.get('success') else '',
            'gemini_analysis': gemini_result.get('analysis', '') if gemini_result.get('success') else '',
            'source': 'google_vision_gemini'
        }
        
        return combined_result
    
    def analyze_property_type(self, image_path: str) -> Dict[str, Any]:
        """
        Определение типа недвижимости с помощью Gemini
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
        
        return self.analyze_image_with_gemini(image_path, property_prompt)
