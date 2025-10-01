#!/usr/bin/env python3
"""
Тестовый скрипт для отладки загрузки файлов в coordinate API
"""

import requests
import os
import sys

def test_image_upload():
    """Тест загрузки изображения"""
    print("🔍 Testing image upload to coordinate detection API...")
    
    # Создаем тестовое изображение если его нет
    test_image_path = "test_image.jpg"
    if not os.path.exists(test_image_path):
        # Создаем простое тестовое изображение
        from PIL import Image
        import io
        
        # Создаем простое изображение 100x100 пикселей
        img = Image.new('RGB', (100, 100), color='red')
        img.save(test_image_path, 'JPEG')
        print(f"✅ Created test image: {test_image_path}")
    
    # Отправляем запрос
    url = "http://localhost:5001/api/coordinates/detect"
    
    try:
        with open(test_image_path, 'rb') as f:
            files = {'file': (test_image_path, f, 'image/jpeg')}
            data = {'location_hint': 'Москва'}
            
            print(f"📤 Sending POST request to {url}")
            print(f"📤 Files: {list(files.keys())}")
            print(f"📤 Data: {data}")
            
            response = requests.post(url, files=files, data=data, timeout=30)
            
            print(f"📥 Response status: {response.status_code}")
            print(f"📥 Response headers: {dict(response.headers)}")
            print(f"📥 Response body: {response.text}")
            
            if response.status_code == 200:
                print("✅ Image upload successful!")
                return True
            else:
                print(f"❌ Image upload failed with status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error during image upload: {e}")
        return False

def test_video_upload():
    """Тест загрузки видео"""
    print("\n🔍 Testing video upload to coordinate analysis API...")
    
    # Создаем тестовое видео если его нет
    test_video_path = "test_video.mp4"
    if not os.path.exists(test_video_path):
        print(f"⚠️ Test video {test_video_path} not found. Skipping video test.")
        return True
    
    # Отправляем запрос
    url = "http://localhost:5001/api/coordinates/video/analyze"
    
    try:
        with open(test_video_path, 'rb') as f:
            files = {'file': (test_video_path, f, 'video/mp4')}
            data = {
                'location_hint': 'Москва',
                'frame_interval': '30',
                'max_frames': '5'
            }
            
            print(f"📤 Sending POST request to {url}")
            print(f"📤 Files: {list(files.keys())}")
            print(f"📤 Data: {data}")
            
            response = requests.post(url, files=files, data=data, timeout=60)
            
            print(f"📥 Response status: {response.status_code}")
            print(f"📥 Response headers: {dict(response.headers)}")
            print(f"📥 Response body: {response.text}")
            
            if response.status_code == 200:
                print("✅ Video upload successful!")
                return True
            else:
                print(f"❌ Video upload failed with status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error during video upload: {e}")
        return False

def main():
    print("🚀 Starting file upload debug tests...")
    print("=" * 50)
    
    # Проверяем доступность backend
    try:
        response = requests.get("http://localhost:5001/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is accessible")
        else:
            print(f"⚠️ Backend responded with status {response.status_code}")
    except Exception as e:
        print(f"❌ Backend is not accessible: {e}")
        sys.exit(1)
    
    # Тестируем загрузку изображения
    image_success = test_image_upload()
    
    # Тестируем загрузку видео
    video_success = test_video_upload()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"  Image upload: {'✅ SUCCESS' if image_success else '❌ FAILED'}")
    print(f"  Video upload: {'✅ SUCCESS' if video_success else '❌ FAILED'}")
    
    if image_success:
        print("\n🎉 File upload is working correctly!")
    else:
        print("\n❌ File upload issues detected. Check backend logs.")

if __name__ == "__main__":
    main()
