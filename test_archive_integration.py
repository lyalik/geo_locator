#!/usr/bin/env python3
"""
Тестирование интеграции архивного датасета
"""
import os
import sys
import json
import logging

# Добавляем путь к backend
sys.path.append('/home/denis/Documents/Hackathon_2025/geo_locator/backend')

from services.archive_photo_service import ArchivePhotoService
from services.coordinate_detector import CoordinateDetector
from services.google_vision_service import GoogleVisionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_archive_service():
    """Тестирует ArchivePhotoService"""
    print("🏛️ Тестирование ArchivePhotoService...")
    
    try:
        service = ArchivePhotoService()
        
        # Получаем статистику
        stats = service.get_archive_statistics()
        print(f"📊 Статистика архива: {stats}")
        
        # Тестируем поиск по тестовому изображению
        test_image = '/home/denis/Documents/Hackathon_2025/geo_locator/backend/data/archive_photos/buildings/sample_building_001.jpg'
        
        if os.path.exists(test_image):
            similar = service.find_similar_buildings(test_image, threshold=0.3)
            print(f"🔍 Найдено похожих зданий: {len(similar)}")
            
            for building in similar[:2]:
                print(f"  - {building['metadata']['description']} (схожесть: {building['similarity']:.3f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в ArchivePhotoService: {e}")
        return False

def test_coordinate_detector_integration():
    """Тестирует интеграцию в coordinate_detector"""
    print("\n🎯 Тестирование интеграции в CoordinateDetector...")
    
    try:
        detector = CoordinateDetector()
        
        # Тестируем с архивным изображением
        test_image = '/home/denis/Documents/Hackathon_2025/geo_locator/backend/data/archive_photos/buildings/sample_building_001.jpg'
        
        if os.path.exists(test_image):
            result = detector.detect_coordinates_from_image(test_image)
            
            print(f"📍 Результат определения координат:")
            print(f"  - Успех: {result.get('success', False)}")
            
            if result.get('coordinates'):
                coords = result['coordinates']
                print(f"  - Координаты: {coords.get('latitude')}, {coords.get('longitude')}")
                print(f"  - Источник: {coords.get('source', 'unknown')}")
            
            # Проверяем источники координат
            sources = result.get('coordinate_sources', {})
            print(f"  - Архивное совпадение: {sources.get('archive_photo_match', False)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в CoordinateDetector: {e}")
        return False

def test_google_vision_integration():
    """Тестирует интеграцию в GoogleVisionService"""
    print("\n🤖 Тестирование интеграции в GoogleVisionService...")
    
    try:
        service = GoogleVisionService()
        
        # Проверяем наличие архивного сервиса
        has_archive = hasattr(service, 'archive_service') and service.archive_service is not None
        print(f"🏛️ Архивный сервис доступен: {has_archive}")
        
        if has_archive:
            test_image = '/home/denis/Documents/Hackathon_2025/geo_locator/backend/data/archive_photos/buildings/sample_building_001.jpg'
            
            if os.path.exists(test_image):
                # Тестируем анализ с архивным контекстом
                result = service.analyze_violations_with_archive_context(test_image)
                
                print(f"📋 Результат анализа с архивным контекстом:")
                print(f"  - Успех: {result.get('success', False)}")
                print(f"  - Найдено похожих зданий: {len(result.get('similar_buildings', []))}")
                
                if result.get('archive_context'):
                    context = result['archive_context']
                    print(f"  - Типы зданий: {context.get('building_types', [])}")
                    print(f"  - Архитектурные стили: {context.get('architectural_styles', [])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в GoogleVisionService: {e}")
        return False

def test_metadata_loading():
    """Тестирует загрузку метаданных"""
    print("\n📄 Тестирование загрузки метаданных...")
    
    metadata_path = '/home/denis/Documents/Hackathon_2025/geo_locator/backend/data/archive_photos/metadata'
    
    try:
        metadata_files = [f for f in os.listdir(metadata_path) if f.endswith('.json')]
        print(f"📁 Найдено файлов метаданных: {len(metadata_files)}")
        
        for file in metadata_files:
            file_path = os.path.join(metadata_path, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"  - {file}: {data.get('description', 'Без описания')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка загрузки метаданных: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ АРХИВНОГО ДАТАСЕТА")
    print("=" * 50)
    
    tests = [
        ("Метаданные", test_metadata_loading),
        ("ArchivePhotoService", test_archive_service),
        ("CoordinateDetector", test_coordinate_detector_integration),
        ("GoogleVisionService", test_google_vision_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"  {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Итого: {passed}/{len(results)} тестов пройдено")
    
    if passed == len(results):
        print("🎉 Все тесты пройдены успешно!")
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте логи выше.")

if __name__ == "__main__":
    main()
