"""
DatasetProcessor для интеграции датасета заказчика ЛЦТ 2025
"""

import pandas as pd
import json
import logging
from pathlib import Path
from typing import List, Dict
from models import db, Photo, Violation

logger = logging.getLogger(__name__)

class DatasetProcessor:
    """Процессор датасета заказчика"""
    
    def __init__(self):
        self.base_path = Path("backend/uploads")
    
    def process_excel_data(self, excel_file: Path) -> List[Dict]:
        """Обработка Excel файла"""
        try:
            df = pd.read_excel(excel_file)
            results = []
            
            for _, row in df.iterrows():
                record = {
                    'filename': row.get('Имя файла', ''),
                    'latitude': float(row.get('latitude', 0)),
                    'longitude': float(row.get('longitude', 0)),
                    'camera_id': row.get('camera', ''),
                    'dataset_type': self._get_type(excel_file.name)
                }
                results.append(record)
            
            logger.info(f"✅ Processed {len(results)} records")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return []
    
    def _get_type(self, filename: str) -> str:
        """Определение типа датасета"""
        if '18-001' in filename:
            return 'building_violations'
        elif '19-001' in filename:
            return 'garbage_violations'
        return 'unknown'
    
    def import_to_database(self, records: List[Dict], user_id: int = 1):
        """Импорт в базу данных"""
        try:
            imported = 0
            for record in records:
                if not record['filename']:
                    continue
                    
                # Создаем Photo
                photo = Photo(
                    file_path=f"dataset/{record['filename']}",
                    latitude=record['latitude'],
                    longitude=record['longitude'],
                    user_id=user_id
                )
                db.session.add(photo)
                db.session.flush()
                
                # Создаем Violation
                violation = Violation(
                    photo_id=photo.id,
                    category=record['dataset_type'],
                    confidence=0.95,
                    source='dataset',
                    user_id=user_id
                )
                db.session.add(violation)
                imported += 1
            
            db.session.commit()
            logger.info(f"✅ Imported {imported} records to database")
            return imported
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Import error: {e}")
            return 0
    
    def process_all_datasets(self) -> Dict:
        """Обработка всех датасетов"""
        results = {
            'buildings': 0,
            'garbage': 0,
            'total': 0
        }
        
        data_path = self.base_path / "metadata" / "data"
        
        for excel_file in data_path.glob("*.xlsx"):
            records = self.process_excel_data(excel_file)
            imported = self.import_to_database(records)
            
            if '18-001' in excel_file.name:
                results['buildings'] = imported
            elif '19-001' in excel_file.name:
                results['garbage'] = imported
            
            results['total'] += imported
        
        return results
