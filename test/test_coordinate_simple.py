#!/usr/bin/env python3
"""
Простой тест для проверки API определения координат
"""

import requests
import json
import os
from PIL import Image
import io

def create_simple_test_image():
    """Создает простое тестовое изображение"""
    img = Image.new('RGB', (400, 300), color='red')
    test_image_path = '/tmp/simple_test_image.jpg'
    img.save(test_image_path, 'JPEG')
    return test_image_path

def test_coordinate_api():
    """Тестирует API определения координат"""
    print("🧪 Тестирование API /api/coordinate/detect...")
    
    image_path = create_simple_test_image()
    url = 'http://localhost:5001/api/coordinates/detect'
    
    with open(image_path, 'rb') as f:
        files = {'image': ('test.jpg', f, 'image/jpeg')}
        data = {'location_hint': 'Москва'}
        
        try:
            response = requests.post(url, files=files, data=data, timeout=15)
            
            print(f"📡 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ API работает!")
                
                # Проверяем структуру ответа
                if 'coordinates' in result:
                    coords = result['coordinates']
                    print(f"📍 Координаты: {coords}")
                
                if 'satellite_data' in result:
                    print(f"🛰️ Спутниковые данные: {result['satellite_data']}")
                
                if 'location_info' in result:
                    print(f"📍 Информация о местоположении: {result['location_info']}")
                
                if 'detected_objects' in result:
                    print(f"🎯 Обнаруженные объекты: {len(result.get('detected_objects', []))}")
                
            else:
                print(f"❌ Ошибка: {response.text}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    # Удаляем тестовый файл
    if os.path.exists(image_path):
        os.remove(image_path)

def check_backend_health():
    """Проверяет работу backend"""
    print("🏥 Проверка здоровья backend...")
    
    try:
        response = requests.get('http://localhost:5001/health', timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Backend работает: {health}")
            return True
        else:
            print(f"❌ Backend недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка соединения с backend: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Простой тест раздела 'Анализ координат'")
    print("=" * 50)
    
    if check_backend_health():
        print()
        test_coordinate_api()
    
    print("\n🎯 Тест завершен!")
    print("Для полного тестирования:")
    print("1. Настройте API ключи в файле .env")
    print("2. Откройте http://localhost:3000")
    print("3. Перейдите в 'Анализ координат'")
    print("4. Загрузите изображение и проверьте новые секции")
