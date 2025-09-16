#!/usr/bin/env python3
"""
Тестирование и улучшение системы координатного распознавания
Анализ точности, уверенности и объектов
"""

import os
import sys
import requests
import json
from pathlib import Path

def test_coordinate_accuracy():
    """Тестирует точность координатного распознавания"""
    print("🎯 АНАЛИЗ ТОЧНОСТИ КООРДИНАТНОГО РАСПОЗНАВАНИЯ")
    print("=" * 60)
    
    # Найдем все тестовые изображения
    test_images = []
    upload_dirs = [
        "backend/uploads/coordinates",
        "backend/data/archive_photos",
        "test_image.jpg"
    ]
    
    for upload_dir in upload_dirs:
        if os.path.exists(upload_dir):
            if os.path.isfile(upload_dir):
                test_images.append(upload_dir)
            else:
                for file in os.listdir(upload_dir):
                    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        test_images.append(os.path.join(upload_dir, file))
    
    if not test_images:
        print("❌ Тестовые изображения не найдены")
        return False
    
    print(f"📁 Найдено изображений для тестирования: {len(test_images)}")
    
    results = []
    url = "http://localhost:5001/api/coordinates/detect"
    
    for i, image_path in enumerate(test_images[:3]):  # Тестируем первые 3
        print(f"\n🖼️ Тестирование изображения {i+1}: {os.path.basename(image_path)}")
        
        try:
            with open(image_path, 'rb') as f:
                files = {'file': f}
                data = {'location_hint': 'Москва, Россия'}
                
                response = requests.post(url, files=files, data=data, timeout=30)
                
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    data = result.get('data', {})
                    coordinates = data.get('coordinates', {})
                    objects = data.get('objects', [])
                    
                    analysis = {
                        'image': os.path.basename(image_path),
                        'coordinates_found': bool(coordinates),
                        'latitude': coordinates.get('latitude'),
                        'longitude': coordinates.get('longitude'),
                        'confidence': coordinates.get('confidence', 0),
                        'objects_count': len(objects),
                        'objects': [obj.get('category') for obj in objects[:5]]
                    }
                    
                    results.append(analysis)
                    
                    print(f"   📍 Координаты: {coordinates.get('latitude')}, {coordinates.get('longitude')}")
                    print(f"   🎯 Уверенность: {coordinates.get('confidence', 0):.3f}")
                    print(f"   🔍 Объектов: {len(objects)}")
                    
                    if objects:
                        print("   📦 Объекты:")
                        for obj in objects[:3]:
                            print(f"      - {obj.get('category', 'неизвестно')}: {obj.get('confidence', 0):.2f}")
                else:
                    print(f"   ❌ Ошибка: {result.get('error', 'неизвестная ошибка')}")
            else:
                print(f"   ❌ HTTP ошибка: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Исключение: {e}")
    
    # Анализ результатов
    print(f"\n📊 АНАЛИЗ РЕЗУЛЬТАТОВ:")
    print("=" * 40)
    
    if results:
        coords_found = sum(1 for r in results if r['coordinates_found'])
        avg_confidence = sum(r['confidence'] for r in results if r['confidence']) / len(results) if results else 0
        total_objects = sum(r['objects_count'] for r in results)
        
        print(f"✅ Координаты найдены: {coords_found}/{len(results)} ({coords_found/len(results)*100:.1f}%)")
        print(f"📈 Средняя уверенность: {avg_confidence:.3f}")
        print(f"🎯 Всего объектов обнаружено: {total_objects}")
        
        # Рекомендации по улучшению
        print(f"\n💡 РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:")
        
        if avg_confidence < 0.5:
            print("⚠️ Низкая уверенность - нужно улучшить алгоритмы")
        
        if total_objects == 0:
            print("⚠️ Объекты не обнаруживаются - проверить YOLO модель")
        
        if coords_found < len(results):
            print("⚠️ Не все координаты найдены - улучшить fallback методы")
    
    return len(results) > 0

