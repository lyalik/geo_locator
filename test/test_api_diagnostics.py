#!/usr/bin/env python3
"""
Диагностический скрипт для тестирования API Yandex и 2GIS
Проверяет конфигурацию ключей, формат запросов и ответы API
"""
import os
import sys
import requests
import json
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment_variables():
    """Проверка переменных окружения"""
    print("=" * 60)
    print("ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ")
    print("=" * 60)
    
    yandex_key = os.getenv('YANDEX_API_KEY')
    dgis_key = os.getenv('DGIS_API_KEY')
    
    print(f"YANDEX_API_KEY: {'✓ Установлен' if yandex_key else '✗ Не найден'}")
    if yandex_key:
        print(f"  Длина ключа: {len(yandex_key)} символов")
        print(f"  Начало ключа: {yandex_key[:10]}...")
    
    print(f"DGIS_API_KEY: {'✓ Установлен' if dgis_key else '✗ Не найден'}")
    if dgis_key:
        print(f"  Длина ключа: {len(dgis_key)} символов")
        print(f"  Начало ключа: {dgis_key[:10]}...")
    
    return yandex_key, dgis_key

def test_yandex_geocoding(api_key, address="Красная площадь, Москва"):
    """Тестирование Yandex Geocoding API"""
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ YANDEX GEOCODING API")
    print("=" * 60)
    
    if not api_key:
        print("❌ API ключ не установлен")
        return False
    
    url = 'https://geocode-maps.yandex.ru/1.x/'
    params = {
        'apikey': api_key,
        'geocode': address,
        'format': 'json',
        'results': 1,
        'lang': 'ru_RU'
    }
    
    print(f"URL: {url}")
    print(f"Параметры: {json.dumps(params, indent=2, ensure_ascii=False)}")
    
    try:
        print("\n🔄 Отправка запроса...")
        response = requests.get(url, params=params, timeout=10)
        
        print(f"Статус код: {response.status_code}")
        print(f"Заголовки ответа: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Успешный ответ:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Проверяем наличие результатов
            geo_objects = data.get('response', {}).get('GeoObjectCollection', {}).get('featureMember', [])
            if geo_objects:
                geo_object = geo_objects[0]['GeoObject']
                coordinates = geo_object['Point']['pos'].split()
                print(f"\n📍 Найденные координаты: {coordinates[1]}, {coordinates[0]}")
                return True
            else:
                print("⚠️ Результаты не найдены")
                return False
        else:
            print(f"❌ Ошибка HTTP {response.status_code}")
            print(f"Текст ошибки: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_yandex_search(api_key, query="кафе", lat=55.7558, lon=37.6176):
    """Тестирование Yandex Search API"""
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ YANDEX SEARCH API")
    print("=" * 60)
    
    if not api_key:
        print("❌ API ключ не установлен")
        return False
    
    url = 'https://api-maps.yandex.ru/search/v1/'
    params = {
        'apikey': api_key,
        'text': query,
        'lang': 'ru_RU',
        'results': 5,
        'format': 'json',
        'll': f"{lon},{lat}",
        'spn': '0.01,0.01'
    }
    
    print(f"URL: {url}")
    print(f"Параметры: {json.dumps(params, indent=2, ensure_ascii=False)}")
    
    try:
        print("\n🔄 Отправка запроса...")
        response = requests.get(url, params=params, timeout=10)
        
        print(f"Статус код: {response.status_code}")
        print(f"Заголовки ответа: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Успешный ответ:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            features = data.get('features', [])
            print(f"\n📊 Найдено объектов: {len(features)}")
            return True
        else:
            print(f"❌ Ошибка HTTP {response.status_code}")
            print(f"Текст ошибки: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_dgis_search(api_key, query="пиццерия", lat=55.7558, lon=37.6176):
    """Тестирование 2GIS Search API"""
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ 2GIS SEARCH API")
    print("=" * 60)
    
    if not api_key:
        print("❌ API ключ не установлен")
        return False
    
    url = 'https://catalog.api.2gis.com/3.0/items'
    params = {
        'key': api_key,
        'q': query,
        'point': f"{lon},{lat}",
        'radius': 1000,
        'region_id': 1,  # Москва
        'page_size': 5,
        'fields': 'items.point,items.adm_div,items.address,items.contact_groups,items.rubrics'
    }
    
    print(f"URL: {url}")
    print(f"Параметры: {json.dumps(params, indent=2, ensure_ascii=False)}")
    
    try:
        print("\n🔄 Отправка запроса...")
        response = requests.get(url, params=params, timeout=10)
        
        print(f"Статус код: {response.status_code}")
        print(f"Заголовки ответа: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Успешный ответ:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            items = data.get('result', {}).get('items', [])
            total = data.get('meta', {}).get('total', 0)
            print(f"\n📊 Найдено объектов: {len(items)} из {total}")
            return True
        else:
            print(f"❌ Ошибка HTTP {response.status_code}")
            print(f"Текст ошибки: {response.text}")
            
            # Попробуем понять причину ошибки
            if response.status_code == 401:
                print("🔑 Возможно, проблема с API ключом")
            elif response.status_code == 403:
                print("🚫 Доступ запрещен - проверьте права API ключа")
            elif response.status_code == 429:
                print("⏱️ Превышен лимит запросов")
            
            return False
            
    except requests.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_dgis_geocoding(api_key, address="Красная площадь, Москва"):
    """Тестирование 2GIS Geocoding"""
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ 2GIS GEOCODING")
    print("=" * 60)
    
    if not api_key:
        print("❌ API ключ не установлен")
        return False
    
    url = 'https://catalog.api.2gis.com/3.0/items'
    params = {
        'key': api_key,
        'q': address,
        'region_id': 1,  # Москва
        'type': 'adm_div.place,building.address',
        'fields': 'items.point,items.adm_div,items.address'
    }
    
    print(f"URL: {url}")
    print(f"Параметры: {json.dumps(params, indent=2, ensure_ascii=False)}")
    
    try:
        print("\n🔄 Отправка запроса...")
        response = requests.get(url, params=params, timeout=10)
        
        print(f"Статус код: {response.status_code}")
        print(f"Заголовки ответа: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Успешный ответ:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            items = data.get('result', {}).get('items', [])
            if items:
                item = items[0]
                point = item.get('point', {})
                if point:
                    print(f"\n📍 Найденные координаты: {point.get('lat')}, {point.get('lon')}")
            
            return True
        else:
            print(f"❌ Ошибка HTTP {response.status_code}")
            print(f"Текст ошибки: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_backend_services():
    """Тестирование backend сервисов"""
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ BACKEND СЕРВИСОВ")
    print("=" * 60)
    
    try:
        # Добавляем путь к backend
        sys.path.append('/home/denis/Documents/Hackathon_2025/geo_locator/backend')
        
        from services.yandex_maps_service import YandexMapsService
        from services.dgis_service import DGISService
        
        print("✅ Импорт сервисов успешен")
        
        # Тестируем Yandex сервис
        print("\n🔄 Тестирование YandexMapsService...")
        yandex_service = YandexMapsService()
        yandex_result = yandex_service.geocode("Красная площадь, Москва")
        print(f"Yandex результат: {json.dumps(yandex_result, indent=2, ensure_ascii=False)}")
        
        # Тестируем 2GIS сервис
        print("\n🔄 Тестирование DGISService...")
        dgis_service = DGISService()
        dgis_result = dgis_service.geocode("Красная площадь, Москва")
        print(f"2GIS результат: {json.dumps(dgis_result, indent=2, ensure_ascii=False)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка тестирования сервисов: {e}")
        return False

def main():
    """Основная функция диагностики"""
    print("🔍 ДИАГНОСТИКА API YANDEX И 2GIS")
    print(f"Время запуска: {datetime.now()}")
    
    # Проверяем переменные окружения
    yandex_key, dgis_key = check_environment_variables()
    
    results = {
        'yandex_geocoding': False,
        'yandex_search': False,
        'dgis_search': False,
        'dgis_geocoding': False,
        'backend_services': False
    }
    
    # Тестируем Yandex API
    if yandex_key:
        results['yandex_geocoding'] = test_yandex_geocoding(yandex_key)
        results['yandex_search'] = test_yandex_search(yandex_key)
    
    # Тестируем 2GIS API
    if dgis_key:
        results['dgis_search'] = test_dgis_search(dgis_key)
        results['dgis_geocoding'] = test_dgis_geocoding(dgis_key)
    
    # Тестируем backend сервисы
    results['backend_services'] = test_backend_services()
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ ПРОШЕЛ" if success else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    print(f"\nОбщий результат: {passed_tests}/{total_tests} тестов прошли успешно")
    
    if passed_tests == 0:
        print("\n🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: Все API тесты провалены!")
        print("Рекомендации:")
        print("1. Проверьте правильность API ключей")
        print("2. Убедитесь, что ключи активны и имеют необходимые права")
        print("3. Проверьте подключение к интернету")
        print("4. Проверьте лимиты API запросов")
    elif passed_tests < total_tests:
        print(f"\n⚠️ ЧАСТИЧНЫЕ ПРОБЛЕМЫ: {total_tests - passed_tests} тестов провалены")
        print("Система может работать с ограниченной функциональностью")
    else:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")

if __name__ == "__main__":
    main()
