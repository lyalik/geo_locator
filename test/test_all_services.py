#!/usr/bin/env python3
"""
Комплексная диагностика всех сервисов системы геолокации
"""
import sys
import os
sys.path.append('/home/denis/Documents/Hackathon_2025/geo_locator/backend')

from services.yandex_maps_service import YandexMapsService
from services.dgis_service import DGISService
from services.openstreetmap_service import OpenStreetMapService
from services.geo_aggregator_service import GeoAggregatorService
from services.coordinate_detector import CoordinateDetector
from services.archive_photo_service import ArchivePhotoService
from services.roscosmos_satellite_service import RoscosmosService
from services.yandex_satellite_service import YandexSatelliteService

def test_yandex_service():
    """Тест Yandex Maps сервиса"""
    print("🗺️ YANDEX MAPS SERVICE")
    print("-" * 40)
    
    try:
        service = YandexMapsService()
        print(f"   ✅ Сервис инициализирован")
        print(f"   🔑 API ключ: {'установлен' if service.api_key else 'НЕ УСТАНОВЛЕН'}")
        
        # Тест geocode
        result = service.geocode("Красная площадь, Москва")
        print(f"   🏛️ Geocode тест: {'✅ успешно' if result.get('success') else '❌ ошибка'}")
        if result.get('success'):
            print(f"      Координаты: {result.get('coordinates')}")
        
        # Тест search_places
        places = service.search_places("достопримечательность", 55.7558, 37.6176)
        print(f"   🔍 Search places: {'✅ успешно' if places.get('success') else '❌ ошибка'}")
        print(f"      Найдено мест: {len(places.get('places', []))}")
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print()

def test_dgis_service():
    """Тест 2GIS сервиса"""
    print("🏢 2GIS SERVICE")
    print("-" * 40)
    
    try:
        service = DGISService()
        print(f"   ✅ Сервис инициализирован")
        print(f"   🔑 API ключ: {'установлен' if service.api_key else 'НЕ УСТАНОВЛЕН'}")
        
        # Тест search_places
        result = service.search_places("кафе", 55.7558, 37.6176)
        print(f"   🔍 Search places: {'✅ успешно' if result.get('success') else '❌ ошибка'}")
        if result.get('success'):
            print(f"      Найдено мест: {len(result.get('places', []))}")
        
        # Тест geocode
        geocode_result = service.geocode("Красная площадь, Москва")
        print(f"   🏛️ Geocode тест: {'✅ успешно' if geocode_result.get('success') else '❌ ошибка'}")
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print()

def test_osm_service():
    """Тест OpenStreetMap сервиса"""
    print("🌍 OSM SERVICE")
    print("-" * 40)
    
    try:
        service = OpenStreetMapService()
        print(f"   ✅ Сервис инициализирован")
        
        # Тест geocode
        result = service.geocode("Красная площадь, Москва")
        print(f"   🏛️ Geocode тест: {'✅ успешно' if result.get('success') else '❌ ошибка'}")
        if result.get('success'):
            print(f"      Координаты: {result.get('coordinates')}")
        
        # Тест поиска зданий
        buildings = service.get_buildings_in_area(55.7558, 37.6176, 1000)
        print(f"   🏠 Buildings search: {'✅ успешно' if buildings.get('success') else '❌ ошибка'}")
        if buildings.get('success'):
            print(f"      Найдено зданий: {len(buildings.get('buildings', []))}")
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print()

def test_satellite_services():
    """Тест спутниковых сервисов"""
    print("🛰️ SATELLITE SERVICES")
    print("-" * 40)
    
    # Роскосмос
    try:
        roscosmos = RoscosmosService()
        print(f"   🇷🇺 Роскосмос: ✅ инициализирован")
        
        # Тест получения изображения
        result = roscosmos.get_satellite_image(55.7558, 37.6176, zoom=15)
        print(f"      Изображение: {'✅ получено' if result.get('success') else '❌ ошибка'}")
        
    except Exception as e:
        print(f"   🇷🇺 Роскосмос: ❌ {e}")
    
    # Яндекс Спутник
    try:
        yandex_sat = YandexSatelliteService()
        print(f"   🗺️ Яндекс Спутник: ✅ инициализирован")
        
        result = yandex_sat.get_satellite_image(55.7558, 37.6176, zoom=15)
        print(f"      Изображение: {'✅ получено' if result.get('success') else '❌ ошибка'}")
        
    except Exception as e:
        print(f"   🗺️ Яндекс Спутник: ❌ {e}")
    
    print()