def test_batch_processing():
    """Тестирует пакетную обработку"""
    print("\n📦 ТЕСТИРОВАНИЕ ПАКЕТНОЙ ОБРАБОТКИ")
    print("=" * 50)
    
    # Найдем несколько изображений
    test_images = []
    upload_dirs = ["backend/uploads/coordinates", "backend/data/archive_photos"]
    
    for upload_dir in upload_dirs:
        if os.path.exists(upload_dir):
            for file in os.listdir(upload_dir):
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    test_images.append(os.path.join(upload_dir, file))
                    if len(test_images) >= 2:  # Максимум 2 изображения для теста
                        break
        if len(test_images) >= 2:
            break
    
    if len(test_images) < 2:
        print("❌ Недостаточно изображений для пакетного тестирования")
        return False
    
    print(f"📁 Тестируем пакетную обработку {len(test_images)} изображений")
    
    url = "http://localhost:5001/api/coordinates/batch"
    
    try:
        files = []
        for i, image_path in enumerate(test_images):
            files.append(('images', (f'image_{i}.jpg', open(image_path, 'rb'), 'image/jpeg')))
        
        data = {'location_hints': 'Москва, Россия'}
        
        response = requests.post(url, files=files, data=data, timeout=60)
        
        # Закрываем файлы
        for _, file_tuple in files:
            file_tuple[1].close()
        
        print(f"📊 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                processed = result.get('processed', 0)
                saved = result.get('saved', 0)
                results = result.get('results', [])
                
                print(f"✅ Обработано: {processed} изображений")
                print(f"💾 Сохранено: {saved} результатов")
                print(f"📊 Результатов получено: {len(results)}")
                
                for i, res in enumerate(results):
                    coords = res.get('coordinates', {})
                    if coords:
                        print(f"   {i+1}. Координаты: {coords.get('latitude')}, {coords.get('longitude')}")
                
                return True
            else:
                print(f"❌ Ошибка: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            print(f"   Ответ: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False

def test_system_statistics():
    """Тестирует статистику системы"""
    print("\n📊 СТАТИСТИКА СИСТЕМЫ")
    print("=" * 30)
    
    url = "http://localhost:5001/api/coordinates/statistics"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                stats = result.get('data', {})
                
                # Системная информация
                system_info = stats.get('system_info', {})
                print(f"🔧 Система: {system_info.get('name', 'Geo Locator')}")
                print(f"📋 Версия: {system_info.get('version', '1.0')}")
                
                # Возможности
                capabilities = stats.get('capabilities', {})
                print(f"\n🎯 ВОЗМОЖНОСТИ СИСТЕМЫ:")
                for capability, enabled in capabilities.items():
                    status = "✅" if enabled else "❌"
                    print(f"   {status} {capability}")
                
                # Статистика базы данных
                db_stats = stats.get('database_stats', {})
                if db_stats:
                    print(f"\n💾 БАЗА ДАННЫХ:")
                    print(f"   📸 Фото: {db_stats.get('total_photos', 0)}")
                    print(f"   🚨 Нарушения: {db_stats.get('total_detections', 0)}")
                
                return True
            else:
                print(f"❌ Ошибка: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ ГЕОЛОКАЦИИ")
    print("=" * 70)
    
    tests = [
        ("Точность координат", test_coordinate_accuracy),
        ("Пакетная обработка", test_batch_processing),
        ("Статистика системы", test_system_statistics)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Запуск теста: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print("\n" + "=" * 70)
    print("📋 ИТОГОВЫЙ ОТЧЕТ:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Результат: {passed}/{len(results)} тестов пройдено")
    
    if passed == len(results):
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к использованию.")
    else:
        print("⚠️ Требуется доработка системы.")
        
        # Рекомендации
        print(f"\n💡 СЛЕДУЮЩИЕ ШАГИ:")
        print("1. Проверить настройку API ключей")
        print("2. Улучшить алгоритмы уверенности")
        print("3. Настроить YOLO модель для объектов")
        print("4. Добавить больше источников данных")

if __name__ == "__main__":
    main()
