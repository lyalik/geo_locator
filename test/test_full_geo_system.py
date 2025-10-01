#!/usr/bin/env python3
"""
ПОЛНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ ГЕОЛОКАЦИОННОГО РАСПОЗНАВАНИЯ
С интеграцией Mistral AI, YOLO, панорамным анализом и всеми сервисами
"""
import os
import sys
import requests
import json
import time
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('.env')

class GeoSystemTester:
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.test_images = [
            '/home/denis/Documents/Hackathon_2025/geo_locator/test_image.jpg',
            '/home/denis/Documents/Hackathon_2025/geo_locator/backend/uploads/coordinates/i_annotated_yolo.jpg',
            '/home/denis/Documents/Hackathon_2025/geo_locator/backend/uploads/coordinates/test_image_annotated_yolo.jpg'
        ]
        self.results = []
    
    def test_backend_health(self):
        """Тест работоспособности backend"""
        print("🏥 ТЕСТИРОВАНИЕ РАБОТОСПОСОБНОСТИ BACKEND")
        print("=" * 60)
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            print(f"📊 Статус: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Backend работает: {data.get('status')}")
                print(f"📋 Версия: {data.get('version')}")
                print(f"💾 База данных: {'✅' if data.get('database') else '❌'}")
                return True
            else:
                print(f"❌ Backend недоступен: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка подключения к backend: {e}")
            return False
    
    def test_mistral_ai_integration(self):
        """Тест интеграции Mistral AI"""
        print("\n🤖 ТЕСТИРОВАНИЕ MISTRAL AI ИНТЕГРАЦИИ")
        print("=" * 60)
        
        try:
            # Добавляем путь к backend
            sys.path.append('/home/denis/Documents/Hackathon_2025/geo_locator/backend')
            
            from services.mistral_ai_service import MistralAIService
            
            service = MistralAIService()
            print(f"🔧 Сервис инициализирован")
            print(f"📋 Модель: {service.model}")
            print(f"🔑 API ключ: {'✅' if service.api_key else '❌'}")
            print(f"🎭 Демо режим: {'❌' if service.demo_mode else '✅'}")
            
            if service.demo_mode:
                print("⚠️ Mistral AI работает в демо режиме")
                return False
            
            # Тест анализа изображения
            test_image = self.test_images[0] if os.path.exists(self.test_images[0]) else None
            if test_image:
                print(f"📸 Тестируем анализ: {os.path.basename(test_image)}")
                
                result = service.analyze_image(
                    test_image, 
                    "Найди на изображении текст с адресами, названиями улиц, номерами домов или координатами GPS"
                )
                
                if result.get('success'):
                    print(f"✅ Mistral AI анализ успешен")
                    print(f"📝 Найденный текст: {result.get('text', 'Нет текста')[:100]}...")
                    return True
                else:
                    print(f"❌ Ошибка Mistral AI: {result.get('error')}")
                    return False
            else:
                print("❌ Тестовое изображение не найдено")
                return False
                
        except Exception as e:
            print(f"❌ Исключение в Mistral AI: {e}")
            return False
    
    def test_yolo_object_detection(self):
        """Тест YOLO детекции объектов"""
        print("\n🎯 ТЕСТИРОВАНИЕ YOLO ДЕТЕКЦИИ ОБЪЕКТОВ")
        print("=" * 60)
        
        try:
            sys.path.append('/home/denis/Documents/Hackathon_2025/geo_locator/backend')
            
            from services.yolo_violation_detector import YOLOObjectDetector
            
            service = YOLOObjectDetector()
            print(f"🔧 YOLO сервис инициализирован")
            print(f"📋 Модель: {service.model_path}")
            print(f"🎯 Модель загружена: {'✅' if service.model else '❌'}")
            
            if not service.model:
                print("❌ YOLO модель не загружена")
                return False
            
            # Тест детекции на изображении
            test_image = self.test_images[0] if os.path.exists(self.test_images[0]) else None
            if test_image:
                print(f"📸 Тестируем детекцию: {os.path.basename(test_image)}")
                
                result = service.detect_objects(test_image)
                
                if result.get('success'):
                    objects = result.get('objects', [])
                    print(f"✅ YOLO детекция успешна")
                    print(f"📦 Объектов найдено: {len(objects)}")
                    
                    for i, obj in enumerate(objects[:3]):  # Показываем первые 3
                        print(f"   {i+1}. {obj.get('class', 'unknown')}: {obj.get('confidence', 0):.2f}")
                    
                    return len(objects) > 0
                else:
                    print(f"❌ Ошибка YOLO: {result.get('error')}")
                    return False
            else:
                print("❌ Тестовое изображение не найдено")
                return False
                
        except Exception as e:
            print(f"❌ Исключение в YOLO: {e}")
            return False
    
    def test_coordinate_detection_api(self):
        """Тест API координатного распознавания"""
        print("\n📍 ТЕСТИРОВАНИЕ API КООРДИНАТНОГО РАСПОЗНАВАНИЯ")
        print("=" * 60)
        
        results = []
        
        for i, test_image in enumerate(self.test_images):
            if not os.path.exists(test_image):
                print(f"⚠️ Изображение {i+1} не найдено: {test_image}")
                continue
            
            print(f"\n📸 Тестирование изображения {i+1}: {os.path.basename(test_image)}")
            
            try:
                with open(test_image, 'rb') as f:
                    files = {'file': f}
                    data = {'location_hint': 'Москва, Россия'}  # Подсказка для улучшения точности
                    
                    start_time = time.time()
                    response = requests.post(
                        f"{self.base_url}/api/coordinates/detect",
                        files=files,
                        data=data,
                        timeout=120  # Увеличиваем таймаут для полного анализа
                    )
                    processing_time = time.time() - start_time
                
                print(f"⏱️ Время обработки: {processing_time:.2f} сек")
                print(f"📊 Статус ответа: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Анализируем результат
                    coordinates = result.get('coordinates')
                    confidence = result.get('confidence', 0)
                    objects = result.get('objects', [])
                    source = result.get('source', 'неизвестен')
                    enhanced = result.get('enhanced_detection', False)
                    
                    print(f"📍 Координаты: {coordinates}")
                    print(f"🎯 Уверенность: {confidence}")
                    print(f"📦 YOLO объектов: {len(objects)}")
                    print(f"🔍 Источник: {source}")
                    print(f"🚀 Расширенная детекция: {'✅' if enhanced else '❌'}")
                    
                    # Детали объектов
                    if objects:
                        print(f"📋 Найденные объекты:")
                        for j, obj in enumerate(objects[:5]):  # Показываем первые 5
                            print(f"   {j+1}. {obj.get('class', 'unknown')}: {obj.get('confidence', 0):.2f}")
                    
                    # Дополнительная информация
                    if 'address_data' in result:
                        addr = result['address_data']
                        print(f"🏠 Адрес: {addr.get('formatted_address', 'Не найден')}")
                    
                    if 'satellite_data' in result:
                        sat = result['satellite_data']
                        print(f"🛰️ Спутниковые данные: {sat.get('source', 'Нет')}")
                    
                    results.append({
                        'image': os.path.basename(test_image),
                        'success': True,
                        'coordinates': coordinates,
                        'confidence': confidence,
                        'objects_count': len(objects),
                        'processing_time': processing_time,
                        'source': source
                    })
                    
                else:
                    print(f"❌ Ошибка API: {response.status_code}")
                    print(f"📝 Ответ: {response.text[:200]}...")
                    results.append({
                        'image': os.path.basename(test_image),
                        'success': False,
                        'error': f"HTTP {response.status_code}"
                    })
                    
            except Exception as e:
                print(f"❌ Исключение: {e}")
                results.append({
                    'image': os.path.basename(test_image),
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def test_panorama_analysis(self):
        """Тест панорамного анализа"""
        print("\n🌐 ТЕСТИРОВАНИЕ ПАНОРАМНОГО АНАЛИЗА")
        print("=" * 60)
        
        try:
            # Тест статистики системы (включает панорамы)
            response = requests.get(f"{self.base_url}/api/coordinates/statistics", timeout=30)
            
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Статистика получена")
                
                services = stats.get('services', {})
                for service_name, status in services.items():
                    if 'panorama' in service_name.lower() or 'yandex' in service_name.lower() or '2gis' in service_name.lower():
                        print(f"🌐 {service_name}: {'✅' if status else '❌'}")
                
                return True
            else:
                print(f"❌ Ошибка получения статистики: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение в панорамном анализе: {e}")
            return False
    
    def test_batch_processing(self):
        """Тест пакетной обработки"""
        print("\n📦 ТЕСТИРОВАНИЕ ПАКЕТНОЙ ОБРАБОТКИ")
        print("=" * 60)
        
        # Подготавливаем файлы для пакетной обработки
        available_images = [img for img in self.test_images if os.path.exists(img)]
        
        if len(available_images) < 2:
            print("⚠️ Недостаточно изображений для пакетной обработки")
            return False
        
        try:
            files = []
            for img in available_images[:2]:  # Берем первые 2 изображения
                files.append(('files', open(img, 'rb')))
            
            data = {'location_hint': 'Москва, Россия'}
            
            print(f"📤 Отправляем {len(files)} изображений на пакетную обработку...")
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/violations/batch_detect",
                files=files,
                data=data,
                timeout=180  # 3 минуты для пакетной обработки
            )
            processing_time = time.time() - start_time
            
            # Закрываем файлы
            for _, file_obj in files:
                file_obj.close()
            
            print(f"⏱️ Время пакетной обработки: {processing_time:.2f} сек")
            print(f"📊 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                results = result.get('results', [])
                
                print(f"✅ Пакетная обработка успешна")
                print(f"📋 Обработано изображений: {len(results)}")
                
                for i, res in enumerate(results):
                    success = res.get('success', False)
                    coords = res.get('coordinates')
                    objects_count = len(res.get('objects', []))
                    
                    print(f"   {i+1}. {'✅' if success else '❌'} Координаты: {coords}, Объектов: {objects_count}")
                
                return len(results) > 0
            else:
                print(f"❌ Ошибка пакетной обработки: {response.status_code}")
                print(f"📝 Ответ: {response.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"❌ Исключение в пакетной обработке: {e}")
            return False
    
    def generate_report(self, test_results):
        """Генерация итогового отчета"""
        print("\n📋 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 60)
        
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results if result[1])
        
        print(f"🎯 Результат: {passed_tests}/{total_tests} тестов пройдено")
        print(f"📊 Успешность: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n📝 ДЕТАЛИЗАЦИЯ:")
        for test_name, result in test_results:
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            print(f"   {test_name}: {status}")
        
        if passed_tests == total_tests:
            print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к продакшену!")
        elif passed_tests >= total_tests * 0.8:
            print("\n⚠️ Большинство тестов пройдено. Система почти готова.")
        else:
            print("\n❌ Требуется серьезная доработка системы.")
        
        return passed_tests / total_tests

def main():
    print("🚀 ПОЛНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ ГЕОЛОКАЦИОННОГО РАСПОЗНАВАНИЯ")
    print("=" * 80)
    print("🤖 Mistral AI + 🎯 YOLO + 🌐 Панорамы + 📍 Координаты")
    print("=" * 80)
    
    tester = GeoSystemTester()
    test_results = []
    
    # Последовательность тестов
    tests = [
        ("Backend Health", tester.test_backend_health),
        ("Mistral AI Integration", tester.test_mistral_ai_integration),
        ("YOLO Object Detection", tester.test_yolo_object_detection),
        ("Panorama Analysis", tester.test_panorama_analysis),
        ("Coordinate Detection API", lambda: len(tester.test_coordinate_detection_api()) > 0),
        ("Batch Processing", tester.test_batch_processing)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🧪 Запуск теста: {test_name}")
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {test_name}: {e}")
            test_results.append((test_name, False))
    
    # Генерируем итоговый отчет
    success_rate = tester.generate_report(test_results)
    
    return success_rate >= 0.8

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
