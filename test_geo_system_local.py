#!/usr/bin/env python3
"""
ЛОКАЛЬНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ ГЕОЛОКАЦИОННОГО РАСПОЗНАВАНИЯ
Тестирование без внешних API вызовов
"""
import os
import sys
import requests
import json
import time
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('.env')

class LocalGeoTester:
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.test_images = [
            '/home/denis/Documents/Hackathon_2025/geo_locator/test_image.jpg',
            '/home/denis/Documents/Hackathon_2025/geo_locator/backend/uploads/coordinates/i_annotated_yolo.jpg'
        ]
    
    def test_backend_health(self):
        """Тест работоспособности backend"""
        print("🏥 ТЕСТИРОВАНИЕ BACKEND")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Backend: {data.get('status')}")
                print(f"📋 Версия: {data.get('version')}")
                print(f"💾 База данных: {'✅' if data.get('database') else '❌'}")
                return True
            else:
                print(f"❌ Backend недоступен: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    def test_coordinate_detection(self):
        """Тест координатного распознавания"""
        print("\n📍 ТЕСТИРОВАНИЕ КООРДИНАТНОГО РАСПОЗНАВАНИЯ")
        print("=" * 50)
        
        success_count = 0
        total_count = 0
        
        for test_image in self.test_images:
            if not os.path.exists(test_image):
                continue
                
            total_count += 1
            image_name = os.path.basename(test_image)
            print(f"\n📸 Тестируем: {image_name}")
            
            try:
                with open(test_image, 'rb') as f:
                    files = {'file': f}
                    data = {'location_hint': 'Москва, Россия'}
                    
                    start_time = time.time()
                    response = requests.post(
                        f"{self.base_url}/api/coordinates/detect",
                        files=files,
                        data=data,
                        timeout=60
                    )
                    processing_time = time.time() - start_time
                
                print(f"⏱️ Время: {processing_time:.2f}с")
                print(f"📊 Статус: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    coordinates = result.get('coordinates')
                    confidence = result.get('confidence', 0)
                    objects = result.get('objects', [])
                    source = result.get('source', 'неизвестен')
                    
                    print(f"📍 Координаты: {coordinates}")
                    print(f"🎯 Уверенность: {confidence}")
                    print(f"📦 Объектов: {len(objects)}")
                    print(f"🔍 Источник: {source}")
                    
                    # Считаем успешным если API отвечает
                    success_count += 1
                    
                    # Показываем найденные объекты
                    if objects:
                        print("📋 Объекты:")
                        for i, obj in enumerate(objects[:3]):
                            obj_class = obj.get('class', 'unknown')
                            obj_conf = obj.get('confidence', 0)
                            print(f"   {i+1}. {obj_class}: {obj_conf:.2f}")
                    
                else:
                    print(f"❌ Ошибка: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Исключение: {e}")
        
        print(f"\n📊 Результат: {success_count}/{total_count} изображений обработано")
        return success_count > 0
    
    def test_system_statistics(self):
        """Тест статистики системы"""
        print("\n📊 ТЕСТИРОВАНИЕ СТАТИСТИКИ СИСТЕМЫ")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.base_url}/api/coordinates/statistics", timeout=30)
            
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Статистика получена")
                
                # Показываем основную информацию
                if 'system' in stats:
                    system = stats['system']
                    print(f"🔧 Система: {system.get('name', 'Geo Locator')}")
                    print(f"📋 Версия: {system.get('version', '1.0')}")
                
                # Показываем статус сервисов
                if 'services' in stats:
                    services = stats['services']
                    active_services = sum(1 for status in services.values() if status)
                    total_services = len(services)
                    print(f"🔌 Сервисы: {active_services}/{total_services} активны")
                    
                    # Показываем ключевые сервисы
                    key_services = ['yandex_maps', 'dgis', 'mistral_ai', 'yolo']
                    for service in key_services:
                        if service in services:
                            status = "✅" if services[service] else "❌"
                            print(f"   {service}: {status}")
                
                # Показываем данные базы
                if 'database' in stats:
                    db = stats['database']
                    photos = db.get('photos', 0)
                    violations = db.get('violations', 0)
                    print(f"💾 База данных:")
                    print(f"   📸 Фото: {photos}")
                    print(f"   🚨 Нарушения: {violations}")
                
                return True
            else:
                print(f"❌ Ошибка получения статистики: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение: {e}")
            return False
    
    def test_violation_detection(self):
        """Тест детекции нарушений"""
        print("\n🚨 ТЕСТИРОВАНИЕ ДЕТЕКЦИИ НАРУШЕНИЙ")
        print("=" * 50)
        
        test_image = self.test_images[0] if os.path.exists(self.test_images[0]) else None
        if not test_image:
            print("❌ Тестовое изображение не найдено")
            return False
        
        try:
            with open(test_image, 'rb') as f:
                files = {'file': f}
                
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/api/violations/detect",
                    files=files,
                    timeout=60
                )
                processing_time = time.time() - start_time
            
            print(f"⏱️ Время обработки: {processing_time:.2f}с")
            print(f"📊 Статус: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                violations = result.get('violations', [])
                print(f"✅ Детекция успешна")
                print(f"🚨 Нарушений найдено: {len(violations)}")
                
                # Показываем найденные нарушения
                for i, violation in enumerate(violations[:3]):
                    category = violation.get('category', 'unknown')
                    confidence = violation.get('confidence', 0)
                    source = violation.get('source', 'unknown')
                    print(f"   {i+1}. {category}: {confidence:.2f} ({source})")
                
                return True
            else:
                print(f"❌ Ошибка детекции: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение: {e}")
            return False
    
    def test_mistral_config(self):
        """Тест конфигурации Mistral AI"""
        print("\n🤖 ТЕСТИРОВАНИЕ КОНФИГУРАЦИИ MISTRAL AI")
        print("=" * 50)
        
        api_key = os.getenv('MISTRAL_API_KEY')
        model = os.getenv('MISTRAL_MODEL', 'pixtral-12b-2409')
        
        print(f"🔑 API ключ: {'✅ Настроен' if api_key else '❌ Не найден'}")
        print(f"🤖 Модель: {model}")
        
        if api_key:
            print(f"🔐 Ключ: {api_key[:8]}...")
            return True
        else:
            print("⚠️ Mistral AI API ключ не настроен в .env")
            return False
    
    def generate_report(self, test_results):
        """Генерация отчета"""
        print("\n📋 ИТОГОВЫЙ ОТЧЕТ")
        print("=" * 60)
        
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results if result[1])
        
        print(f"🎯 Результат: {passed_tests}/{total_tests} тестов пройдено")
        print(f"📊 Успешность: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n📝 ДЕТАЛИЗАЦИЯ:")
        for test_name, result in test_results:
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            print(f"   {test_name}: {status}")
        
        # Рекомендации
        print("\n💡 РЕКОМЕНДАЦИИ:")
        if passed_tests == total_tests:
            print("🎉 Система работает отлично!")
        elif passed_tests >= total_tests * 0.8:
            print("⚠️ Система работает хорошо, есть мелкие проблемы")
        elif passed_tests >= total_tests * 0.6:
            print("🔧 Система частично работает, нужны доработки")
        else:
            print("❌ Система требует серьезных исправлений")
        
        return passed_tests / total_tests

def main():
    print("🚀 ЛОКАЛЬНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ ГЕОЛОКАЦИИ")
    print("=" * 70)
    print("🤖 Mistral AI + 🎯 YOLO + 🌐 Панорамы + 📍 Координаты")
    print("=" * 70)
    
    tester = LocalGeoTester()
    test_results = []
    
    # Последовательность тестов
    tests = [
        ("Backend Health", tester.test_backend_health),
        ("Mistral AI Config", tester.test_mistral_config),
        ("System Statistics", tester.test_system_statistics),
        ("Coordinate Detection", tester.test_coordinate_detection),
        ("Violation Detection", tester.test_violation_detection)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🧪 Запуск теста: {test_name}")
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            test_results.append((test_name, False))
    
    # Генерируем отчет
    success_rate = tester.generate_report(test_results)
    
    return success_rate >= 0.6

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
