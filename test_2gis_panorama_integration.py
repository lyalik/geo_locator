#!/usr/bin/env python3
"""
Тест интеграции 2GIS панорам в систему анализа координат
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.dgis_panorama_service import DGISPanoramaService
from backend.services.panorama_analyzer_service import PanoramaAnalyzer
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_dgis_panorama_service():
    """
    Тест сервиса 2GIS панорам
    """
    print("🔍 Testing 2GIS Panorama Service...")
    
    service = DGISPanoramaService()
    
    # Тестовые координаты (центр Москвы)
    test_coords = [
        (55.7558, 37.6176),  # Красная площадь
        (55.7522, 37.6156),  # ГУМ
        (59.9311, 30.3609),  # Дворцовая площадь, СПб
    ]
    
    for lat, lon in test_coords:
        print(f"\n📍 Testing coordinates: {lat}, {lon}")
        
        # Поиск панорам
        result = service.get_panorama_nearby(lat, lon, radius=200)
        
        if result['success']:
            panoramas = result.get('panoramas', [])
            print(f"✅ Found {len(panoramas)} 2GIS panoramas")
            
            for i, panorama in enumerate(panoramas[:2]):
                print(f"   Panorama {i+1}:")
                print(f"     ID: {panorama.get('id', 'N/A')}")
                print(f"     Name: {panorama.get('name', 'N/A')}")
                print(f"     Address: {panorama.get('address', 'N/A')}")
                print(f"     Distance: {panorama.get('distance', 0):.1f}m")
                print(f"     Photos: {len(panorama.get('photos', []))}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        # Поиск мест с фотографиями
        places_result = service.search_places_with_photos("кафе", lat, lon, radius=500)
        
        if places_result['success']:
            places = places_result.get('places', [])
            print(f"🏪 Found {len(places)} places with photos")
        else:
            print(f"❌ Places search error: {places_result.get('error', 'Unknown error')}")

def test_combined_panorama_analysis():
    """
    Тест объединенного анализа панорам (Yandex + 2GIS)
    """
    print("\n🔍 Testing Combined Panorama Analysis...")
    
    analyzer = PanoramaAnalyzer()
    
    # Тестовые координаты
    lat, lon = 55.7558, 37.6176  # Красная площадь
    
    # Создаем тестовое изображение (используем существующее)
    test_image = "test_image.jpg"
    if not os.path.exists(test_image):
        print(f"⚠️ Test image {test_image} not found, skipping analysis test")
        return
    
    print(f"📍 Analyzing location: {lat}, {lon}")
    
    result = analyzer.analyze_location_with_panoramas(
        target_image_path=test_image,
        lat=lat,
        lon=lon,
        search_radius=300
    )
    
    if result['success']:
        print("✅ Panorama analysis successful!")
        print(f"   Confidence: {result['confidence']:.3f}")
        print(f"   Source: {result.get('panorama_source', 'unknown')}")
        print(f"   Coordinates: {result['coordinates']['latitude']:.6f}, {result['coordinates']['longitude']:.6f}")
        print(f"   Panoramas analyzed: {result['panoramas_analyzed']}")
        print(f"   Total found: {result['total_panoramas_found']}")
        
        sources_used = result.get('sources_used', {})
        print(f"   Sources used:")
        print(f"     Yandex: {sources_used.get('yandex', 0)}")
        print(f"     2GIS: {sources_used.get('2gis', 0)}")
        
        analysis_details = result.get('analysis_details', {})
        print(f"   Analysis details:")
        print(f"     Target objects: {analysis_details.get('target_objects', 0)}")
        print(f"     Panorama objects: {analysis_details.get('panorama_objects', 0)}")
        print(f"     Similarity score: {analysis_details.get('similarity_score', 0):.3f}")
    else:
        print(f"❌ Analysis failed: {result.get('message', 'Unknown error')}")
        if 'sources_checked' in result:
            print(f"   Sources checked: {result['sources_checked']}")

def test_api_keys():
    """
    Проверка наличия API ключей
    """
    print("\n🔑 Checking API Keys...")
    
    yandex_key = os.getenv('YANDEX_API_KEY')
    dgis_key = os.getenv('DGIS_API_KEY')
    
    print(f"Yandex API Key: {'✅ Present' if yandex_key else '❌ Missing'}")
    print(f"2GIS API Key: {'✅ Present' if dgis_key else '❌ Missing'}")
    
    if not yandex_key:
        print("⚠️ Set YANDEX_API_KEY environment variable")
    if not dgis_key:
        print("⚠️ Set DGIS_API_KEY environment variable")

def main():
    """
    Основная функция тестирования
    """
    print("🚀 Starting 2GIS Panorama Integration Tests")
    print("=" * 50)
    
    try:
        # Проверка API ключей
        test_api_keys()
        
        # Тест сервиса 2GIS
        test_dgis_panorama_service()
        
        # Тест объединенного анализа
        test_combined_panorama_analysis()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"\n❌ Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
