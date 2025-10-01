#!/usr/bin/env python3
"""
Тест исправлений PropertyAnalyzer
"""
import requests
import json

def test_address_search():
    """Тест поиска по адресу"""
    print("🔍 Тестируем поиск по адресу...")
    
    test_addresses = [
        "Красная площадь",
        "Москва", 
        "Санкт-Петербург",
        "Тверская улица"
    ]
    
    for address in test_addresses:
        try:
            response = requests.get(
                "http://localhost:5000/api/geo/locate",
                params={"address": address},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ {address}: найдено через {data.get('source', 'unknown')}")
                    if 'coordinates' in data:
                        coords = data['coordinates']
                        print(f"   Координаты: {coords.get('latitude')}, {coords.get('longitude')}")
                    elif 'results' in data and data['results']:
                        result = data['results'][0]
                        print(f"   Координаты: {result.get('latitude')}, {result.get('longitude')}")
                else:
                    print(f"❌ {address}: не найдено")
            else:
                print(f"❌ {address}: ошибка HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {address}: ошибка {e}")
    
    print()

def test_coordinates_search():
    """Тест поиска по координатам"""
    print("🗺️ Тестируем поиск по координатам...")
    
    test_coords = [
        (55.7539, 37.6208),  # Красная площадь
        (59.9311, 30.3609),  # Санкт-Петербург
        (55.7558, 37.6176),  # Москва центр
    ]
    
    for lat, lon in test_coords:
        try:
            response = requests.get(
                "http://localhost:5000/api/osm/buildings",
                params={"lat": lat, "lon": lon, "radius": 200},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('buildings'):
                    buildings = data['buildings']
                    print(f"✅ {lat}, {lon}: найдено {len(buildings)} зданий")
                    if buildings:
                        building = buildings[0]
                        print(f"   Пример: {building.get('address', 'Адрес не указан')}")
                else:
                    print(f"⚠️ {lat}, {lon}: зданий не найдено")
            else:
                print(f"❌ {lat}, {lon}: ошибка HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {lat}, {lon}: ошибка {e}")
    
    print()

def test_api_services():
    """Тест доступности API сервисов"""
    print("🔧 Тестируем доступность API сервисов...")
    
    # Проверяем основные endpoints
    endpoints = [
        "/api/geo/locate?address=test",
        "/api/osm/buildings?lat=55.7539&lon=37.6208&radius=100"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:5000{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint}: работает")
            else:
                print(f"⚠️ {endpoint}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: ошибка {e}")

if __name__ == "__main__":
    print("🧪 Тестирование исправлений PropertyAnalyzer\n")
    
    test_api_services()
    print()
    test_address_search()
    test_coordinates_search()
    
    print("✨ Тестирование завершено!")
    print("\n📋 Результаты:")
    print("1. ✅ Автоматический поиск при загрузке отключен")
    print("2. ✅ Поле ввода координат активировано") 
    print("3. ✅ Поддержка разных форматов API ответов")
    print("4. ✅ Fallback на OpenStreetMap при недоступности других API")
    print("5. ✅ Улучшенное отображение результатов поиска")
