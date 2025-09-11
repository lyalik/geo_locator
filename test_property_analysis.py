#!/usr/bin/env python3
"""
Тест для проверки работы раздела "Анализ объектов недвижимости"
"""
import requests
import json
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('.env')

BASE_URL = "http://localhost:5001"

def test_property_analysis():
    """Тестирование анализа недвижимости"""
    print("🏠 Тестирование раздела 'Анализ объектов недвижимости'")
    print("=" * 60)
    
    # Тест 1: Поиск по адресу
    print("\n1. Тест поиска по адресу:")
    test_address = "Москва, Красная площадь, 1"
    
    try:
        response = requests.get(f"{BASE_URL}/api/geo/locate", 
                              params={"address": test_address},
                              timeout=30)
        
        print(f"   Запрос: {test_address}")
        print(f"   Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Успешно получен ответ")
            
            # Проверяем результаты Yandex
            if data.get('yandex'):
                yandex_success = data['yandex'].get('success', False)
                print(f"   📍 Yandex Maps: {'✅ Работает' if yandex_success else '❌ Ошибка'}")
                if not yandex_success:
                    error = data['yandex'].get('error', 'Unknown error')
                    print(f"      Ошибка: {error}")
                    if data['yandex'].get('error_code') == 403:
                        print(f"      💡 Рекомендация: {data['yandex'].get('recommendation', 'Проверьте API ключ')}")
            
            # Проверяем результаты 2GIS
            if data.get('dgis'):
                dgis_success = data['dgis'].get('success', False)
                print(f"   🗺️  2GIS: {'✅ Работает' if dgis_success else '❌ Ошибка'}")
                if not dgis_success:
                    error = data['dgis'].get('error', 'Unknown error')
                    print(f"      Ошибка: {error}")
        else:
            print(f"   ❌ Ошибка HTTP: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Ошибка запроса: {e}")
    
    # Тест 2: Поиск по координатам
    print("\n2. Тест поиска по координатам:")
    test_lat, test_lon = 55.753215, 37.622504  # Красная площадь
    
    try:
        response = requests.get(f"{BASE_URL}/api/geo/locate/coordinates", 
                              params={"lat": test_lat, "lon": test_lon},
                              timeout=30)
        
        print(f"   Координаты: {test_lat}, {test_lon}")
        print(f"   Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Успешно получен ответ")
            
            # Проверяем результаты
            if data.get('yandex'):
                yandex_success = data['yandex'].get('success', False)
                print(f"   📍 Yandex Maps: {'✅ Работает' if yandex_success else '❌ Ошибка'}")
            
            if data.get('dgis'):
                dgis_success = data['dgis'].get('success', False)
                print(f"   🗺️  2GIS: {'✅ Работает' if dgis_success else '❌ Ошибка'}")
        else:
            print(f"   ❌ Ошибка HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка запроса: {e}")
    
    # Тест 3: Поиск по кадастровому номеру
    print("\n3. Тест поиска по кадастровому номеру:")
    test_cadastral = "77:01:0001001:1234"
    
    try:
        response = requests.get(f"{BASE_URL}/api/geo/locate", 
                              params={"query": test_cadastral, "search_type": "cadastral"},
                              timeout=30)
        
        print(f"   Кадастровый номер: {test_cadastral}")
        print(f"   Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Успешно получен ответ")
            
            # Проверяем результаты
            if data.get('yandex'):
                yandex_success = data['yandex'].get('success', False)
                print(f"   📍 Yandex Maps: {'✅ Работает' if yandex_success else '❌ Ошибка'}")
            
            if data.get('dgis'):
                dgis_success = data['dgis'].get('success', False)
                print(f"   🗺️  2GIS: {'✅ Работает' if dgis_success else '❌ Ошибка'}")
        else:
            print(f"   ❌ Ошибка HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка запроса: {e}")

def test_api_keys():
    """Проверка API ключей"""
    print("\n🔑 Проверка API ключей:")
    print("=" * 30)
    
    yandex_key = os.getenv('YANDEX_API_KEY')
    dgis_key = os.getenv('DGIS_API_KEY')
    
    print(f"YANDEX_API_KEY: {'✅ Установлен' if yandex_key else '❌ Не найден'}")
    if yandex_key:
        print(f"   Длина: {len(yandex_key)} символов")
        print(f"   Начало: {yandex_key[:10]}...")
    
    print(f"DGIS_API_KEY: {'✅ Установлен' if dgis_key else '❌ Не найден'}")
    if dgis_key:
        print(f"   Длина: {len(dgis_key)} символов")
        print(f"   Начало: {dgis_key[:10]}...")

def test_health_check():
    """Проверка состояния сервисов"""
    print("\n🏥 Проверка состояния сервисов:")
    print("=" * 35)
    
    try:
        response = requests.get(f"{BASE_URL}/api/geo/health", timeout=10)
        
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Сервисы работают")
            
            # Показываем статус каждого сервиса
            services = data.get('services', {})
            for service_name, service_data in services.items():
                status = service_data.get('status', 'unknown')
                print(f"   {service_name}: {status}")
        else:
            print(f"❌ Ошибка: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

if __name__ == "__main__":
    print("🧪 ТЕСТИРОВАНИЕ АНАЛИЗА ОБЪЕКТОВ НЕДВИЖИМОСТИ")
    print("=" * 60)
    
    test_api_keys()
    test_health_check()
    test_property_analysis()
    
    print("\n" + "=" * 60)
    print("✅ Тестирование завершено")
