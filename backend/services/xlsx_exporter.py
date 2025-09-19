"""XLSX Exporter для ТЗ ЛЦТ 2025"""

import pandas as pd
from datetime import datetime
from pathlib import Path
from models import Photo, Violation

class XLSXExporter:
    def __init__(self):
        self.output_dir = Path("backend/uploads/exports")
        self.output_dir.mkdir(exist_ok=True)
    
    def export_violations(self) -> str:
        """Экспорт нарушений в XLSX"""
        violations = Violation.query.join(Photo).all()
        
        data = []
        for v in violations:
            data.append({
                'ID': v.id,
                'Файл': v.photo.file_path,
                'Категория': v.category,
                'Уверенность': f"{v.confidence * 100:.1f}%",
                'Широта': v.photo.latitude,
                'Долгота': v.photo.longitude,
                'Источник': v.source,
                'Дата': v.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        df = pd.DataFrame(data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"violations_{timestamp}.xlsx"
        file_path = self.output_dir / filename
        
        df.to_excel(file_path, index=False)
        return str(file_path)
