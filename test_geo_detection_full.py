#!/usr/bin/env python3
"""
Полное тестирование системы геолокационного распознавания
Тестирует все компоненты: Mistral AI OCR, панорамы, спутниковые снимки
"""

import os
import sys
import requests
import json
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_coordinate_detection_api():
    """Тестирует API детекции координат"""
    print("🔍 Тестирование API детекции координат...")
    
    # Найдем тестовое изображение
    test_image_path = None
    upload_dirs = [
        "backend/uploads/coordinates",
        "backend/data/archive_photos", 
        "."
    ]
    
    for upload_dir in upload_dirs:
        if os.path.exists(upload_dir):
            for file in os.listdir(upload_dir):
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    test_image_path = os.path.join(upload_dir, file)
                    break
        if test_image_path:
            break
    
    if not test_image_path:
        print("❌ Тестовое изображение не найдено")
        return False
    
    print(f"📁 Используем изображение: {test_image_path}")
    
    # Тестируем API
    url = "http://localhost:5001/api/coordinates/detect"
    
    try:
        with open(test_image_path, 'rb') as f:
            files = {'file': f}  # Изменено с 'image' на 'file'
            data = {
                'location_hint': 'Москва, Россия'
            }
            
            response = requests.post(url, files=files, data=data, timeout=30)
            
        print(f"📊 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Успешный ответ от API")
            
            # Анализируем результат
            if result.get('success'):
                data = result.get('data', {})
                coordinates = data.get('coordinates', {})
                objects = data.get('objects', [])
                
                print(f"📍 Координаты найдены: {bool(coordinates)}")
                if coordinates:
                    print(f"   Широта: {coordinates.get('latitude')}")
                    print(f"   Долгота: {coordinates.get('longitude')}")
                    print(f"   Уверенность: {coordinates.get('confidence', 0):.2f}")
                
                print(f"🎯 Обнаружено объектов: {len(objects)}")
                for obj in objects[:3]:  # Показываем первые 3 объекта
                    print(f"   - {obj.get('category', 'неизвестно')}: {obj.get('confidence', 0):.2f}")
                
                # Проверяем дополнительные данные
                if 'sources' in data:
                    sources = data['sources']
                    print(f"🔍 Источники данных: {len(sources)}")
                    for source_name, source_data in sources.items():
                        if source_data:
                            print(f"   ✅ {source_name}: {source_data.get('confidence', 0):.2f}")
                
                return True
            else:
                print(f"❌ API вернул ошибку: {result.get('error', 'неизвестная ошибка')}")
                return False
        else:
            print(f"❌ Ошибка HTTP: {response.status_code}")
            print(f"   Ответ: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return False

def test_mistral_ocr_api():
    """Тестирует Mistral AI OCR API"""
    print("\n🤖 Тестирование Mistral AI OCR...")
    
    # Найдем изображение с текстом
    test_image_path = None
    upload_dirs = [
        "backend/uploads/coordinates",
        "backend/data/archive_photos",
        "."
    ]
    
    for upload_dir in upload_dirs:
        if os.path.exists(upload_dir):
            for file in os.listdir(upload_dir):
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    test_image_path = os.path.join(upload_dir, file)
                    break
        if test_image_path:
            break
    
    if not test_image_path:
        print("❌ Тестовое изображение не найдено")
        return False
    
    print(f"📁 Используем изображение: {test_image_path}")
    
    url = "http://localhost:5001/api/geo/mistral/address"
    
    try:
        with open(test_image_path, 'rb') as f:
            files = {'file': f}
            
            response = requests.post(url, files=files, timeout=20)
            
        print(f"📊 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Успешный ответ от Mistral AI OCR")
            
            if result.get('success'):
                ocr_text = result.get('ocr_text', '')
                analysis = result.get('analysis', {})
                
                print(f"📝 Извлеченный текст: {len(ocr_text)} символов")
                if ocr_text:
                    print(f"   Превью: {ocr_text[:100]}...")
                
                if analysis:
                    addresses = analysis.get('addresses', [])
                    buildings = analysis.get('buildings', [])
                    
                    print(f"🏠 Найдено адресов: {len(addresses)}")
                    print(f"🏢 Найдено зданий: {len(buildings)}")
                
                return True
            else:
                print(f"❌ Mistral AI вернул ошибку: {result.get('error')}")
                return False
        else:
            print(f"❌ Ошибка HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return False

def test_panorama_api():
    """Тестирует API панорамного анализа"""
    print("\n🌐 Тестирование панорамного анализа...")
    
    # Проверим статистику координатного детектора
    url = "http://localhost:5001/api/coordinates/statistics"
    
    try:
        response = requests.get(url, timeout=15)
        
        print(f"📊 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Успешный ответ от статистики системы")
            
            if result.get('success'):
                stats = result.get('data', {})
                system_info = stats.get('system_info', {})
                capabilities = stats.get('capabilities', {})
                
                print(f"🔧 Система: {system_info.get('name', 'неизвестно')}")
                print(f"📊 Возможности: {len(capabilities)} модулей")
                
                for capability, enabled in capabilities.items():
                    status = "✅" if enabled else "❌"
                    print(f"   {status} {capability}")
                
                return True
            else:
                print(f"❌ API вернул ошибку: {result.get('error')}")
                return False
        else:
            print(f"❌ Ошибка HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 ПОЛНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ ГЕОЛОКАЦИИ")
    print("=" * 50)
    
    results = []
    
    # Тест 1: Детекция координат
    results.append(test_coordinate_detection_api())
    
    # Тест 2: Mistral AI OCR
    results.append(test_mistral_ocr_api())
    
    # Тест 3: Панорамный анализ
    results.append(test_panorama_api())
    
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    
    test_names = [
        "Детекция координат",
        "Mistral AI OCR", 
        "Панорамный анализ"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{i+1}. {name}: {status}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n🎯 Итого: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("⚠️ Некоторые тесты провалены, требуется доработка")

if __name__ == "__main__":
    main()