def test_archive_service():
    """Тест архивного сервиса"""
    print("🏛️ ARCHIVE SERVICE")
    print("-" * 40)
    
    try:
        service = ArchivePhotoService()
        print(f"   ✅ Сервис инициализирован")
        
        # Проверяем наличие архивных данных
        archive_path = "/home/denis/Documents/Hackathon_2025/geo_locator/backend/data/archive_photos"
        if os.path.exists(archive_path):
            files = os.listdir(archive_path)
            print(f"   📁 Архивных файлов: {len(files)}")
        else:
            print(f"   📁 Архивная папка: не найдена")
        
        # Тест поиска похожих зданий (если есть тестовое изображение)
        test_image = "/home/denis/Documents/Hackathon_2025/geo_locator/backend/uploads/coordinates/1krasn_pl2-3797155958.jpg"
        if os.path.exists(test_image):
            result = service.find_similar_buildings(test_image)
            print(f"   🔍 Поиск похожих: {'✅ выполнен' if result else '❌ ошибка'}")
            if result:
                print(f"      Найдено совпадений: {len(result)}")
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print()

def test_geo_aggregator():
    """Тест агрегатора геолокации"""
    print("🌐 GEO AGGREGATOR SERVICE")
    print("-" * 40)
    
    try:
        service = GeoAggregatorService()
        print(f"   ✅ Сервис инициализирован")
        
        # Тест с изображением
        test_image = "/home/denis/Documents/Hackathon_2025/geo_locator/backend/uploads/coordinates/1krasn_pl2-3797155958.jpg"
        if os.path.exists(test_image):
            print(f"   📸 Тестируем с изображением...")
            
            # Тест с подсказкой местоположения
            result = service.locate_image(test_image, location_hint="Красная площадь")
            print(f"   🎯 С подсказкой: {'✅ успешно' if result.get('success') else '❌ ошибка'}")
            if result.get('success'):
                print(f"      Координаты: {result.get('final_location')}")
                print(f"      Уверенность: {result.get('confidence_score', 0):.2f}")
                print(f"      Источники: {', '.join(result.get('sources_used', []))}")
            
            # Тест без подсказки
            result_no_hint = service.locate_image(test_image)
            print(f"   🎲 Без подсказки: {'✅ успешно' if result_no_hint.get('success') else '❌ ошибка'}")
            
        else:
            print(f"   📸 Тестовое изображение не найдено")
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print()

def test_coordinate_detector():
    """Тест детектора координат"""
    print("📍 COORDINATE DETECTOR")
    print("-" * 40)
    
    try:
        service = CoordinateDetector()
        print(f"   ✅ Сервис инициализирован")
        
        # Тест с изображением
        test_image = "/home/denis/Documents/Hackathon_2025/geo_locator/backend/uploads/coordinates/1krasn_pl2-3797155958.jpg"
        if os.path.exists(test_image):
            print(f"   📸 Анализируем изображение...")
            
            result = service.detect_coordinates_from_image(
                image_path=test_image,
                location_hint="Москва"
            )
            
            print(f"   🎯 Детекция: {'✅ успешно' if result.get('success') else '❌ ошибка'}")
            print(f"   📊 Сообщение: {result.get('message', 'нет')}")
            print(f"   📍 Координаты: {result.get('coordinates', 'не найдены')}")
            print(f"   🎯 Объектов: {len(result.get('detected_objects', []))}")
            print(f"   🛰️ Спутниковые данные: {'есть' if result.get('satellite_data') else 'нет'}")
            
        else:
            print(f"   📸 Тестовое изображение не найдено")
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print()

def main():
    """Запуск всех тестов"""
    print("🔍 КОМПЛЕКСНАЯ ДИАГНОСТИКА СЕРВИСОВ")
    print("=" * 60)
    print()
    
    # Тестируем все сервисы
    test_yandex_service()
    test_dgis_service() 
    test_osm_service()
    test_satellite_services()
    test_archive_service()
    test_geo_aggregator()
    test_coordinate_detector()
    
    print("=" * 60)
    print("✅ Диагностика завершена")

if __name__ == "__main__":
    main()
