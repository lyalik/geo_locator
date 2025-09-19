"""Сервис поиска по эталонной базе датасета заказчика"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

class DatasetSearchService:
    def __init__(self):
        self.buildings_data = []
        self.garbage_data = []
        self._load_dataset()
    
    def _load_dataset(self):
        """Загрузка датасета"""
        try:
            data_path = Path("uploads/metadata/data")
            
            # Здания
            buildings_excel = data_path / "18-001_gin_building_echd_19.08.25.xlsx"
            if buildings_excel.exists():
                df = pd.read_excel(buildings_excel)
                self.buildings_data = df.to_dict('records')
                logger.info(f"✅ Loaded {len(self.buildings_data)} buildings")
            
            # Мусор
            garbage_excel = data_path / "19-001_gin_garbage_echd_19.08.25.xlsx"
            if garbage_excel.exists():
                df = pd.read_excel(garbage_excel)
                self.garbage_data = df.to_dict('records')
                logger.info(f"✅ Loaded {len(self.garbage_data)} garbage records")
                
        except Exception as e:
            logger.error(f"❌ Dataset load error: {e}")
    
    def search_by_coordinates(self, lat: float, lon: float, radius: float = 0.01) -> List[Dict]:
        """Поиск по координатам"""
        results = []
        
        for record in self.buildings_data + self.garbage_data:
            r_lat = record.get('latitude', 0)
            r_lon = record.get('longitude', 0)
            
            if abs(r_lat - lat) <= radius and abs(r_lon - lon) <= radius:
                results.append({
                    'filename': record.get('Имя файла', ''),
                    'latitude': r_lat,
                    'longitude': r_lon,
                    'type': 'building' if record in self.buildings_data else 'garbage'
                })
        
        return results[:20]
    
    def get_training_data(self, violation_type: str) -> List[Dict]:
        """Получение данных для обучения"""
        if violation_type == 'building':
            return self.buildings_data[:100]
        elif violation_type == 'garbage':
            return self.garbage_data[:100]
        return []
