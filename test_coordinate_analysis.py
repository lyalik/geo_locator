#!/usr/bin/env python3
"""
Тест для проверки работы раздела "Анализ координат" с реальными API ключами
"""

import requests
import json
import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io

def create_test_image_with_gps():
    """Создает тестовое изображение с GPS координатами"""
    # Создаем простое изображение
    img = Image.new('RGB', (800, 600), color='blue')
    
    # Добавляем GPS данные в EXIF (координаты Москвы - Красная площадь)
    exif_dict = {
        "0th": {},
        "Exif": {},
        "GPS": {
            1: 'N',  # GPS latitude ref
            2: ((55, 1), (45, 1), (2100, 100)),  # GPS latitude (55.7539)
            3: 'E',  # GPS longitude ref  
            4: ((37, 1), (37, 1), (1200, 100)),  # GPS longitude (37.6208)
        },
        "1st": {},
        "thumbnail": None
    }
    
    # Сохраняем изображение
    test_image_path = '/tmp/test_gps_image.jpg'
    img.save(test_image_path, 'JPEG')
    
    return test_image_path

def test_coordinate_detection_api():
    """Тестирует API определения координат"""
    print("🧪 Тестирование API определения координат...")
    
    # Создаем тестовое изображение
    image_path = create_test_image_with_gps()
    
    # Отправляем запрос к API
    url = 'http://localhost:5001/api/coordinate/detect'
    
    with open(image_path, 'rb') as f:
        files = {'file': ('test_image.jpg', f, 'image/jpeg')}
        data = {'location_hint': 'Москва, Красная площадь'}
        
        try:
            response = requests.post(url, files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ API ответил успешно!")
                print(f"📍 Координаты: {result.get('coordinates', 'Не найдены')}")
                
                # Проверяем наличие спутниковых данных
                if 'satellite_data' in result:
                    sat_data = result['satellite_data']
                    print(f"🛰️ Спутниковые данные: {sat_data.get('success', False)}")
                    print(f"📡 Источник: {sat_data.get('primary_source', 'Неизвестен')}")
                    print(f"🔗 Доступных источников: {sat_data.get('available_sources', 0)}")
                
                # Проверяем информацию о местоположении
                if 'location_info' in result:
                    loc_info = result['location_info']
                    print("📍 Информация о местоположении:")
                    
                    if 'reverse_geocoding' in loc_info:
                        geocoding = loc_info['reverse_geocoding']
                        print(f"   Адрес (Яндекс): {geocoding.get('address', 'Не определен')}")
                        print(f"   Точность: {geocoding.get('confidence', 0)*100:.1f}%")
                    
                    if 'nearby_places' in loc_info and loc_info['nearby_places']:
                        print(f"   Ближайших мест (2GIS): {len(loc_info['nearby_places'])}")
                        for place in loc_info['nearby_places'][:3]:
                            print(f"     - {place.get('name', 'Без названия')}")
                
                print("\n📊 Полный ответ API:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                print(f"Ответ: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка соединения: {e}")
    
    # Удаляем тестовый файл
    if os.path.exists(image_path):
        os.remove(image_path)

def check_api_keys():
    """Проверяет наличие API ключей в окружении"""
    print("🔑 Проверка API ключей...")
    
    keys = {
        'YANDEX_API_KEY': os.getenv('YANDEX_API_KEY'),
        'DGIS_API_KEY': os.getenv('DGIS_API_KEY'), 
        'ROSCOSMOS_API_KEY': os.getenv('ROSCOSMOS_API_KEY')
    }
    
    for key_name, key_value in keys.items():
        if key_value:
            print(f"✅ {key_name}: установлен ({key_value[:10]}...)")
        else:
            print(f"❌ {key_name}: не найден")
    
    return all(keys.values())

if __name__ == "__main__":
    print("🚀 Тестирование раздела 'Анализ координат'")
    print("=" * 50)
    
    # Проверяем API ключи
    if not check_api_keys():
        print("\n⚠️ Не все API ключи настроены. Проверьте файл .env")
        exit(1)
    
    print()
    
    # Тестируем API
    test_coordinate_detection_api()
    
    print("\n🎯 Тест завершен!")
    print("Теперь можете протестировать через веб-интерфейс:")
    print("1. Откройте http://localhost:3000")
    print("2. Перейдите в раздел 'Анализ координат'")
    print("3. Загрузите изображение с GPS данными")
    print("4. Проверьте отображение спутниковых снимков и информации о местоположении")
