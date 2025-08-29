#!/usr/bin/env python3
"""
Тест интеграции OpenStreetMap API в Geo Locator
Проверяет все компоненты OSM интеграции
"""

import requests
import json
import time
import sys
import os

# Добавляем путь к backend для импорта модулей
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_osm_api_endpoints():
    """Тестирование всех OSM API endpoints"""
    base_url = "http://localhost:5000"
    
    print("🔍 Тестирование OSM API endpoints...")
    
    # Тест координат Москвы
    moscow_lat, moscow_lon = 55.7558, 37.6176
    
    tests = [
        {
            "name": "OSM Health Check",
            "url": f"{base_url}/api/osm/health",
            "method": "GET"
        },
        {
            "name": "OSM Geocoding",
            "url": f"{base_url}/api/osm/geocode",
            "method": "GET",
            "params": {"address": "Красная площадь, Москва"}
        },
        {
            "name": "OSM Reverse Geocoding", 
            "url": f"{base_url}/api/osm/reverse-geocode",
            "method": "GET",
            "params": {"lat": moscow_lat, "lon": moscow_lon}
        },
        {
            "name": "OSM Buildings",
            "url": f"{base_url}/api/osm/buildings",
            "method": "GET", 
            "params": {"lat": moscow_lat, "lon": moscow_lon, "radius": 500}
        },
        {
            "name": "OSM Search Places",
            "url": f"{base_url}/api/osm/search",
            "method": "GET",
            "params": {"query": "кафе", "lat": moscow_lat, "lon": moscow_lon}
        },
        {
            "name": "OSM Urban Context",
            "url": f"{base_url}/api/osm/urban-context", 
            "method": "GET",
            "params": {"lat": moscow_lat, "lon": moscow_lon, "radius": 1000}
        }
    ]
    
    results = []
    
    for test in tests:
        try:
            print(f"  ⏳ {test['name']}...")
            
            if test['method'] == 'GET':
                response = requests.get(
                    test['url'], 
                    params=test.get('params', {}),
                    timeout=10
                )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                
                result = {
                    "test": test['name'],
                    "status": "✅ PASS" if success else "⚠️ PARTIAL",
                    "response_time": response.elapsed.total_seconds(),
                    "data_count": len(data.get('buildings', data.get('results', data.get('places', []))))
                }
                
                if success:
                    print(f"    ✅ {test['name']} - OK ({result['response_time']:.2f}s)")
                    if result['data_count'] > 0:
                        print(f"       📊 Получено записей: {result['data_count']}")
                else:
                    print(f"    ⚠️ {test['name']} - Частичный успех")
                    
            else:
                result = {
                    "test": test['name'],
                    "status": f"❌ FAIL ({response.status_code})",
                    "response_time": response.elapsed.total_seconds(),
                    "error": response.text[:200]
                }
                print(f"    ❌ {test['name']} - Ошибка {response.status_code}")
                
            results.append(result)
            
        except Exception as e:
            result = {
                "test": test['name'],
                "status": "❌ ERROR",
                "error": str(e)
            }
            results.append(result)
            print(f"    ❌ {test['name']} - Исключение: {e}")
    
    return results

def test_geo_aggregator_osm():
    """Тестирование интеграции OSM в geo aggregator"""
    print("\n🔍 Тестирование Geo Aggregator с OSM...")
    
    try:
        from services.geo_aggregator_service import GeoAggregatorService
        
        aggregator = GeoAggregatorService()
        
        # Тест поиска места с OSM
        print("  ⏳ Тестирование поиска места...")
        results = aggregator._search_external_apis("Красная площадь")
        
        osm_found = 'osm' in results and results['osm'].get('success')
        
        if osm_found:
            print("    ✅ OSM поиск работает")
            print(f"       📍 Координаты: {results['osm']['coordinates']}")
            return True
        else:
            print("    ⚠️ OSM поиск не вернул результатов")
            return False
            
    except Exception as e:
        print(f"    ❌ Ошибка в geo aggregator: {e}")
        return False

