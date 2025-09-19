#!/usr/bin/env python3
"""
Скрипт для переименования файлов датасета с кракозябрами
в читаемые имена согласно их содержимому
"""

import os
import json
import shutil
from pathlib import Path

def rename_json_files():
    """Переименование JSON файлов с метаданными"""
    json_path = Path("backend/uploads/metadata/json")
    
    if not json_path.exists():
        print(f"Папка {json_path} не существует")
        return
    
    # Получаем список всех JSON файлов
    json_files = list(json_path.glob("*.json"))
    print(f"Найдено {len(json_files)} JSON файлов")
    
    for i, json_file in enumerate(json_files):
        try:
            # Читаем содержимое файла
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Извлекаем информацию для нового имени
            count = data.get('count', 0)
            provider = data.get('provider', 'unknown')
            
            # Ищем коды нарушений в results
            violation_codes = set()
            for result in data.get('results', []):
                for issue in result.get('issues', []):
                    label = issue.get('label', '')
                    if label:
                        violation_codes.add(label)
            
            # Формируем новое имя
            codes_str = '_'.join(sorted(violation_codes)) if violation_codes else 'unknown'
            new_name = f"metadata_{provider}_{codes_str}_{count}items.json"
            
            # Переименовываем файл
            new_path = json_path / new_name
            if not new_path.exists():
                shutil.move(str(json_file), str(new_path))
                print(f"✅ Переименован: {json_file.name} → {new_name}")
            else:
                print(f"⚠️  Файл уже существует: {new_name}")
                
        except Exception as e:
            print(f"❌ Ошибка обработки {json_file.name}: {e}")

def analyze_data_structure():
    """Анализ структуры папок data"""
    data_path = Path("backend/uploads/metadata/data")
    
    if not data_path.exists():
        print(f"Папка {data_path} не существует")
        return
    
    print("\n📊 Анализ структуры data:")
    
    for item in data_path.iterdir():
        if item.is_dir():
            # Подсчитываем файлы в папке
            image_count = len(list(item.glob("*.jpg"))) + len(list(item.glob("*.jpeg")))
            print(f"📁 {item.name}: {image_count} изображений")
            
            # Показываем несколько примеров файлов
            examples = list(item.glob("*.jpg"))[:3]
            for example in examples:
                print(f"   📄 {example.name}")
                
        elif item.suffix == '.xlsx':
            size_mb = item.stat().st_size / (1024 * 1024)
            print(f"📊 {item.name}: {size_mb:.1f} MB")

def create_mapping_file():
    """Создание файла сопоставления для понимания связей"""
    mapping = {
        "violation_codes": {
            "00-022": "Неизвестный тип нарушения (из JSON)",
            "18-001": "Нарушения в зданиях (gin_building)",
            "19-001": "Мусорные нарушения (gin_garbage)"
        },
        "data_structure": {
            "bpla/": "Фотографии с БПЛА с координатами в именах файлов",
            "metadata/json/": "JSON файлы с детекциями и bounding boxes",
            "metadata/data/": "Excel файлы и соответствующие изображения",
            "objekt/": "Примеры объектов для детекции"
        },
        "file_naming": {
            "bpla": "{UUID}_{latitude}_{longitude}.jpeg",
            "metadata_images": "{UUID}.jpg",
            "json_files": "metadata_{provider}_{codes}_{count}items.json"
        }
    }
    
    mapping_file = Path("backend/uploads/DATASET_MAPPING.json")
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    print(f"\n📋 Создан файл сопоставления: {mapping_file}")

if __name__ == "__main__":
    print("🔄 Переименование файлов датасета...")
    
    # Переименовываем JSON файлы
    rename_json_files()
    
    # Анализируем структуру
    analyze_data_structure()
    
    # Создаем файл сопоставления
    create_mapping_file()
    
    print("\n✅ Переименование завершено!")
