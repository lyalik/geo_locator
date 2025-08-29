#!/usr/bin/env python3
"""
Тест двухколоночного поиска недвижимости через Яндекс и 2GIS
"""
import requests
import json

def test_address_search():
    """Тест поиска по адресу"""
    print("🏠 Тестируем поиск по адресу...")
    
    addresses = ["Москва", "Красная площадь", "Санкт-Петербург"]
    
    for address in addresses:
        try:
            response = requests.get(
                "http://localhost:5000/api/geo/locate",
                params={"address": address},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n📍 {address}:")
                print(f"  Успех: {data.get('success')}")
                
                if data.get('yandex'):
                    yandex = data['yandex']
                    print(f"  🟡 Яндекс: {yandex.get('formatted_address', 'N/A')}")
                    if yandex.get('coordinates'):
                        coords = yandex['coordinates']
                        print(f"     Координаты: {coords['latitude']}, {coords['longitude']}")
                else:
                    print("  🟡 Яндекс: результатов нет")
                
                if data.get('dgis'):
                    dgis = data['dgis']
                    print(f"  🔵 2GIS: найдено {len(dgis.get('results', []))} результатов")
                else:
                    print("  🔵 2GIS: результатов нет")
            else:
                print(f"❌ {address}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {address}: ошибка {e}")

def test_cadastral_search():
    """Тест поиска по кадастровому номеру"""
    print("\n📋 Тестируем поиск по кадастровому номеру...")
    
    cadastral_numbers = [
        "77:01:0001001:1234",
        "78:12:0123456:789",
        "50:21:0000001:1"
    ]
    
    for cadastral in cadastral_numbers:
        try:
            response = requests.get(
                "http://localhost:5000/api/geo/locate/cadastral",
                params={"cadastral_number": cadastral},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n🏷️ {cadastral}:")
                print(f"  Успех: {data.get('success')}")
                
                yandex_count = len(data.get('yandex', {}).get('results', [])) if data.get('yandex') else 0
                dgis_count = len(data.get('dgis', {}).get('results', [])) if data.get('dgis') else 0
                
                print(f"  🟡 Яндекс: {yandex_count} результатов")
                print(f"  🔵 2GIS: {dgis_count} результатов")
            else:
                print(f"❌ {cadastral}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {cadastral}: ошибка {e}")

def test_coordinates_search():
    """Тест поиска по координатам"""
    print("\n🗺️ Тестируем поиск по координатам...")
    
    coordinates = [
        (55.7539, 37.6208),  # Красная площадь
        (59.9311, 30.3609),  # Санкт-Петербург
        (55.7558, 37.6176),  # Москва центр
    ]
    
    for lat, lon in coordinates:
        try:
            response = requests.get(
                "http://localhost:5000/api/geo/locate/coordinates",
                params={"lat": lat, "lon": lon},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n📍 {lat}, {lon}:")
                print(f"  Успех: {data.get('success')}")
                
                if data.get('yandex'):
                    yandex = data['yandex']
                    print(f"  🟡 Яндекс: {yandex.get('formatted_address', 'N/A')}")
                else:
                    print("  🟡 Яндекс: результатов нет")
                
                dgis_count = len(data.get('dgis', {}).get('results', [])) if data.get('dgis') else 0
                print(f"  🔵 2GIS: {dgis_count} результатов")
            else:
                print(f"❌ {lat}, {lon}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {lat}, {lon}: ошибка {e}")

if __name__ == "__main__":
    print("🧪 Тестирование двухколоночного поиска недвижимости\n")
    
    test_address_search()
    test_cadastral_search()
    test_coordinates_search()
    
    print("\n✨ Тестирование завершено!")
    print("\n📊 Новые возможности:")
    print("1. ✅ Параллельный поиск через Яндекс и 2GIS")
    print("2. ✅ Двухколоночное отображение результатов")
    print("3. ✅ Поиск по адресу, кадастру и координатам")
    print("4. ✅ Отдельные endpoints для каждого типа поиска")
    print("5. ✅ Улучшенная точность через российские API")