def test_frontend_integration():
    """Тестирование frontend интеграции"""
    print("\n🔍 Тестирование Frontend интеграции...")
    
    base_url = "http://localhost:3000"
    
    try:
        # Проверяем доступность frontend
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("    ✅ Frontend доступен")
            
            # Проверяем API вызовы из frontend
            api_tests = [
                f"http://localhost:5000/api/osm/buildings?lat=55.7558&lon=37.6176&radius=200",
                f"http://localhost:5000/api/osm/urban-context?lat=55.7558&lon=37.6176&radius=1000"
            ]
            
            for api_url in api_tests:
                try:
                    api_response = requests.get(api_url, timeout=10)
                    if api_response.status_code == 200:
                        data = api_response.json()
                        if data.get('success'):
                            print(f"    ✅ API endpoint работает: {api_url.split('/')[-1].split('?')[0]}")
                        else:
                            print(f"    ⚠️ API endpoint частично работает: {api_url.split('/')[-1].split('?')[0]}")
                    else:
                        print(f"    ❌ API endpoint недоступен: {api_url.split('/')[-1].split('?')[0]}")
                except Exception as e:
                    print(f"    ❌ Ошибка API: {e}")
            
            return True
        else:
            print(f"    ❌ Frontend недоступен (статус: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"    ❌ Ошибка подключения к frontend: {e}")
        return False

def generate_test_report(osm_results, geo_test, frontend_test):
    """Генерация отчета о тестировании"""
    print("\n" + "="*60)
    print("📋 ОТЧЕТ О ТЕСТИРОВАНИИ OSM ИНТЕГРАЦИИ")
    print("="*60)
    
    # OSM API результаты
    print("\n🔧 OSM API Endpoints:")
    passed = sum(1 for r in osm_results if "PASS" in r['status'])
    total = len(osm_results)
    print(f"   Пройдено: {passed}/{total}")
    
    for result in osm_results:
        print(f"   {result['status']} {result['test']}")
        if 'response_time' in result:
            print(f"      ⏱️ Время ответа: {result['response_time']:.2f}s")
        if 'data_count' in result and result['data_count'] > 0:
            print(f"      📊 Данных получено: {result['data_count']}")
    
    # Geo Aggregator
    print(f"\n🔄 Geo Aggregator: {'✅ PASS' if geo_test else '❌ FAIL'}")
    
    # Frontend
    print(f"🌐 Frontend Integration: {'✅ PASS' if frontend_test else '❌ FAIL'}")
    
    # Общий результат
    overall_success = (passed >= total * 0.7) and geo_test and frontend_test
    print(f"\n🎯 ОБЩИЙ РЕЗУЛЬТАТ: {'✅ SUCCESS' if overall_success else '❌ NEEDS ATTENTION'}")
    
    if overall_success:
        print("\n🎉 OSM интеграция работает корректно!")
        print("   Можно переходить к тестированию пользовательского интерфейса.")
    else:
        print("\n⚠️ Обнаружены проблемы в OSM интеграции.")
        print("   Рекомендуется проверить логи backend и исправить ошибки.")
    
    print("\n" + "="*60)

def main():
    """Главная функция тестирования"""
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ OSM ИНТЕГРАЦИИ")
    print("="*60)
    
    # Проверяем доступность backend
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend недоступен. Запустите ./start_local.sh")
            return
    except:
        print("❌ Backend недоступен. Запустите ./start_local.sh")
        return
    
    print("✅ Backend доступен, начинаем тестирование...\n")
    
    # Запуск тестов
    osm_results = test_osm_api_endpoints()
    geo_test = test_geo_aggregator_osm()
    frontend_test = test_frontend_integration()
    
    # Генерация отчета
    generate_test_report(osm_results, geo_test, frontend_test)

if __name__ == "__main__":
    main()
