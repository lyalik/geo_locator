#!/usr/bin/env python3
"""
Тестирование API с ключами из переменных окружения
Использование: 
export YANDEX_API_KEY="ваш_ключ"
export DGIS_API_KEY="ваш_ключ"
python3 test_with_env_keys.py
"""
import os
import sys
import requests
import json

def test_yandex_api():
    """Тест Yandex API"""
    api_key = os.getenv('YANDEX_API_KEY')
    if not api_key:
        print("❌ YANDEX_API_KEY не установлен")
        return False
    
    print("🔍 ТЕСТИРОВАНИЕ YANDEX GEOCODING")
    print("=" * 40)
    
    url = 'https://geocode-maps.yandex.ru/1.x/'
    params = {
        'apikey': api_key,
        'geocode': 'Красная площадь, Москва',
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
                
                print(f"✅ Адрес: {formatted_address}")
                print(f"📍 Координаты: {coordinates[1]}, {coordinates[0]}")
                return True
            else:
                print("❌ Адрес не найден")
                return False
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_dgis_api():
    """Тест 2GIS API"""
    api_key = os.getenv('DGIS_API_KEY')
    if not api_key:
        print("❌ DGIS_API_KEY не установлен")
        return False
    
    print("\n🔍 ТЕСТИРОВАНИЕ 2GIS SEARCH")
    print("=" * 40)
    
    url = 'https://catalog.api.2gis.com/3.0/items'
    params = {
        'key': api_key,
        'q': 'кафе',
        'point': '37.6176,55.7558',
        'radius': 1000,
        'region_id': 1,
        'page_size': 3,
        'fields': 'items.point,items.address,items.rubrics'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'error' in data.get('meta', {}):
                error_info = data['meta']['error']
                print(f"❌ API Ошибка: {error_info.get('message', 'Unknown error')}")
                return False
            
            items = data.get('result', {}).get('items', [])
            total = data.get('meta', {}).get('total', 0)
            
            print(f"✅ Найдено {len(items)} из {total} объектов")
            
            for i, item in enumerate(items[:2], 1):
                name = item.get('name', 'Без названия')
                address = item.get('address_name', 'Адрес не указан')
                print(f"{i}. {name} - {address}")
            
            return True
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_geo_api_endpoint():
    """Тест нашего geo API endpoint"""
    print("\n🔍 ТЕСТИРОВАНИЕ GEO API ENDPOINT")
    print("=" * 40)
    
    try:
        response = requests.get('http://localhost:5000/api/geo/locate?address=Красная%20площадь,%20Москва', timeout=10)
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                results = data.get('results', [])
                if results:
                    result = results[0]
                    print(f"✅ Источник: {data.get('source')}")
                    print(f"📍 Координаты: {result.get('latitude')}, {result.get('longitude')}")
                    print(f"📍 Адрес: {result.get('formatted_address', '')[:100]}...")
                    return True
            
            print(f"❌ API вернул: {data}")
            return False
        else:
            print(f"❌ HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 ТЕСТИРОВАНИЕ API КЛЮЧЕЙ")
    print("=" * 50)
    
    results = {
        'yandex': test_yandex_api(),
        'dgis': test_dgis_api(),
        'geo_endpoint': test_geo_api_endpoint()
    }
    
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ")
    print("=" * 50)
    
    for test_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\nИтог: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("\n🎉 ВСЕ API РАБОТАЮТ!")
    elif passed > 0:
        print(f"\n⚠️  Частично работает ({passed}/{total})")
    else:
        print("\n❌ ВСЕ API НЕ РАБОТАЮТ")

if __name__ == "__main__":
    main()
