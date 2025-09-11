#!/usr/bin/env python3
"""
Тест Google сервисов для распознавания зданий и анализа координат
"""
import os
import sys
import logging
from pathlib import Path

# Добавляем путь к backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.coordinate_detector import CoordinateDetector
from services.google_vision_service import GoogleVisionService

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_google_services():
    """Тестирование Google сервисов"""
    print("🤖 ТЕСТИРОВАНИЕ GOOGLE СЕРВИСОВ")
    print("=" * 50)
    
    # Инициализация сервисов
    google_service = GoogleVisionService()
    coordinate_detector = CoordinateDetector()
    
    # Проверка доступности Google Vision
    print("\n1. Проверка Google Vision API:")
    if google_service.vision_client:
        print("   ✅ Google Vision клиент инициализирован")
    else:
        print("   ❌ Google Vision клиент недоступен")
        print("   💡 Проверьте GOOGLE_APPLICATION_CREDENTIALS")
    
    # Проверка доступности Google Gemini
    print("\n2. Проверка Google Gemini API:")
    if google_service.gemini_model:
        print("   ✅ Google Gemini модель инициализирована")
        print(f"   📋 Модель: {os.getenv('GEMINI_MODEL', 'не указана')}")
    else:
        print("   ❌ Google Gemini модель недоступна")
        print("   💡 Проверьте GOOGLE_API_KEY и региональные ограничения")
    
    return google_service, coordinate_detector

def test_coordinate_detection_with_image():
    """Тестирование определения координат с реальным изображением"""
    print("\n🗺️ ТЕСТИРОВАНИЕ ОПРЕДЕЛЕНИЯ КООРДИНАТ")
    print("=" * 50)
    
    # Поиск тестового изображения
    test_image_paths = [
        "/home/denis/Documents/Hackathon_2025/geo_locator/backend/uploads/coordinates/1krasn_pl2-3797155958.jpg",
        "/home/denis/Documents/Hackathon_2025/geo_locator/backend/data/archive_photos/red_square_1.jpg",
        "/home/denis/Documents/Hackathon_2025/geo_locator/backend/data/archive_photos/red_square_2.jpg"
    ]
    
    test_image = None
    for path in test_image_paths:
        if os.path.exists(path):
            test_image = path
            break
    
    if not test_image:
        print("❌ Тестовое изображение не найдено")
        return
    
    print(f"📁 Используем изображение: {test_image}")
    
    # Инициализация детектора
    coordinate_detector = CoordinateDetector()
    
    # Тест 1: Анализ без подсказки
    print("\n1. Анализ без подсказки о местоположении:")
    result_no_hint = coordinate_detector.detect_coordinates_from_image(test_image)
    
    if result_no_hint['success']:
        coords = result_no_hint.get('coordinates')
        if coords:
            print(f"   ✅ Координаты найдены: {coords['latitude']:.6f}, {coords['longitude']:.6f}")
            print(f"   📍 Источник: {coords.get('source', 'неизвестно')}")
            print(f"   🎯 Уверенность: {coords.get('confidence', 0):.2f}")
        else:
            print("   ⚠️ Координаты не найдены")
    else:
        print(f"   ❌ Ошибка: {result_no_hint.get('error', 'неизвестная ошибка')}")
    
    # Тест 2: Анализ с подсказкой "Москва"
    print("\n2. Анализ с подсказкой 'Москва':")
    result_moscow = coordinate_detector.detect_coordinates_from_image(test_image, "Москва")
    
    if result_moscow['success']:
        coords = result_moscow.get('coordinates')
        if coords:
            print(f"   ✅ Координаты найдены: {coords['latitude']:.6f}, {coords['longitude']:.6f}")
            print(f"   📍 Источник: {coords.get('source', 'неизвестно')}")
            print(f"   🎯 Уверенность: {coords.get('confidence', 0):.2f}")
            
            # Проверяем, что это действительно Москва
            lat, lon = coords['latitude'], coords['longitude']
            if 55.5 <= lat <= 56.0 and 37.0 <= lon <= 38.0:
                print("   ✅ Координаты соответствуют Москве")
            else:
                print("   ⚠️ Координаты НЕ соответствуют Москве")
        else:
            print("   ⚠️ Координаты не найдены")
    else:
        print(f"   ❌ Ошибка: {result_moscow.get('error', 'неизвестная ошибка')}")
    
    # Тест 3: Анализ с подсказкой "Красная площадь"
    print("\n3. Анализ с подсказкой 'Красная площадь':")
    result_red_square = coordinate_detector.detect_coordinates_from_image(test_image, "Красная площадь")
    
    if result_red_square['success']:
        coords = result_red_square.get('coordinates')
        if coords:
            print(f"   ✅ Координаты найдены: {coords['latitude']:.6f}, {coords['longitude']:.6f}")
            print(f"   📍 Источник: {coords.get('source', 'неизвестно')}")
            print(f"   🎯 Уверенность: {coords.get('confidence', 0):.2f}")
            
            # Проверяем, что это действительно Красная площадь
            lat, lon = coords['latitude'], coords['longitude']
            if 55.752 <= lat <= 55.756 and 37.617 <= lon <= 37.625:
                print("   ✅ Координаты соответствуют Красной площади")
            else:
                print("   ⚠️ Координаты НЕ соответствуют Красной площади")
        else:
            print("   ⚠️ Координаты не найдены")
    else:
        print(f"   ❌ Ошибка: {result_red_square.get('error', 'неизвестная ошибка')}")

