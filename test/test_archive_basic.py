#!/usr/bin/env python3
"""
Базовое тестирование архивного сервиса без Google API
"""
import os
import sys
import json
import logging

# Добавляем путь к backend
sys.path.append('/home/denis/Documents/Hackathon_2025/geo_locator/backend')

from services.archive_photo_service import ArchivePhotoService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_archive_service_basic():
    """Базовое тестирование ArchivePhotoService"""
    print("🏛️ Тестирование ArchivePhotoService...")
    
    try:
        service = ArchivePhotoService()
        
        # Получаем статистику
        stats = service.get_archive_statistics()
        print(f"📊 Статистика архива:")
        print(f"  - Всего фото: {stats.get('total_photos', 0)}")
        print(f"  - По типам: {stats.get('by_type', {})}")
        print(f"  - По стилям: {stats.get('by_style', {})}")
        
        # Проверяем загрузку метаданных
        metadata_count = len(service.metadata_cache)
        print(f"  - Загружено метаданных: {metadata_count}")
        
        # Тестируем поиск по тестовому изображению
        test_image = '/home/denis/Documents/Hackathon_2025/geo_locator/backend/data/archive_photos/buildings/sample_building_001.jpg'
        
        if os.path.exists(test_image):
            print(f"\n🔍 Тестирование поиска похожих зданий...")
            similar = service.find_similar_buildings(test_image, threshold=0.1)
            print(f"  - Найдено похожих зданий: {len(similar)}")
            
            for i, building in enumerate(similar[:3]):
                metadata = building.get('metadata', {})
                similarity = building.get('similarity', 0)
                description = metadata.get('description', 'Без описания')
                print(f"  - #{i+1}: {description} (схожесть: {similarity:.3f})")
        else:
            print(f"⚠️ Тестовое изображение не найдено: {test_image}")
        
        # Тестируем получение координат
        print(f"\n📍 Тестирование получения координат...")
        if os.path.exists(test_image):
            coords = service.get_coordinates_from_similar_buildings(test_image, threshold=0.1)
            if coords:
                print(f"  - Координаты найдены: {coords.get('latitude')}, {coords.get('longitude')}")
                print(f"  - Источник: {coords.get('matched_building', {}).get('description', 'Неизвестно')}")
            else:
                print(f"  - Координаты не найдены")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в ArchivePhotoService: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metadata_files():
    """Тестирует файлы метаданных"""
    print("\n📄 Проверка файлов метаданных...")
    
    metadata_path = '/home/denis/Documents/Hackathon_2025/geo_locator/backend/data/archive_photos/metadata'
    
    try:
        if not os.path.exists(metadata_path):
            print(f"❌ Папка метаданных не существует: {metadata_path}")
            return False
            
        metadata_files = [f for f in os.listdir(metadata_path) if f.endswith('.json')]
        print(f"📁 Найдено файлов метаданных: {len(metadata_files)}")
        
        for file in metadata_files:
            file_path = os.path.join(metadata_path, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    description = data.get('description', 'Без описания')
                    coords = data.get('coordinates', {})
                    lat = coords.get('latitude', 'N/A')
                    lon = coords.get('longitude', 'N/A')
                    print(f"  - {file}: {description} ({lat}, {lon})")
            except Exception as e:
                print(f"  - ❌ Ошибка в {file}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки метаданных: {e}")
        return False

def test_image_files():
    """Проверяет наличие файлов изображений"""
    print("\n🖼️ Проверка файлов изображений...")
    
    base_path = '/home/denis/Documents/Hackathon_2025/geo_locator/backend/data/archive_photos'
    
    folders = ['buildings', 'landmarks', 'streets']
    total_images = 0
    
    for folder in folders:
        folder_path = os.path.join(base_path, folder)
        if os.path.exists(folder_path):
            images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            print(f"  - {folder}: {len(images)} изображений")
            total_images += len(images)
            
            for img in images[:3]:  # Показываем первые 3
                img_path = os.path.join(folder_path, img)
                size = os.path.getsize(img_path)
                print(f"    * {img} ({size} байт)")
        else:
            print(f"  - {folder}: папка не существует")
    
    print(f"📊 Всего изображений: {total_images}")
    return total_images > 0

def main():
    """Основная функция тестирования"""
    print("🧪 БАЗОВОЕ ТЕСТИРОВАНИЕ АРХИВНОГО ДАТАСЕТА")
    print("=" * 50)
    
    tests = [
        ("Файлы метаданных", test_metadata_files),
        ("Файлы изображений", test_image_files),
        ("ArchivePhotoService", test_archive_service_basic)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print()
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
        print("\n📋 Архивный датасет готов к использованию:")
        print("  - Загружайте фото в раздел 'Анализ координат' для определения местоположения")
        print("  - Загружайте фото в раздел 'Анализ ИИ' для улучшенного анализа нарушений")
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте логи выше.")

if __name__ == "__main__":
    main()
