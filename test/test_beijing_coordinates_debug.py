#!/usr/bin/env python3
"""
Тест для диагностики проблемы с Beijing координатами
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import logging
from services.enhanced_coordinate_detector import EnhancedCoordinateDetector
from services.coordinate_detector import CoordinateDetector
from services.video_coordinate_detector import VideoCoordinateDetector

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_beijing_coordinates_detection():
    """Тест детекции Beijing координат"""
    print("🔍 ДИАГНОСТИКА BEIJING КООРДИНАТ")
    print("=" * 50)
    
    try:
        # Инициализация детектора
        detector = EnhancedCoordinateDetector()
        
        # Тестовые Beijing координаты
        beijing_coords = [
            {'latitude': 39.903573, 'longitude': 116.336536},  # Точные координаты из проблемы
            {'latitude': 39.9042, 'longitude': 116.4074},      # Координаты из кода
            {'latitude': 39.9, 'longitude': 116.3},            # Приблизительные
        ]
        
        print("1. Тест валидации Beijing координат:")
        for i, coords in enumerate(beijing_coords, 1):
            is_valid = detector._validate_coordinates(coords, "")
            print(f"   Координаты {i}: {coords}")
            print(f"   Валидны: {'❌ НЕТ' if not is_valid else '✅ ДА'}")
            print()
        
        # Тест умных fallback координат
        print("2. Тест умных fallback координат:")
        fallback_result = detector.get_smart_fallback_coordinates("Москва")
        print(f"   Результат для 'Москва': {fallback_result}")
        
        fallback_result_empty = detector.get_smart_fallback_coordinates("")
        print(f"   Результат для пустой подсказки: {fallback_result_empty}")
        
        # Тест региональных дефолтов
        print("3. Региональные дефолты:")
        print(f"   Россия: {detector.regional_defaults.get('russia', 'НЕ НАЙДЕНО')}")
        print(f"   Европа: {detector.regional_defaults.get('europe', 'НЕ НАЙДЕНО')}")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()

def test_coordinate_sources():
    """Тест источников координат"""
    print("\n🗺️ ТЕСТ ИСТОЧНИКОВ КООРДИНАТ")
    print("=" * 50)
    
    try:
        detector = CoordinateDetector()
        
        # Проверяем доступные источники
        print("Доступные источники координат:")
        if hasattr(detector, 'yandex_service'):
            print("   ✅ Yandex Maps")
        if hasattr(detector, 'dgis_service'):
            print("   ✅ 2GIS")
        if hasattr(detector, 'google_vision'):
            print("   ✅ Google Vision")
        if hasattr(detector, 'geo_aggregator'):
            print("   ✅ Geo Aggregator")
            
        # Тест с тестовым изображением
        test_image_path = "backend/uploads/coordinates/1krasn_pl2-3797155958.jpg"
        if os.path.exists(test_image_path):
            print(f"\n📸 Тест с изображением: {test_image_path}")
            result = detector.detect_coordinates_from_image(test_image_path, location_hint="Краснодар")
            
            if result.get('success'):
                coords = result.get('coordinates', {})
                print(f"   Результат: {coords}")
                
                # Проверяем, не Beijing ли это
                if coords:
                    lat, lon = coords.get('latitude', 0), coords.get('longitude', 0)
                    is_beijing = abs(lat - 39.9042) < 0.1 and abs(lon - 116.4074) < 0.1
                    print(f"   Beijing координаты: {'❌ ДА' if is_beijing else '✅ НЕТ'}")
                    
                    # Показываем источники
                    sources = result.get('coordinate_sources', {})
                    print(f"   Источники: {sources}")
            else:
                print(f"   ❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")
        else:
            print(f"   ⚠️ Тестовое изображение не найдено: {test_image_path}")
            
    except Exception as e:
        print(f"❌ Ошибка в тесте источников: {e}")
        import traceback
        traceback.print_exc()

def test_video_analysis_timeout():
    """Тест таймаута видео анализа"""
    print("\n🎬 ТЕСТ ВИДЕО АНАЛИЗА")
    print("=" * 50)
    
    try:
        video_detector = VideoCoordinateDetector()
        print("✅ VideoCoordinateDetector инициализирован")
        
        # Проверяем доступные компоненты
        if hasattr(video_detector, 'yolo_detector'):
            print("   ✅ YOLO детектор доступен")
        if hasattr(video_detector, 'coordinate_detector'):
            print("   ✅ Coordinate детектор доступен")
            
        # Ищем тестовое видео
        video_paths = [
            "backend/uploads/videos/test_video.mp4",
            "backend/data/test_video.mp4",
            "test_video.mp4"
        ]
        
        test_video = None
        for path in video_paths:
            if os.path.exists(path):
                test_video = path
                break
                
        if test_video:
            print(f"📹 Найдено тестовое видео: {test_video}")
            print("   ⚠️ Запуск анализа может занять много времени...")
            
            # Анализ с минимальными параметрами для быстрого теста
            result = video_detector.analyze_video(
                test_video, 
                location_hint="Краснодар",
                frame_interval=30,  # Каждый 30-й кадр
                max_frames=3       # Максимум 3 кадра
            )
            
            print(f"   Результат: {result.get('success', False)}")
            if result.get('coordinates'):
                coords = result['coordinates']
                lat, lon = coords.get('latitude', 0), coords.get('longitude', 0)
                is_beijing = abs(lat - 39.9042) < 0.1 and abs(lon - 116.4074) < 0.1
                print(f"   Координаты: {coords}")
                print(f"   Beijing координаты: {'❌ ДА' if is_beijing else '✅ НЕТ'}")
        else:
            print("   ⚠️ Тестовое видео не найдено")
            
    except Exception as e:
        print(f"❌ Ошибка в тесте видео: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_beijing_coordinates_detection()
    test_coordinate_sources()
    test_video_analysis_timeout()
    
    print("\n" + "=" * 50)
    print("🏁 ДИАГНОСТИКА ЗАВЕРШЕНА")
