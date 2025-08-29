#!/usr/bin/env python3
"""
Быстрый тест API с ключами
"""
import requests
import json

# Вставьте ваши ключи здесь:
YANDEX_KEY = "6b7fac7-fc7f-4c1c-09bd-c354cd93f"  # Ключ из скриншота
DGIS_KEY = "ruxrqk2730"  # Замените на ваш реальный 2GIS ключ

def test_yandex():
    print("🔍 Тест Yandex API...")
    url = 'https://geocode-maps.yandex.ru/1.x/'
    params = {
        'apikey': YANDEX_KEY,
        'geocode': 'Красная площадь, Москва',
        'format': 'json',
        'results': 1,
        'lang': 'ru_RU'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Yandex статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            geo_objects = data.get('response', {}).get('GeoObjectCollection', {}).get('featureMember', [])
            if geo_objects:
                geo_object = geo_objects[0]['GeoObject']
                coordinates = geo_object['Point']['pos'].split()
                print(f"✅ Yandex работает! Координаты: {coordinates[1]}, {coordinates[0]}")
                return True
        
        print(f"❌ Yandex ошибка: {response.text}")
        return False
    except Exception as e:
        print(f"❌ Yandex исключение: {e}")
        return False

def test_dgis():
    print("\n🔍 Тест 2GIS API...")
    url = 'https://catalog.api.2gis.com/3.0/items'
    params = {
        'key': DGIS_KEY,
        'q': 'кафе',
        'point': '37.6176,55.7558',
        'radius': 1000,
        'region_id': 1,
        'page_size': 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"2GIS статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'error' not in data.get('meta', {}):
                items = data.get('result', {}).get('items', [])
                print(f"✅ 2GIS работает! Найдено: {len(items)} объектов")
                return True
            else:
                print(f"❌ 2GIS API ошибка: {data['meta']['error']}")
        else:
            print(f"❌ 2GIS HTTP ошибка: {response.text}")
        return False
    except Exception as e:
        print(f"❌ 2GIS исключение: {e}")
        return False

if __name__ == "__main__":
    print("🚀 БЫСТРЫЙ ТЕСТ API")
    print("=" * 30)
    
    if YANDEX_KEY == "6b7fac7-fc7f-4c1c-09bd-c354cd93f":
        print("⚠️  Замените YANDEX_KEY на ваш реальный ключ!")
    
    if DGIS_KEY == "YOUR_DGIS_KEY":
        print("⚠️  Замените DGIS_KEY на ваш реальный ключ!")
    
    yandex_ok = test_yandex()
    dgis_ok = test_dgis()
    
    print(f"\n📊 Результат:")
    print(f"Yandex: {'✅' if yandex_ok else '❌'}")
    print(f"2GIS: {'✅' if dgis_ok else '❌'}")
