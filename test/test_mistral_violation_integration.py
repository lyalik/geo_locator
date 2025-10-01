#!/usr/bin/env python3
"""
Тест полной интеграции Mistral AI в систему анализа нарушений
Проверяет замену Google Vision на Mistral AI в violation_api.py
"""

import os
import sys
import requests
import json
from pathlib import Path

# Добавляем путь к backend для импорта
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_mistral_violation_api():
    """Тестирует API анализа нарушений с Mistral AI"""
    
    print("🧪 Тестирование Mistral AI интеграции в violation API...")
    
    # URL для тестирования
    base_url = "http://localhost:5001"
    detect_url = f"{base_url}/api/violations/detect"
    batch_url = f"{base_url}/api/violations/batch_detect"
    
    # Проверяем доступность API
    try:
        health_response = requests.get(f"{base_url}/api/violations/health", timeout=5)
        if health_response.status_code != 200:
            print(f"❌ Backend недоступен: {health_response.status_code}")
            return False
        print("✅ Backend доступен")
    except Exception as e:
        print(f"❌ Ошибка подключения к backend: {e}")
        return False
    
    # Путь к тестовому изображению
    test_image = "test_image.jpg"
    if not os.path.exists(test_image):
        print(f"❌ Тестовое изображение {test_image} не найдено")
        return False
    
    print(f"📸 Используем тестовое изображение: {test_image}")
    
    # Тест 1: Одиночное изображение
    print("\n🔍 Тест 1: Анализ одиночного изображения")
    try:
        with open(test_image, 'rb') as f:
            files = {'file': f}
            data = {
                'user_id': 'test_user',
                'location_notes': 'Test location',
                'location_hint': 'Moscow, Russia'
            }
            
            response = requests.post(detect_url, files=files, data=data, timeout=30)
            
        if response.status_code == 200:
            result = response.json()
            print("✅ API вызов успешен")
            
            # Проверяем структуру ответа
            if result.get('success'):
                violations = result.get('data', {}).get('violations', [])
                print(f"📊 Найдено нарушений: {len(violations)}")
                
                # Анализируем источники нарушений
                mistral_count = len([v for v in violations if v.get('source') == 'mistral_ai'])
                yolo_count = len([v for v in violations if v.get('source') == 'yolo'])
                
                print(f"🤖 Mistral AI: {mistral_count} нарушений")
                print(f"🎯 YOLO: {yolo_count} нарушений")
                
                # Проверяем, что Mistral AI используется
                if mistral_count > 0:
                    print("✅ Mistral AI успешно интегрирован")
                    
                    # Показываем детали Mistral AI нарушений
                    for violation in violations:
                        if violation.get('source') == 'mistral_ai':
                            print(f"  • {violation.get('category', 'unknown')}: {violation.get('description', 'N/A')} ({violation.get('confidence', 0)*100:.1f}%)")
                else:
                    print("⚠️ Mistral AI нарушения не найдены")
                
                return True
            else:
                print(f"❌ API вернул ошибку: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

def test_mistral_batch_processing():
    """Тестирует batch processing с Mistral AI"""
    
    print("\n🔍 Тест 2: Batch анализ изображений")
    
    base_url = "http://localhost:5001"
    batch_url = f"{base_url}/api/violations/batch_detect"
    
    test_image = "test_image.jpg"
    if not os.path.exists(test_image):
        print(f"❌ Тестовое изображение {test_image} не найдено")
        return False
    
    try:
        # Отправляем несколько копий одного изображения для batch теста
        files = []
        for i in range(2):
            files.append(('files', (f'test_image_{i}.jpg', open(test_image, 'rb'), 'image/jpeg')))
        
        data = {
            'user_id': 'test_user',
            'location_hint': 'Moscow, Russia'
        }
        
        response = requests.post(batch_url, files=files, data=data, timeout=60)
        
        # Закрываем файлы
        for _, (_, file_obj, _) in files:
            file_obj.close()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Batch API вызов успешен")
            
            if result.get('success'):
                batch_results = result.get('data', [])
                print(f"📊 Обработано файлов: {len(batch_results)}")
                
                total_mistral = 0
                total_yolo = 0
                
                for i, file_result in enumerate(batch_results):
                    if isinstance(file_result, dict):
                        violations = file_result.get('detection', {}).get('violations', [])
                    else:
                        print(f"⚠️ Неожиданная структура данных для файла {i+1}: {type(file_result)}")
                        violations = []
                    
                    mistral_count = len([v for v in violations if v.get('source') == 'mistral_ai'])
                    yolo_count = len([v for v in violations if v.get('source') == 'yolo'])
                    
                    total_mistral += mistral_count
                    total_yolo += yolo_count
                    
                    print(f"  Файл {i+1}: 🤖 Mistral AI: {mistral_count}, 🎯 YOLO: {yolo_count}")
                
                print(f"📊 Общий итог: 🤖 Mistral AI: {total_mistral}, 🎯 YOLO: {total_yolo}")
                
                if total_mistral > 0:
                    print("✅ Mistral AI успешно работает в batch режиме")
                    return True
                else:
                    print("⚠️ Mistral AI нарушения не найдены в batch режиме")
                    return False
            else:
                print(f"❌ Batch API вернул ошибку: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Batch HTTP ошибка: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при batch тестировании: {e}")
        return False

def check_environment():
    """Проверяет настройки окружения"""
    
    print("🔧 Проверка переменных окружения...")
    
    # Проверяем наличие .env файла
    env_file = Path('.env')
    if env_file.exists():
        print("✅ Файл .env найден")
        
        # Читаем содержимое .env
        with open(env_file, 'r') as f:
            env_content = f.read()
            
        if 'MISTRAL_API_KEY' in env_content:
            print("✅ MISTRAL_API_KEY найден в .env")
        else:
            print("⚠️ MISTRAL_API_KEY не найден в .env")
            
    else:
        print("⚠️ Файл .env не найден")
    
    # Проверяем переменные окружения
    mistral_key = os.getenv('MISTRAL_API_KEY')
    if mistral_key:
        print(f"✅ MISTRAL_API_KEY установлен: {mistral_key[:10]}...")
    else:
        print("⚠️ MISTRAL_API_KEY не установлен в переменных окружения")

def main():
    """Основная функция тестирования"""
    
    print("=" * 60)
    print("🧪 ТЕСТ ИНТЕГРАЦИИ MISTRAL AI В VIOLATION ANALYSIS")
    print("=" * 60)
    
    # Проверяем окружение
    check_environment()
    
    # Запускаем тесты
    test1_success = test_mistral_violation_api()
    test2_success = test_mistral_batch_processing()
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("=" * 60)
    print(f"🔍 Одиночный анализ: {'✅ ПРОЙДЕН' if test1_success else '❌ ПРОВАЛЕН'}")
    print(f"🔍 Batch анализ: {'✅ ПРОЙДЕН' if test2_success else '❌ ПРОВАЛЕН'}")
    
    if test1_success and test2_success:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Mistral AI успешно интегрирован в violation analysis")
        return True
    else:
        print("\n⚠️ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ. Проверьте настройки API ключей и backend")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
