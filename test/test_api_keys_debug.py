#!/usr/bin/env python3
"""
Отладка API ключей Яндекс и 2GIS
"""
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_yandex_api():
    """Тест Яндекс API напрямую"""
    print("🟡 Тестируем Яндекс Geocoder API...")
    
    api_key = os.getenv('YANDEX_API_KEY')
    if not api_key:
        print("❌ YANDEX_API_KEY не найден")
        return
    
    print(f"🔑 Ключ: {api_key[:20]}...")
    
    # Тест геокодирования
    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        'apikey': api_key,
        'geocode': 'Москва',
        'format': 'json',
        'results': 1,
        'lang': 'ru_RU'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"📡 HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            geo_objects = data.get('response', {}).get('GeoObjectCollection', {}).get('featureMember', [])
            
            if geo_objects:
                geo_object = geo_objects[0]['GeoObject']
                coordinates = geo_object['Point']['pos'].split()
                lat, lon = float(coordinates[1]), float(coordinates[0])
                address = geo_object.get('metaDataProperty', {}).get('GeocoderMetaData', {}).get('text', '')
                
                print(f"✅ Адрес: {address}")
                print(f"📍 Координаты: {lat}, {lon}")
                
                # Проверим, правильные ли координаты для Москвы
                if 55.0 < lat < 56.0 and 37.0 < lon < 38.0:
                    print("✅ Координаты Москвы корректные")
                else:
                    print(f"❌ Координаты неверные для Москвы: {lat}, {lon}")
            else:
                print("❌ Результаты не найдены")
        else:
            print(f"❌ Ошибка HTTP: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_2gis_api():
    """Тест 2GIS API напрямую"""
    print("\n🔵 Тестируем 2GIS API...")
    
    api_key = os.getenv('DGIS_API_KEY')
    if not api_key:
        print("❌ DGIS_API_KEY не найден")
        return
    
    print(f"🔑 Ключ: {api_key[:20]}...")
    
    # Тест поиска
    url = "https://catalog.api.2gis.com/3.0/items"
    params = {
        'key': api_key,
        'q': 'Москва',
        'region_id': 1,
        'type': 'adm_div.place',
        'fields': 'items.point,items.adm_div,items.address',
        'page_size': 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"📡 HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📄 Ответ: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            items = data.get('result', {}).get('items', [])
            if items:
                item = items[0]
                print(f"✅ Найдено: {item.get('name', 'Без названия')}")
                if 'point' in item:
                    point = item['point']
                    lat, lon = point.get('lat'), point.get('lon')
                    print(f"📍 Координаты: {lat}, {lon}")
                else:
                    print("⚠️ Координаты не найдены")
            else:
                print("❌ Результаты не найдены")
        else:
            print(f"❌ Ошибка HTTP: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_backend_services():
    """Тест backend сервисов"""
    print("\n🔧 Тестируем backend сервисы...")
    
    # Добавляем путь к backend
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
    
    try:
        from services.yandex_maps_service import YandexMapsService
        from services.dgis_service import DGISService
        
        # Тест Yandex
        print("🟡 Тест YandexMapsService...")
        yandex = YandexMapsService()
        result = yandex.geocode('Москва')
        print(f"Результат: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # Тест 2GIS
        print("\n🔵 Тест DGISService...")
        dgis = DGISService()
        result = dgis.geocode('Москва')
        print(f"Результат: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"❌ Ошибка импорта сервисов: {e}")

if __name__ == "__main__":
    print("🧪 Отладка API ключей\n")
    
    # Проверяем переменные окружения
    print("📋 Переменные окружения:")
    print(f"YANDEX_API_KEY: {'✅' if os.getenv('YANDEX_API_KEY') else '❌'}")
    print(f"DGIS_API_KEY: {'✅' if os.getenv('DGIS_API_KEY') else '❌'}")
    print()
    
    test_yandex_api()
    test_2gis_api()
    test_backend_services()
    
    print("\n✨ Отладка завершена!")
