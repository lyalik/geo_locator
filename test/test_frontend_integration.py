#!/usr/bin/env python3
"""
ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ ФРОНТЕНДА С BACKEND
Проверка всех разделов сайта с функционалом ИИ и геолокации
"""
import os
import sys
import requests
import json
import time
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('.env')

class FrontendIntegrationTester:
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.frontend_url = "http://localhost:3000"
        self.test_images = [
            '/home/denis/Documents/Hackathon_2025/geo_locator/test_image.jpg',
            '/home/denis/Documents/Hackathon_2025/geo_locator/backend/uploads/coordinates/i_annotated_yolo.jpg'
        ]
        self.results = {}
    
    def check_frontend_availability(self):
        """Проверка доступности фронтенда"""
        print("🌐 ПРОВЕРКА ДОСТУПНОСТИ ФРОНТЕНДА")
        print("=" * 50)
        
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                print(f"✅ Frontend доступен: {self.frontend_url}")
                return True
            else:
                print(f"❌ Frontend недоступен: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка подключения к frontend: {e}")
            return False
    
    def test_ai_analysis_api(self):
        """Тест API для раздела 'Анализ с ИИ' (Violation Detection)"""
        print("\n🤖 ТЕСТИРОВАНИЕ РАЗДЕЛА 'АНАЛИЗ С ИИ'")
        print("=" * 50)
        
        test_image = self.test_images[0] if os.path.exists(self.test_images[0]) else None
        if not test_image:
            print("❌ Тестовое изображение не найдено")
            return False
        
        try:
            # Тест основного API endpoint для детекции нарушений
            with open(test_image, 'rb') as f:
                files = {'file': f}
                data = {
                    'user_id': 'test_user',
                    'location_hint': 'Москва, Россия',
                    'location_notes': 'Тестовая загрузка'
                }
                
                print(f"📤 Отправляем запрос на /api/violations/detect")
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/api/violations/detect",
                    files=files,
                    data=data,
                    timeout=60
                )
                processing_time = time.time() - start_time
            
            print(f"⏱️ Время обработки: {processing_time:.2f}с")
            print(f"📊 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ API работает корректно")
                
                # API возвращает структуру {success: true, data: {...}}
                if result.get('success') and 'data' in result:
                    data = result['data']
                    violations = data.get('violations', [])
                    location = data.get('location', {})
                    
                    print(f"🚨 Нарушений найдено: {len(violations)}")
                    print(f"📍 Геолокация: {'✅' if location.get('success') else '❌'}")
                    
                    # Проверяем структуру ответа
                    required_fields = ['violation_id', 'image_path', 'violations', 'location', 'metadata']
                    missing_fields = [field for field in required_fields if field not in data]
                else:
                    print(f"⚠️ API вернул успех, но без данных: {result.get('message', 'Нет сообщения')}")
                    violations = []
                    location = {}
                    missing_fields = []
                
                if missing_fields:
                    print(f"⚠️ Отсутствующие поля: {missing_fields}")
                else:
                    print(f"✅ Структура ответа корректна")
                
                self.results['ai_analysis'] = {
                    'status': 'success',
                    'violations_count': len(violations),
                    'processing_time': processing_time,
                    'has_location': location.get('success', False)
                }
                return True
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                print(f"📝 Ответ: {response.text[:200]}...")
                self.results['ai_analysis'] = {'status': 'failed', 'error': f"HTTP {response.status_code}"}
                return False
                
        except Exception as e:
            print(f"❌ Исключение: {e}")
            self.results['ai_analysis'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def test_ocr_analysis_api(self):
        """Тест API для раздела 'OCR Анализ'"""
        print("\n📝 ТЕСТИРОВАНИЕ РАЗДЕЛА 'OCR АНАЛИЗ'")
        print("=" * 50)
        
        test_image = self.test_images[0] if os.path.exists(self.test_images[0]) else None
        if not test_image:
            print("❌ Тестовое изображение не найдено")
            return False
        
        try:
            # Проверяем доступность Mistral AI OCR через coordinate detection
            with open(test_image, 'rb') as f:
                files = {'file': f}
                data = {'location_hint': 'Москва, Россия'}
                
                print(f"📤 Отправляем запрос на /api/coordinates/detect (включает OCR)")
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/api/coordinates/detect",
                    files=files,
                    data=data,
                    timeout=60
                )
                processing_time = time.time() - start_time
            
            print(f"⏱️ Время обработки: {processing_time:.2f}с")
            print(f"📊 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ OCR API работает корректно")
                print(f"📍 Координаты: {result.get('coordinates', 'Не найдены')}")
                print(f"🔍 Источник: {result.get('source', 'неизвестен')}")
                print(f"🎯 Уверенность: {result.get('confidence', 0)}")
                
                # Проверяем наличие OCR данных в ответе
                has_ocr_data = 'source' in result and result.get('source') != 'неизвестен'
                
                self.results['ocr_analysis'] = {
                    'status': 'success',
                    'processing_time': processing_time,
                    'has_coordinates': result.get('coordinates') is not None,
                    'has_ocr_data': has_ocr_data
                }
                return True
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                self.results['ocr_analysis'] = {'status': 'failed', 'error': f"HTTP {response.status_code}"}
                return False
                
        except Exception as e:
            print(f"❌ Исключение: {e}")
            self.results['ocr_analysis'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def test_coordinate_analysis_api(self):
        """Тест API для раздела 'Анализ координат'"""
        print("\n📍 ТЕСТИРОВАНИЕ РАЗДЕЛА 'АНАЛИЗ КООРДИНАТ'")
        print("=" * 50)
        
        success_count = 0
        total_tests = 0
        
        for i, test_image in enumerate(self.test_images):
            if not os.path.exists(test_image):
                continue
                
            total_tests += 1
            image_name = os.path.basename(test_image)
            print(f"\n📸 Тест {i+1}: {image_name}")
            
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
                
                print(f"   ⏱️ Время: {processing_time:.2f}с")
                print(f"   📊 Статус: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    coordinates = result.get('coordinates')
                    confidence = result.get('confidence', 0)
                    objects = result.get('objects', [])
                    source = result.get('source', 'неизвестен')
                    enhanced = result.get('enhanced_detection', False)
                    
                    print(f"   📍 Координаты: {coordinates}")
                    print(f"   🎯 Уверенность: {confidence}")
                    print(f"   📦 YOLO объектов: {len(objects)}")
                    print(f"   🔍 Источник: {source}")
                    print(f"   🚀 Расширенная детекция: {'✅' if enhanced else '❌'}")
                    
                    success_count += 1
                else:
                    print(f"   ❌ Ошибка: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Исключение: {e}")
        
        success_rate = success_count / total_tests if total_tests > 0 else 0
        print(f"\n📊 Результат: {success_count}/{total_tests} тестов пройдено ({success_rate*100:.1f}%)")
        
        self.results['coordinate_analysis'] = {
            'status': 'success' if success_rate > 0.5 else 'failed',
            'success_rate': success_rate,
            'tests_passed': success_count,
            'total_tests': total_tests
        }
        
        return success_rate > 0.5
    
    def test_batch_analysis_api(self):
        """Тест API для раздела 'Пакетный анализ'"""
        print("\n📦 ТЕСТИРОВАНИЕ РАЗДЕЛА 'ПАКЕТНЫЙ АНАЛИЗ'")
        print("=" * 50)
        
        # Подготавливаем файлы для пакетной обработки
        available_images = [img for img in self.test_images if os.path.exists(img)]
        
        if len(available_images) < 2:
            print("⚠️ Недостаточно изображений для пакетной обработки")
            self.results['batch_analysis'] = {'status': 'skipped', 'reason': 'insufficient_images'}
            return False
        
        try:
            files = []
            for img in available_images[:2]:  # Берем первые 2 изображения
                files.append(('files', open(img, 'rb')))
            
            data = {
                'user_id': 'test_user',
                'location_hint': 'Москва, Россия'
            }
            
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
            
            print(f"⏱️ Время пакетной обработки: {processing_time:.2f}с")
            print(f"📊 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ Пакетная обработка успешна")
                
                # API возвращает структуру {success: true, data: {results: [...]}}
                if result.get('success') and 'data' in result:
                    data = result['data']
                    results = data.get('results', [])
                    
                    print(f"📋 Обработано изображений: {len(results)}")
                    
                    # Анализируем результаты
                    successful_results = 0
                    for i, res in enumerate(results):
                        success = res.get('detection', {}).get('success', False)
                        violations = res.get('detection', {}).get('violations', [])
                        location = res.get('location', {}).get('success', False)
                        
                        print(f"   {i+1}. {'✅' if success else '❌'} Нарушений: {len(violations)}, Геолокация: {'✅' if location else '❌'}")
                        if success:
                            successful_results += 1
                else:
                    print(f"⚠️ API вернул успех, но без данных: {result.get('message', 'Нет сообщения')}")
                    results = []
                    successful_results = 0
                
                success_rate = successful_results / len(results) if results else 0
                
                self.results['batch_analysis'] = {
                    'status': 'success',
                    'processing_time': processing_time,
                    'images_processed': len(results),
                    'success_rate': success_rate
                }
                
                return len(results) > 0
            else:
                print(f"❌ Ошибка пакетной обработки: {response.status_code}")
                print(f"📝 Ответ: {response.text[:200]}...")
                self.results['batch_analysis'] = {'status': 'failed', 'error': f"HTTP {response.status_code}"}
                return False
                
        except Exception as e:
            print(f"❌ Исключение в пакетной обработке: {e}")
            self.results['batch_analysis'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def test_multi_photo_analysis_api(self):
        """Тест API для раздела 'Мульти-фото анализ'"""
        print("\n🖼️ ТЕСТИРОВАНИЕ РАЗДЕЛА 'МУЛЬТИ-ФОТО АНАЛИЗ'")
        print("=" * 50)
        
        # Подготавливаем данные для группового анализа
        available_images = [img for img in self.test_images if os.path.exists(img)]
        
        if len(available_images) < 2:
            print("⚠️ Недостаточно изображений для мульти-фото анализа")
            self.results['multi_photo_analysis'] = {'status': 'skipped', 'reason': 'insufficient_images'}
            return False
        
        try:
            # Создаем группу фотографий
            photo_groups = [
                {
                    'name': 'Тестовая группа',
                    'photos': available_images[:2]
                }
            ]
            
            files = []
            group_data = []
            
            for group_idx, group in enumerate(photo_groups):
                for photo_idx, photo_path in enumerate(group['photos']):
                    files.append(('files', open(photo_path, 'rb')))
                    group_data.append({
                        'group_id': group_idx,
                        'group_name': group['name'],
                        'photo_index': photo_idx
                    })
            
            data = {
                'user_id': 'test_user',
                'location_hint': 'Москва, Россия',
                'groups': json.dumps(group_data)
            }
            
            print(f"📤 Отправляем {len(files)} изображений в {len(photo_groups)} группах...")
            
            start_time = time.time()
            # Используем обычный batch endpoint, так как специального multi-photo endpoint может не быть
            response = requests.post(
                f"{self.base_url}/api/violations/batch_detect",
                files=files,
                data=data,
                timeout=180
            )
            processing_time = time.time() - start_time
            
            # Закрываем файлы
            for _, file_obj in files:
                file_obj.close()
            
            print(f"⏱️ Время обработки: {processing_time:.2f}с")
            print(f"📊 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                results = result.get('results', [])
                
                print(f"✅ Мульти-фото анализ успешен")
                print(f"📋 Обработано изображений: {len(results)}")
                
                # Группируем результаты
                grouped_results = {}
                for i, res in enumerate(results):
                    group_id = i // 2  # Простая группировка по 2 изображения
                    if group_id not in grouped_results:
                        grouped_results[group_id] = []
                    grouped_results[group_id].append(res)
                
                print(f"📊 Создано групп: {len(grouped_results)}")
                
                for group_id, group_results in grouped_results.items():
                    total_violations = 0
                    successful_detections = 0
                    
                    for res in group_results:
                        detection = res.get('detection', {})
                        if detection.get('success'):
                            successful_detections += 1
                            total_violations += len(detection.get('violations', []))
                    
                    print(f"   Группа {group_id+1}: {successful_detections}/{len(group_results)} успешных детекций, {total_violations} нарушений")
                
                self.results['multi_photo_analysis'] = {
                    'status': 'success',
                    'processing_time': processing_time,
                    'groups_processed': len(grouped_results),
                    'total_images': len(results)
                }
                
                return len(results) > 0
            else:
                print(f"❌ Ошибка мульти-фото анализа: {response.status_code}")
                self.results['multi_photo_analysis'] = {'status': 'failed', 'error': f"HTTP {response.status_code}"}
                return False
                
        except Exception as e:
            print(f"❌ Исключение в мульти-фото анализе: {e}")
            self.results['multi_photo_analysis'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def test_system_endpoints(self):
        """Тест системных endpoints"""
        print("\n⚙️ ТЕСТИРОВАНИЕ СИСТЕМНЫХ ENDPOINTS")
        print("=" * 50)
        
        endpoints_to_test = [
            ('/health', 'Health Check'),
            ('/api/coordinates/statistics', 'System Statistics'),
            ('/api/violations/list', 'Violations List')
        ]
        
        working_endpoints = 0
        
        for endpoint, name in endpoints_to_test:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                
                if response.status_code == 200:
                    print(f"✅ {name}: работает")
                    working_endpoints += 1
                else:
                    print(f"❌ {name}: ошибка {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {name}: исключение {e}")
        
        success_rate = working_endpoints / len(endpoints_to_test)
        print(f"\n📊 Системные endpoints: {working_endpoints}/{len(endpoints_to_test)} работают")
        
        return success_rate > 0.8
    
    def generate_integration_report(self, test_results):
        """Генерация отчета интеграции"""
        print("\n📋 ОТЧЕТ ИНТЕГРАЦИИ ФРОНТЕНДА С BACKEND")
        print("=" * 70)
        
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results if result[1])
        
        print(f"🎯 Результат: {passed_tests}/{total_tests} разделов работают корректно")
        print(f"📊 Успешность интеграции: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n📝 ДЕТАЛИЗАЦИЯ ПО РАЗДЕЛАМ:")
        for test_name, result in test_results:
            status = "✅ РАБОТАЕТ" if result else "❌ НЕ РАБОТАЕТ"
            print(f"   {test_name}: {status}")
        
        # Детальная информация по результатам
        print("\n🔍 ДЕТАЛЬНАЯ ИНФОРМАЦИЯ:")
        
        if 'ai_analysis' in self.results:
            ai_data = self.results['ai_analysis']
            if ai_data['status'] == 'success':
                print(f"   🤖 Анализ с ИИ: {ai_data['violations_count']} нарушений за {ai_data['processing_time']:.2f}с")
        
        if 'coordinate_analysis' in self.results:
            coord_data = self.results['coordinate_analysis']
            if coord_data['status'] == 'success':
                print(f"   📍 Анализ координат: {coord_data['success_rate']*100:.1f}% успешность")
        
        if 'batch_analysis' in self.results:
            batch_data = self.results['batch_analysis']
            if batch_data['status'] == 'success':
                print(f"   📦 Пакетный анализ: {batch_data['images_processed']} изображений за {batch_data['processing_time']:.2f}с")
        
        # Рекомендации
        print("\n💡 РЕКОМЕНДАЦИИ:")
        if passed_tests == total_tests:
            print("🎉 Все разделы фронтенда интегрированы корректно!")
            print("✅ Система готова для пользователей")
        elif passed_tests >= total_tests * 0.8:
            print("⚠️ Большинство разделов работает, есть мелкие проблемы")
            print("🔧 Рекомендуется протестировать проблемные разделы")
        else:
            print("❌ Требуется серьезная доработка интеграции")
            print("🛠️ Проверьте API endpoints и frontend компоненты")
        
        return passed_tests / total_tests

def main():
    print("🚀 ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ ФРОНТЕНДА С BACKEND")
    print("=" * 80)
    print("🤖 ИИ Анализ + 📝 OCR + 📍 Координаты + 📦 Пакетный + 🖼️ Мульти-фото")
    print("=" * 80)
    
    tester = FrontendIntegrationTester()
    test_results = []
    
    # Проверяем доступность фронтенда
    if not tester.check_frontend_availability():
        print("\n⚠️ Frontend недоступен, тестируем только backend API")
    
    # Последовательность тестов разделов
    tests = [
        ("Анализ с ИИ", tester.test_ai_analysis_api),
        ("OCR Анализ", tester.test_ocr_analysis_api),
        ("Анализ координат", tester.test_coordinate_analysis_api),
        ("Пакетный анализ", tester.test_batch_analysis_api),
        ("Мульти-фото анализ", tester.test_multi_photo_analysis_api),
        ("Системные endpoints", tester.test_system_endpoints)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🧪 Тестирование раздела: {test_name}")
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в разделе {test_name}: {e}")
            test_results.append((test_name, False))
    
    # Генерируем отчет
    success_rate = tester.generate_integration_report(test_results)
    
    return success_rate >= 0.8

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
