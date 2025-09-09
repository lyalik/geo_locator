#!/usr/bin/env python3
"""
Скрипт для создания тестовых архивных изображений
"""
import os
import numpy as np
from PIL import Image, ImageDraw
import json

def create_test_building_image(filename, building_info):
    """Создает тестовое изображение здания"""
    img = Image.new('RGB', (400, 300), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    if building_info['building_type'] == 'historical':
        # Историческое здание
        draw.rectangle([50, 100, 350, 250], fill='darkred', outline='black', width=2)
        draw.ellipse([100, 80, 150, 120], fill='gold', outline='black', width=2)
        draw.ellipse([250, 80, 300, 120], fill='gold', outline='black', width=2)
    elif building_info['building_type'] == 'landmark':
        # Башня
        draw.rectangle([150, 50, 250, 250], fill='brown', outline='black', width=2)
        draw.ellipse([175, 100, 225, 150], fill='white', outline='black', width=2)
    elif building_info['building_type'] == 'street':
        # Уличный вид
        colors = ['lightgray', 'beige', 'lightcoral']
        for i in range(3):
            x = 50 + i * 100
            draw.rectangle([x, 120, x+80, 250], fill=colors[i], outline='black', width=1)
    
    return img

def main():
    base_path = '/home/denis/Documents/Hackathon_2025/geo_locator/backend/data/archive_photos'
    
    test_buildings = [
        {
            'filename': 'sample_building_001.jpg',
            'path': os.path.join(base_path, 'buildings'),
            'metadata': {
                "filename": "sample_building_001.jpg",
                "coordinates": {"latitude": 55.7558, "longitude": 37.6176},
                "building_type": "historical",
                "description": "Собор Василия Блаженного"
            }
        }
    ]
    
    for building in test_buildings:
        os.makedirs(building['path'], exist_ok=True)
        
        # Создаем изображение
        img = create_test_building_image(building['filename'], building['metadata'])
        img_path = os.path.join(building['path'], building['filename'])
        img.save(img_path)
        
        print(f"✅ Создано: {img_path}")

if __name__ == "__main__":
    main()