def test_gemini_analysis():
    """Тестирование анализа изображения через Gemini"""
    print("\n🤖 ТЕСТИРОВАНИЕ GEMINI АНАЛИЗА")
    print("=" * 50)
    
    # Поиск тестового изображения
    test_image_paths = [
        "/home/denis/Documents/Hackathon_2025/geo_locator/backend/uploads/coordinates/1krasn_pl2-3797155958.jpg",
        "/home/denis/Documents/Hackathon_2025/geo_locator/backend/data/archive_photos/red_square_1.jpg"
    ]
    
    test_image = None
    for path in test_image_paths:
        if os.path.exists(path):
            test_image = path
            break
    
    if not test_image:
        print("❌ Тестовое изображение не найдено")
        return
    
    print(f"📁 Используем изображение: {test_image}")
    
    # Инициализация сервиса
    google_service = GoogleVisionService()
    
    if not google_service.gemini_model:
        print("❌ Gemini модель недоступна")
        return
    
    # Тест анализа изображения
    prompt = """Проанализируй изображение и определи:

1. Что за здание или место изображено?
2. Есть ли характерные архитектурные элементы (купола, башни, колонны)?
3. Видны ли надписи, вывески, названия?
4. Это известная достопримечательность?
5. В каком городе или стране это может находиться?

Ответь кратко и конкретно, назови место если узнаешь его."""
    
    try:
        result = google_service.analyze_image_with_gemini(test_image, prompt)
        
        if result.get('success'):
            analysis = result.get('analysis', '')
            print("✅ Анализ Gemini:")
            print(f"   {analysis}")
            
            # Проверяем, упоминается ли Красная площадь или Кремль
            analysis_lower = analysis.lower()
            if any(keyword in analysis_lower for keyword in ['красная площадь', 'кремль', 'спасская башня']):
                print("   ✅ Gemini правильно распознал достопримечательность")
            else:
                print("   ⚠️ Gemini не распознал конкретную достопримечательность")
        else:
            print(f"❌ Ошибка анализа: {result.get('error', 'неизвестная ошибка')}")
            
    except Exception as e:
        print(f"❌ Исключение при анализе: {str(e)}")

if __name__ == "__main__":
    print("🧪 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ КООРДИНАТ")
    print("=" * 60)
    
    # Проверка переменных окружения
    print("\n🔑 Проверка переменных окружения:")
    google_api_key = os.getenv('GOOGLE_API_KEY')
    google_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    gemini_model = os.getenv('GEMINI_MODEL')
    
    print(f"   GOOGLE_API_KEY: {'✅ установлен' if google_api_key else '❌ не установлен'}")
    print(f"   GOOGLE_APPLICATION_CREDENTIALS: {'✅ установлен' if google_creds else '❌ не установлен'}")
    print(f"   GEMINI_MODEL: {gemini_model or '❌ не установлен'}")
    
    # Запуск тестов
    test_google_services()
    test_coordinate_detection_with_image()
    test_gemini_analysis()
    
    print("\n" + "=" * 60)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
