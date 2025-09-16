#!/usr/bin/env python3
"""
Отладка YOLO детекции объектов
"""

import os
import sys
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_yolo_detection():
    """Тестирует YOLO детекцию напрямую"""
    print("🎯 ТЕСТИРОВАНИЕ YOLO ДЕТЕКЦИИ")
    print("=" * 40)
    
    try:
        from services.yolo_violation_detector import YOLOObjectDetector
        
        # Инициализируем детектор
        print("📦 Инициализация YOLO детектора...")
        yolo_detector = YOLOObjectDetector()
        print("✅ YOLO детектор инициализирован")
        
        # Найдем тестовое изображение
        test_image_path = None
        upload_dirs = [
            "backend/uploads/coordinates",
            "backend/data/archive_photos",
            "test_image.jpg"
        ]
        
        for upload_dir in upload_dirs:
            if os.path.exists(upload_dir):
                if os.path.isfile(upload_dir):
                    test_image_path = upload_dir
                    break
                else:
                    for file in os.listdir(upload_dir):
                        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                            test_image_path = os.path.join(upload_dir, file)
                            break
            if test_image_path:
                break
        
        if not test_image_path:
            print("❌ Тестовое изображение не найдено")
            return False
        
        print(f"📁 Используем изображение: {test_image_path}")
        
        # Тестируем детекцию
        print("🔍 Запуск детекции объектов...")
        result = yolo_detector.detect_objects(test_image_path)
        
        print(f"📊 Результат детекции:")
        print(f"   Успешно: {result.get('success', False)}")
        print(f"   Объектов найдено: {result.get('total_objects', 0)}")
        
        if result.get('success'):
            objects = result.get('objects', [])
            print(f"\n📦 ДЕТАЛИ ОБЪЕКТОВ:")
            
            if objects:
                for i, obj in enumerate(objects[:5]):  # Показываем первые 5
                    print(f"   {i+1}. {obj.get('category', 'неизвестно')}")
                    print(f"      Уверенность: {obj.get('confidence', 0):.3f}")
                    print(f"      Координаты: {obj.get('bbox', {})}")
            else:
                print("   ⚠️ Объекты не обнаружены")
                
                # Проверим модель и настройки
                model_info = result.get('model_info', {})
                print(f"\n🔧 ИНФОРМАЦИЯ О МОДЕЛИ:")
                print(f"   Тип модели: {model_info.get('model_type', 'неизвестно')}")
                print(f"   Порог уверенности: {model_info.get('confidence_threshold', 'неизвестно')}")
                print(f"   Устройство: {model_info.get('device', 'неизвестно')}")
                
                # Рекомендации
                print(f"\n💡 РЕКОМЕНДАЦИИ:")
                print("   1. Проверить качество изображения")
                print("   2. Снизить порог уверенности (сейчас 0.25)")
                print("   3. Проверить совместимость модели YOLOv8")
                print("   4. Убедиться что изображение содержит распознаваемые объекты")
            
            # Проверим аннотированное изображение
            annotated_path = result.get('annotated_image_path')
            if annotated_path and os.path.exists(annotated_path):
                print(f"\n🖼️ Аннотированное изображение создано: {annotated_path}")
            
            return len(objects) > 0
        else:
            error = result.get('error', 'неизвестная ошибка')
            print(f"❌ Ошибка детекции: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False

def test_yolo_model_info():
    """Проверяет информацию о YOLO модели"""
    print("\n🔧 ИНФОРМАЦИЯ О YOLO МОДЕЛИ")
    print("=" * 35)
    
    try:
        from services.yolo_violation_detector import YOLOObjectDetector
        import torch
        from ultralytics import YOLO
        
        print(f"🐍 Python: {sys.version}")
        print(f"🔥 PyTorch: {torch.__version__}")
        print(f"🎯 CUDA доступна: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"   GPU: {torch.cuda.get_device_name(0)}")
        
        # Проверим модель YOLO
        model_path = "yolov8n.pt"
        if os.path.exists(model_path):
            print(f"✅ Модель найдена: {model_path}")
            
            # Загрузим модель для проверки
            model = YOLO(model_path)
            print(f"✅ Модель загружена успешно")
            print(f"   Классы: {len(model.names)} категорий")
            print(f"   Первые 10 классов: {list(model.names.values())[:10]}")
        else:
            print(f"❌ Модель не найдена: {model_path}")
            print("   Модель будет загружена автоматически при первом запуске")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки модели: {e}")
        return False

def test_yolo_with_lower_threshold():
    """Тестирует YOLO с пониженным порогом уверенности"""
    print("\n🔻 ТЕСТ С ПОНИЖЕННЫМ ПОРОГОМ УВЕРЕННОСТИ")
    print("=" * 50)
    
    try:
        from services.yolo_violation_detector import YOLOObjectDetector
        
        # Создаем детектор с пониженным порогом
        yolo_detector = YOLOObjectDetector()
        
        # Временно снижаем порог
        original_threshold = yolo_detector.CONFIDENCE_THRESHOLD
        yolo_detector.CONFIDENCE_THRESHOLD = 0.1  # Очень низкий порог
        
        print(f"🔧 Порог уверенности снижен с {original_threshold} до {yolo_detector.CONFIDENCE_THRESHOLD}")
        
        # Найдем тестовое изображение
        test_image_path = None
        upload_dirs = ["backend/uploads/coordinates", "backend/data/archive_photos"]
        
        for upload_dir in upload_dirs:
            if os.path.exists(upload_dir):
                for file in os.listdir(upload_dir):
                    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        test_image_path = os.path.join(upload_dir, file)
                        break
            if test_image_path:
                break
        
        if not test_image_path:
            print("❌ Тестовое изображение не найдено")
            return False
        
        print(f"📁 Тестируем: {os.path.basename(test_image_path)}")
        
        # Тестируем с низким порогом
        result = yolo_detector.detect_objects(test_image_path)
        
        # Восстанавливаем исходный порог
        yolo_detector.CONFIDENCE_THRESHOLD = original_threshold
        
        print(f"📊 Результат с низким порогом:")
        print(f"   Объектов найдено: {result.get('total_objects', 0)}")
        
        if result.get('success') and result.get('objects'):
            objects = result.get('objects', [])
            print(f"\n📦 НАЙДЕННЫЕ ОБЪЕКТЫ:")
            for i, obj in enumerate(objects[:10]):
                print(f"   {i+1}. {obj.get('category', 'неизвестно')}: {obj.get('confidence', 0):.3f}")
            
            return True
        else:
            print("   ⚠️ Даже с низким порогом объекты не найдены")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка теста с низким порогом: {e}")
        return False

def main():
    """Основная функция отладки"""
    print("🚀 ОТЛАДКА YOLO ДЕТЕКЦИИ ОБЪЕКТОВ")
    print("=" * 50)
    
    tests = [
        ("Информация о модели", test_yolo_model_info),
        ("Стандартная детекция", test_yolo_detection),
        ("Детекция с низким порогом", test_yolo_with_lower_threshold)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в '{test_name}': {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("📋 ОТЧЕТ ПО ОТЛАДКЕ YOLO:")
    
    for test_name, result in results:
        status = "✅ УСПЕШНО" if result else "❌ ОШИБКА"
        print(f"   {test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    print(f"\n🎯 Результат: {passed}/{len(results)} тестов прошли успешно")
    
    if passed < len(results):
        print(f"\n💡 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
        print("1. Убедитесь что модель yolov8n.pt загружена")
        print("2. Проверьте качество тестовых изображений")
        print("3. Рассмотрите использование другой предобученной модели")
        print("4. Проверьте совместимость версий ultralytics и torch")

if __name__ == "__main__":
    main()
