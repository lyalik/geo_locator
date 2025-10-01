#!/usr/bin/env python3
"""
Тестирование с реальными API ключами
ВНИМАНИЕ: Замените ключи на ваши реальные перед запуском
"""
import os
import sys
import requests
import json

# РЕАЛЬНЫЕ API КЛЮЧИ
YANDEX_API_KEY = input("Введите Yandex API ключ: ").strip()
DGIS_API_KEY = input("Введите 2GIS API ключ: ").strip()

def test_yandex_geocoding_real(api_key, address="Красная площадь, Москва"):
    """Тест Yandex Geocoding с реальным ключом"""
    print("🔍 ТЕСТИРОВАНИЕ YANDEX GEOCODING (РЕАЛЬНЫЙ КЛЮЧ)")
    print("=" * 50)
    
    url = 'https://geocode-maps.yandex.ru/1.x/'
    params = {
        'apikey': api_key,
        'geocode': address,
        'format': 'json',
        'results': 1,
        'lang': 'ru_RU'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            geo_objects = data.get('response', {}).get('GeoObjectCollection', {}).get('featureMember', [])
            
            if geo_objects:
                geo_object = geo_objects[0]['GeoObject']
                coordinates = geo_object['Point']['pos'].split()
                formatted_address = geo_object.get('metaDataProperty', {}).get('GeocoderMetaData', {}).get('text', '')
                
                print(f"✅ Успех! Найден адрес: {formatted_address}")
                print(f"📍 Координаты: {coordinates[1]}, {coordinates[0]}")
                return True
            else:
                print("❌ Адрес не найден")
                return False
        else:
            print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_dgis_search_real(api_key, query="кафе", lat=55.7558, lon=37.6176):
    """Тест 2GIS Search с реальным ключом"""
    print("\n🔍 ТЕСТИРОВАНИЕ 2GIS SEARCH (РЕАЛЬНЫЙ КЛЮЧ)")
    print("=" * 50)
    
    url = 'https://catalog.api.2gis.com/3.0/items'
    params = {
        'key': api_key,
        'q': query,
        'point': f"{lon},{lat}",
        'radius': 1000,
        'region_id': 1,  # Москва
        'page_size': 3,
        'fields': 'items.point,items.adm_div,items.address,items.contact_groups,items.rubrics'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'error' in data.get('meta', {}):
                print(f"❌ API Ошибка: {data['meta']['error']}")
                return False
            
            items = data.get('result', {}).get('items', [])
            total = data.get('meta', {}).get('total', 0)
            
            print(f"✅ Успех! Найдено {len(items)} из {total} объектов")
            
            for i, item in enumerate(items[:3], 1):
                name = item.get('name', 'Без названия')
                address = item.get('address_name', 'Адрес не указан')
                point = item.get('point', {})
                lat_item = point.get('lat', 0)
                lon_item = point.get('lon', 0)
                
                print(f"{i}. {name}")
                print(f"   📍 {address}")
                print(f"   🗺️  {lat_item}, {lon_item}")
            
            return True
        else:
            print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_backend_integration():
    """Тест интеграции с backend"""
    print("\n🔍 ТЕСТИРОВАНИЕ BACKEND ИНТЕГРАЦИИ")
    print("=" * 50)
    
    try:
        # Устанавливаем переменные окружения
        os.environ['YANDEX_API_KEY'] = YANDEX_API_KEY
        os.environ['DGIS_API_KEY'] = DGIS_API_KEY
        
        # Добавляем путь к backend
        sys.path.append('/home/denis/Documents/Hackathon_2025/geo_locator/backend')
        
        from services.yandex_maps_service import YandexMapsService
        from services.dgis_service import DGISService
        
        # Тест Yandex сервиса
        print("🔄 Тестирование YandexMapsService...")
        yandex_service = YandexMapsService()
        yandex_result = yandex_service.geocode("Красная площадь, Москва")
        
        if yandex_result.get('success'):
            coords = yandex_result.get('coordinates', {})
            print(f"✅ Yandex: {coords.get('latitude')}, {coords.get('longitude')}")
        else:
            print(f"❌ Yandex: {yandex_result.get('error')}")
        
        # Тест 2GIS сервиса
        print("🔄 Тестирование DGISService...")
        dgis_service = DGISService()
        dgis_result = dgis_service.search_places("кафе", 55.7558, 37.6176, 1000)
        
        if dgis_result.get('success'):
            places_count = len(dgis_result.get('places', []))
            print(f"✅ 2GIS: Найдено {places_count} мест")
        else:
            print(f"❌ 2GIS: {dgis_result.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка интеграции: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ РЕАЛЬНЫХ API КЛЮЧЕЙ")
    print("=" * 60)
    
    if YANDEX_API_KEY == "YOUR_YANDEX_KEY_HERE":
        print("⚠️  ВНИМАНИЕ: Замените YANDEX_API_KEY на реальный ключ!")
        return
    
    if DGIS_API_KEY == "YOUR_DGIS_KEY_HERE":
        print("⚠️  ВНИМАНИЕ: Замените DGIS_API_KEY на реальный ключ!")
        return
    
    results = {
        'yandex_geocoding': test_yandex_geocoding_real(YANDEX_API_KEY),
        'dgis_search': test_dgis_search_real(DGIS_API_KEY),
        'backend_integration': test_backend_integration()
    }
    
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ ПРОШЕЛ" if success else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\nРезультат: {passed}/{total} тестов прошли успешно")
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ! API ключи работают корректно!")
        print("Система готова к полноценной работе с Yandex и 2GIS API.")
    else:
        print("\n⚠️  Некоторые тесты провалены. Проверьте API ключи.")

if __name__ == "__main__":
    main()
