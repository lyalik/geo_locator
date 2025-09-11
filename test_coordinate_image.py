#!/usr/bin/env python3
"""
Тест загрузки изображения в раздел "Анализ координат"
"""
import requests
import os

BASE_URL = "http://localhost:5001"

def test_coordinate_detection_with_real_image():
    """Тест coordinate detection с реальным изображением"""
    print("🖼️ Тестирование загрузки изображения в 'Анализ координат'")
    print("=" * 60)
    
    # Путь к тестовому изображению
    test_image_path = "/home/denis/Documents/Hackathon_2025/geo_locator/backend/uploads/coordinates/1krasn_pl2-3797155958.jpg"
    
    if not os.path.exists(test_image_path):
        print("❌ Тестовое изображение не найдено")
        return
    
    print(f"📁 Найдено изображение: {os.path.basename(test_image_path)}")
    print(f"📏 Размер файла: {os.path.getsize(test_image_path)} байт")
    
    try:
        # Подготавливаем файл для загрузки
        with open(test_image_path, 'rb') as f:
            files = {'image': ('test_image.jpg', f, 'image/jpeg')}
            data = {
                'location_hint': '',
                'user_description': 'Тестовое изображение для анализа координат'
            }
            
            print("\n🚀 Отправляем запрос на /api/coordinates/detect...")
            
            response = requests.post(
                f"{BASE_URL}/api/coordinates/detect",
                files=files,
                data=data,
                timeout=60
            )
            
            print(f"📊 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Запрос выполнен успешно!")
                
                # Анализируем результат
                print(f"\n📋 Результаты анализа:")
                print(f"   Success: {result.get('success', 'unknown')}")
                print(f"   Message: {result.get('message', 'no message')}")
                
                # Проверяем координаты
                coordinates = result.get('coordinates')
                if coordinates:
                    print(f"   📍 Координаты найдены: {coordinates}")
                else:
                    print(f"   📍 Координаты: не определены")
                
                # Проверяем детекцию объектов
                objects = result.get('detected_objects', [])
                print(f"   🎯 Обнаружено объектов: {len(objects)}")
                
                # Проверяем источники данных
                sources = result.get('sources_used', [])
                print(f"   📡 Использованные источники: {', '.join(sources) if sources else 'нет'}")
                
                # Проверяем рекомендации
                recommendations = result.get('recommendations', [])
                if recommendations:
                    print(f"\n💡 Рекомендации:")
                    for i, rec in enumerate(recommendations, 1):
                        print(f"   {i}. {rec}")
                
                # Проверяем спутниковые данные
                satellite_data = result.get('satellite_data')
                if satellite_data:
                    print(f"\n🛰️ Спутниковые данные:")
                    print(f"   Источник: {satellite_data.get('source', 'unknown')}")
                    print(f"   Изображение: {'найдено' if satellite_data.get('image_url') else 'не найдено'}")
                
            else:
                print(f"❌ Ошибка HTTP: {response.status_code}")
                print(f"Ответ: {response.text}")
                
    except Exception as e:
        print(f"❌ Ошибка при отправке запроса: {e}")

def test_coordinate_api_health():
    """Проверка доступности coordinate API"""
    print("\n🏥 Проверка доступности coordinate API:")
    
    try:
        response = requests.options(f"{BASE_URL}/api/coordinates/detect", timeout=10)
        print(f"   OPTIONS запрос: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ API endpoint доступен")
        else:
            print("   ❌ API endpoint недоступен")
            
    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")

if __name__ == "__main__":
    test_coordinate_api_health()
    test_coordinate_detection_with_real_image()
    
    print("\n" + "=" * 60)
    print("✅ Тестирование завершено")
