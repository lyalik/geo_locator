#!/usr/bin/env python3
"""
Создание тестового видео из изображения для диагностики видео анализа
"""
import cv2
import os
import numpy as np
from PIL import Image

def create_test_video():
    """Создает тестовое видео из существующего изображения"""
    
    # Путь к тестовому изображению
    image_path = "backend/uploads/coordinates/1krasn_pl2-3797155958.jpg"
    output_path = "backend/uploads/videos/test_video.mp4"
    
    if not os.path.exists(image_path):
        print(f"❌ Изображение не найдено: {image_path}")
        return False
    
    try:
        # Загружаем изображение
        img = cv2.imread(image_path)
        if img is None:
            print(f"❌ Не удалось загрузить изображение: {image_path}")
            return False
        
        height, width, layers = img.shape
        
        # Настройки видео
        fps = 1  # 1 кадр в секунду для быстрого тестирования
        duration = 3  # 3 секунды
        total_frames = fps * duration
        
        # Создаем видео writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not video_writer.isOpened():
            print(f"❌ Не удалось создать видео writer")
            return False
        
        print(f"📹 Создание тестового видео...")
        print(f"   Размер: {width}x{height}")
        print(f"   FPS: {fps}")
        print(f"   Длительность: {duration} сек")
        print(f"   Кадров: {total_frames}")
        
        # Записываем кадры (одно и то же изображение)
        for frame_num in range(total_frames):
            # Можно добавить небольшие изменения для разнообразия
            frame = img.copy()
            
            # Добавляем номер кадра в угол
            cv2.putText(frame, f"Frame {frame_num + 1}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            video_writer.write(frame)
            print(f"   Записан кадр {frame_num + 1}/{total_frames}")
        
        # Освобождаем ресурсы
        video_writer.release()
        
        # Проверяем размер файла
        file_size = os.path.getsize(output_path)
        print(f"✅ Тестовое видео создано: {output_path}")
        print(f"   Размер файла: {file_size / 1024:.1f} KB")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания видео: {e}")
        return False

if __name__ == "__main__":
    print("🎬 СОЗДАНИЕ ТЕСТОВОГО ВИДЕО")
    print("=" * 40)
    
    success = create_test_video()
    
    if success:
        print("\n✅ Тестовое видео готово для диагностики!")
    else:
        print("\n❌ Не удалось создать тестовое видео")
