#!/usr/bin/env python3
"""
Анализ Excel файлов и их связи с изображениями в датасете
"""

import pandas as pd
import os
from pathlib import Path
import json

def analyze_excel_file(excel_path, images_dir):
    """Анализ Excel файла и сопоставление с изображениями"""
    try:
        print(f"\n📊 Анализ файла: {excel_path.name}")
        
        # Читаем Excel файл
        df = pd.read_excel(excel_path)
        
        print(f"📋 Размер таблицы: {df.shape[0]} строк, {df.shape[1]} столбцов")
        print(f"📝 Столбцы: {list(df.columns)}")
        
        # Показываем первые несколько строк
        print("\n🔍 Первые 3 строки:")
        print(df.head(3).to_string())
        
        # Ищем столбцы с UUID или ID
        uuid_columns = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['id', 'uuid', 'guid', 'key']):
                uuid_columns.append(col)
        
        if uuid_columns:
            print(f"\n🔑 Найдены столбцы с ID: {uuid_columns}")
            
            # Проверяем соответствие с файлами изображений
            if images_dir.exists():
                image_files = list(images_dir.glob("*.jpg"))
                image_uuids = [f.stem for f in image_files]
                
                print(f"📁 Изображений в папке: {len(image_files)}")
                
                # Проверяем соответствие UUID
                for col in uuid_columns:
                    excel_uuids = df[col].astype(str).tolist()
                    matches = set(excel_uuids) & set(image_uuids)
                    print(f"✅ Совпадений по столбцу '{col}': {len(matches)}")
        
        # Ищем координаты
        coord_columns = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['lat', 'lon', 'coord', 'x', 'y', 'широта', 'долгота']):
                coord_columns.append(col)
        
        if coord_columns:
            print(f"\n🗺️ Найдены столбцы с координатами: {coord_columns}")
        
        # Ищем информацию о нарушениях
        violation_columns = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['violation', 'issue', 'нарушение', 'проблема', 'category', 'type']):
                violation_columns.append(col)
        
        if violation_columns:
            print(f"\n⚠️ Найдены столбцы с нарушениями: {violation_columns}")
        
        return {
            'file': excel_path.name,
            'rows': df.shape[0],
            'columns': df.shape[1],
            'column_names': list(df.columns),
            'uuid_columns': uuid_columns,
            'coord_columns': coord_columns,
            'violation_columns': violation_columns,
            'sample_data': df.head(2).to_dict()
        }
        
    except Exception as e:
        print(f"❌ Ошибка анализа {excel_path.name}: {e}")
        return None

def main():
    """Основная функция анализа"""
    data_path = Path("backend/uploads/metadata/data")
    
    if not data_path.exists():
        print(f"❌ Папка {data_path} не существует")
        return
    
    results = []
    
    # Анализируем каждый Excel файл
    for excel_file in data_path.glob("*.xlsx"):
        # Определяем соответствующую папку с изображениями
        base_name = excel_file.stem
        images_dir = data_path / base_name
        
        result = analyze_excel_file(excel_file, images_dir)
        if result:
            results.append(result)
    
    # Сохраняем результаты анализа
    output_file = Path("backend/uploads/EXCEL_ANALYSIS.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n💾 Результаты сохранены в: {output_file}")
    
    # Общая статистика
    total_rows = sum(r['rows'] for r in results)
    total_images = 0
    
    for item in data_path.iterdir():
        if item.is_dir():
            image_count = len(list(item.glob("*.jpg")))
            total_images += image_count
    
    print(f"\n📈 ОБЩАЯ СТАТИСТИКА:")
    print(f"📊 Excel файлов: {len(results)}")
    print(f"📋 Всего записей в Excel: {total_rows}")
    print(f"📁 Всего изображений: {total_images}")
    print(f"🔗 Соотношение записи/изображения: {total_rows/total_images:.2f}" if total_images > 0 else "")

if __name__ == "__main__":
    print("🔍 Анализ Excel файлов датасета...")
    main()
    print("\n✅ Анализ завершен!")
