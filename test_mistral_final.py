#!/usr/bin/env python3
"""
Финальный тест Mistral AI интеграции
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('.env')

def test_mistral_api_direct():
    """Прямой тест Mistral API"""
    print("🔑 ТЕСТИРОВАНИЕ MISTRAL AI API")
    print("=" * 50)
    
    api_key = os.getenv('MISTRAL_API_KEY')
    model = os.getenv('MISTRAL_MODEL', 'pixtral-12b-2409')
    
    if not api_key:
        print("❌ MISTRAL_API_KEY не найден в .env файле")
        return False
    
    print(f"🤖 Модель: {model}")
    print(f"🔑 API ключ: {api_key[:8]}...")
    
    # Тест простого текстового запроса
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "model": model,
        "messages": [
            {
                "role": "user", 
                "content": "Привет! Ты работаешь?"
            }
        ],
        "max_tokens": 100
    }
    
    try:
        print("📡 Отправляем тестовый запрос...")
        response = requests.post(
            'https://api.mistral.ai/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"📊 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content']
            print(f"✅ Ответ Mistral AI: {message}")
            return True
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"📝 Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False

def test_mistral_service():
    """Тест через наш сервис"""
    print("\n🔧 ТЕСТИРОВАНИЕ MISTRAL SERVICE")
    print("=" * 50)
    
    try:
        # Добавляем путь к backend
        sys.path.append('/home/denis/Documents/Hackathon_2025/geo_locator/backend')
        
        from services.mistral_ai_service import MistralAIService
        
        service = MistralAIService()
        print(f"🤖 Сервис инициализирован")
        print(f"📋 Модель: {service.model}")
        print(f"🔑 API ключ: {'✅ Есть' if service.api_key else '❌ Нет'}")
        print(f"🎭 Демо режим: {'✅ Да' if service.demo_mode else '❌ Нет'}")
        
        if service.demo_mode:
            print("⚠️ Работаем в демо режиме - API ключ не настроен")
            return False
        
        # Тест анализа изображения
        test_image = '/home/denis/Documents/Hackathon_2025/geo_locator/test_image.jpg'
        if os.path.exists(test_image):
            print(f"📸 Тестируем анализ изображения: {test_image}")
            
            result = service.analyze_image(
                test_image, 
                "Опиши что видишь на этом изображении кратко"
            )
            
            if result.get('success'):
                print(f"✅ Анализ успешен:")
                print(f"📝 Описание: {result.get('description', 'Нет описания')}")
                return True
            else:
                print(f"❌ Ошибка анализа: {result.get('error', 'Неизвестная ошибка')}")
                return False
        else:
            print(f"❌ Тестовое изображение не найдено: {test_image}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение в сервисе: {e}")
        return False

def test_coordinate_detection_with_mistral():
    """Тест координатного распознавания с Mistral AI"""
    print("\n📍 ТЕСТИРОВАНИЕ КООРДИНАТНОГО РАСПОЗНАВАНИЯ")
    print("=" * 50)
    
    try:
        # Тест через API
        test_image = '/home/denis/Documents/Hackathon_2025/geo_locator/test_image.jpg'
        if not os.path.exists(test_image):
            print(f"❌ Тестовое изображение не найдено: {test_image}")
            return False
        
        print(f"📸 Тестируем координатное распознавание: {test_image}")
        
        with open(test_image, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                'http://localhost:5001/api/coordinates/detect',
                files=files,
                timeout=60
            )
        
        print(f"📊 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Координаты найдены: {result.get('coordinates')}")
            print(f"🎯 Уверенность: {result.get('confidence', 0)}")
            print(f"📦 Объектов обнаружено: {len(result.get('objects', []))}")
            print(f"🔍 Источник: {result.get('source', 'неизвестен')}")
            return True
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"📝 Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ MISTRAL AI")
    print("=" * 60)
    
    results = []
    
    # Тест 1: Прямой API
    results.append(("Прямой Mistral API", test_mistral_api_direct()))
    
    # Тест 2: Наш сервис
    results.append(("Mistral Service", test_mistral_service()))
    
    # Тест 3: Координатное распознавание
    results.append(("Координатное распознавание", test_coordinate_detection_with_mistral()))
    
    # Итоги
    print("\n📋 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
    print("=" * 60)
    
    passed = 0
    for name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Результат: {passed}/{len(results)} тестов пройдено")
    
    if passed == len(results):
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Mistral AI готов к работе!")
    else:
        print("⚠️ Требуется доработка конфигурации Mistral AI")
