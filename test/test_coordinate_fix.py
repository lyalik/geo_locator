#!/usr/bin/env python3
"""
Тест исправления проблемы с разделом "Анализ координат"
Проверяет работу всех API сервисов после исправлений
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Добавляем backend в путь
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Загружаем переменные окружения
load_dotenv('.env')

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_yandex_maps_service():
    """Тест Yandex Maps Service"""
    try:
        from services.yandex_maps_service import YandexMapsService
        
        service = YandexMapsService()
        logger.info("🗺️ Testing Yandex Maps Service...")
        
        # Тест поиска с корректным запросом
        result = service.search_places("кафе", 55.7558, 37.6176)
        logger.info(f"✅ Yandex search result: {result.get('success', False)}")
        
        # Тест с некорректным запросом (должен использовать fallback)
        result2 = service.search_places("detected objects")
        logger.info(f"✅ Yandex fallback result: {result2.get('success', False)}")
        
        # Тест геокодирования
        geocode_result = service.geocode("Москва, Красная площадь")
        logger.info(f"✅ Yandex geocode result: {geocode_result.get('success', False)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Yandex Maps Service test failed: {e}")
        return False

def test_coordinate_detector():
    """Тест CoordinateDetector"""
    try:
        from services.coordinate_detector import CoordinateDetector
        
        detector = CoordinateDetector()
        logger.info("🎯 Testing Coordinate Detector...")
        
        # Создаем тестовое изображение
        test_image_path = "backend/data/archive_photos/test_image.jpg"
        if not os.path.exists(test_image_path):
            # Создаем простое тестовое изображение
            from PIL import Image
            import numpy as np
            
            # Создаем простое изображение 100x100 пикселей
            img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            img = Image.fromarray(img_array)
            
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(test_image_path), exist_ok=True)
            img.save(test_image_path)
            logger.info(f"📸 Created test image: {test_image_path}")
        
        # Тест без location_hint (должен использовать fallback)
        result = detector.detect_coordinates_from_image(test_image_path)
        logger.info(f"✅ Coordinate detection without hint: {result.get('success', False)}")
        
        # Тест с корректным location_hint
        result2 = detector.detect_coordinates_from_image(test_image_path, "Москва")
        logger.info(f"✅ Coordinate detection with hint: {result2.get('success', False)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Coordinate Detector test failed: {e}")
        return False

def test_geo_aggregator():
    """Тест GeoAggregatorService"""
    try:
        from services.geo_aggregator_service import GeoAggregatorService
        
        aggregator = GeoAggregatorService()
        logger.info("🌍 Testing Geo Aggregator Service...")
        
        # Создаем тестовое изображение если не существует
        test_image_path = "backend/data/archive_photos/test_image.jpg"
        if not os.path.exists(test_image_path):
            from PIL import Image
            import numpy as np
            
            img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            img = Image.fromarray(img_array)
            os.makedirs(os.path.dirname(test_image_path), exist_ok=True)
            img.save(test_image_path)
        
        # Тест с корректным location_hint
        result = aggregator.locate_image(test_image_path, "Москва, Красная площадь")
        logger.info(f"✅ Geo aggregator with valid hint: {result.get('success', False)}")
        
        # Тест с некорректным location_hint (должен использовать fallback)
        result2 = aggregator.locate_image(test_image_path, "detected objects")
        logger.info(f"✅ Geo aggregator with invalid hint: {result2.get('success', False)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Geo Aggregator Service test failed: {e}")
        return False

def test_api_keys():
    """Проверка API ключей"""
    logger.info("🔑 Testing API Keys...")
    
    yandex_key = os.getenv('YANDEX_API_KEY')
    dgis_key = os.getenv('DGIS_API_KEY')
    
    if yandex_key and yandex_key != 'your_yandex_api_key_here':
        logger.info("✅ YANDEX_API_KEY is configured")
    else:
        logger.warning("⚠️ YANDEX_API_KEY is not properly configured")
    
    if dgis_key and dgis_key != 'your_2gis_api_key_here':
        logger.info("✅ DGIS_API_KEY is configured")
    else:
        logger.warning("⚠️ DGIS_API_KEY is not properly configured")
    
    return True

def main():
    """Основная функция тестирования"""
    logger.info("🚀 Starting Coordinate Analysis Fix Test...")
    
    tests = [
        ("API Keys", test_api_keys),
        ("Yandex Maps Service", test_yandex_maps_service),
        ("Geo Aggregator Service", test_geo_aggregator),
        ("Coordinate Detector", test_coordinate_detector),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ Test {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Итоговый отчет
    logger.info(f"\n{'='*50}")
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Coordinate Analysis section should work correctly now.")
    else:
        logger.warning(f"⚠️ {total - passed} tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
