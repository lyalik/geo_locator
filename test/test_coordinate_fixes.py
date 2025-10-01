#!/usr/bin/env python3
"""
Тест исправлений в системе определения координат
"""

import requests
import json
import os
from pathlib import Path

# Настройки
BASE_URL = "http://localhost:5001"
TEST_IMAGE_PATH = "/home/denis/Documents/Hackathon_2025/geo_locator/backend/data/archive_photos"

def test_coordinate_detection():
    """Тест определения координат с улучшенной логикой"""
    
    # Найдем тестовое изображение
    test_images = []
    if os.path.exists(TEST_IMAGE_PATH):
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            test_images.extend(Path(TEST_IMAGE_PATH).glob(ext))
    
    if not test_images:
        print("❌ Нет тестовых изображений в архиве")
        return False
    
    test_image = str(test_images[0])
    print(f"📸 Тестируем с изображением: {os.path.basename(test_image)}")
    
    # Подготовка запроса
    url = f"{BASE_URL}/api/coordinates/detect"
    
    try:
        with open(test_image, 'rb') as f:
            files = {'image': f}
            data = {
                'location_hint': '',  # Пустая подсказка для тестирования улучшенной логики
                'user_description': 'Тестовое изображение здания'
            }
            
            print("🔄 Отправляем запрос на определение координат...")
            response = requests.post(url, files=files, data=data, timeout=30)
            
            print(f"📊 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Запрос выполнен успешно")
                
                # Анализ результата
                print(f"🎯 Успех: {result.get('success', False)}")
                print(f"📝 Сообщение: {result.get('message', 'Нет сообщения')}")
                
                if result.get('coordinates'):
                    coords = result['coordinates']
                    print(f"📍 Координаты: {coords.get('latitude', 'N/A')}, {coords.get('longitude', 'N/A')}")
                    print(f"🎯 Источник: {coords.get('source', 'N/A')}")
                    print(f"📊 Уверенность: {coords.get('confidence', 'N/A')}")
                else:
                    print("❌ Координаты не определены")
                
                # Проверка спутниковых данных
                if result.get('satellite_data'):
                    sat_data = result['satellite_data']
                    print(f"🛰️ Спутниковые данные: {sat_data.get('source', 'N/A')}")
                    if sat_data.get('image_url'):
                        print(f"🖼️ URL спутникового снимка: {sat_data['image_url'][:50]}...")
                
                # Проверка информации о местоположении
                if result.get('location_info'):
                    loc_info = result['location_info']
                    print("📍 Информация о местоположении:")
                    
                    if loc_info.get('yandex_address'):
                        ya_addr = loc_info['yandex_address']
                        print(f"  🗺️ Яндекс: {ya_addr.get('formatted_address', 'N/A')}")
                    
                    if loc_info.get('dgis_places'):
                        dgis_places = loc_info['dgis_places']
                        print(f"  🏢 2GIS: {len(dgis_places)} мест найдено")
                
                # Проверка рекомендаций
                if result.get('recommendations'):
                    print("💡 Рекомендации:")
                    for rec in result['recommendations'][:3]:
                        print(f"  - {rec}")
                
                return True
                
            else:
                print(f"❌ Ошибка запроса: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"📝 Детали ошибки: {error_data}")
                except:
                    print(f"📝 Текст ошибки: {response.text}")
                return False
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_api_health():
    """Проверка работоспособности API"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API работает")
            return True
        else:
            print(f"❌ API недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ СИСТЕМЫ КООРДИНАТ")
    print("=" * 50)
    
    # Проверка API
    if not test_api_health():
        print("❌ Тестирование прервано - API недоступен")
        return
    
    print()
    
    # Тест определения координат
    success = test_coordinate_detection()
    
    print()
    print("=" * 50)
    if success:
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
    else:
        print("❌ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ")

if __name__ == "__main__":
    main()
