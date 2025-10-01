#!/usr/bin/env python3
"""
Тест для проверки работы раздела "Анализ координат"
"""
import requests
import json
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('.env')

BASE_URL = "http://localhost:5001"

def test_coordinate_detection():
    """Тестирование анализа координат"""
    print("🗺️ Тестирование раздела 'Анализ координат'")
    print("=" * 50)
    
    # Тест 1: Прямой вызов Yandex search_places через geo_aggregator
    print("\n1. Тест поиска мест через Yandex API:")
    
    try:
        # Имитируем запрос как в coordinate detection
        test_data = {
            'location_hint': 'достопримечательность',
            'user_description': None
        }
        
        response = requests.post(f"{BASE_URL}/api/geo/search/places", 
                               json=test_data,
                               timeout=30)
        
        print(f"   Запрос: {test_data['location_hint']}")
        print(f"   Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Успешно получен ответ")
            
            # Проверяем результаты Yandex
            if data.get('yandex'):
                yandex_success = data['yandex'].get('success', False)
                total_found = data['yandex'].get('total_found', 0)
                print(f"   📍 Yandex Maps: {'✅ Работает' if yandex_success else '❌ Ошибка'}")
                print(f"   📊 Найдено мест: {total_found}")
                
                if not yandex_success:
                    error = data['yandex'].get('error', 'Unknown error')
                    print(f"      Ошибка: {error}")
            
            # Проверяем результаты 2GIS
            if data.get('dgis'):
                dgis_success = data['dgis'].get('success', False)
                print(f"   🗺️  2GIS: {'✅ Работает' if dgis_success else '❌ Ошибка'}")
        else:
            print(f"   ❌ Ошибка HTTP: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Ошибка запроса: {e}")

def test_coordinate_detection_with_image():
    """Тест coordinate detection с изображением"""
    print("\n2. Тест анализа координат с изображением:")
    
    # Проверяем наличие тестового изображения
    test_image_path = "/home/denis/Documents/Hackathon_2025/geo_locator/backend/uploads/coordinates/1krasn_pl2-3797155958.jpg"
    
    if not os.path.exists(test_image_path):
        print("   ⚠️  Тестовое изображение не найдено, создаем mock запрос")
        
        # Mock данные для тестирования
        mock_data = {
            'location_hint': None,
            'user_description': 'тест'
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/coordinates/detect",
                                   json=mock_data,
                                   timeout=30)
            
            print(f"   Статус: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ API endpoint доступен")
                print(f"   📊 Результат: {data.get('success', 'unknown')}")
                print(f"   📝 Сообщение: {data.get('message', 'no message')}")
            else:
                print(f"   ❌ Ошибка HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка запроса: {e}")
    else:
        print(f"   📁 Найдено тестовое изображение: {test_image_path}")

def test_yandex_service_directly():
    """Прямой тест Yandex сервиса"""
    print("\n3. Прямой тест Yandex Maps сервиса:")
    
    try:
        # Тестируем новый исправленный метод search_places
        from backend.services.yandex_maps_service import YandexMapsService
        
        yandex_service = YandexMapsService()
        result = yandex_service.search_places("достопримечательность")
        
        print(f"   ✅ Сервис инициализирован")
        print(f"   📍 Результат: {'✅ Успешно' if result.get('success') else '❌ Ошибка'}")
        
        if result.get('success'):
            print(f"   📊 Найдено мест: {result.get('total_found', 0)}")
            places = result.get('places', [])
            if places:
                print(f"   🏛️  Первое место: {places[0].get('name', 'Без названия')}")
        else:
            print(f"   ❌ Ошибка: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Ошибка импорта/выполнения: {e}")

if __name__ == "__main__":
    print("🧪 ТЕСТИРОВАНИЕ АНАЛИЗА КООРДИНАТ")
    print("=" * 50)
    
    test_yandex_service_directly()
    test_coordinate_detection()
    test_coordinate_detection_with_image()
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено")
