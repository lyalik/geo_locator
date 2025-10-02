"""
Унифицированный формат ответа для нарушений
Соответствует формату датасета заказчика (fivegen)
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

class ViolationResponseFormatter:
    """Форматирование ответов в формат датасета заказчика"""
    
    # Маппинг наших категорий на типы заказчика
    VIOLATION_TYPE_MAPPING = {
        # Строительные нарушения -> 18-001
        'construction_site': '18-001',
        'construction': '18-001',
        'building_under_construction': '18-001',
        'scaffolding': '18-001',
        'crane': '18-001',
        'building_work': '18-001',
        'строительство': '18-001',
        'строительная площадка': '18-001',
        
        # Нарушения недвижимости -> 00-022
        'building_violation': '00-022',
        'facade_violation': '00-022',
        'architectural_violation': '00-022',
        'unauthorized_construction': '00-022',
        'building': '00-022',
        'facade': '00-022',
        'нарушения фасадов': '00-022',
        'объект недвижимости': '00-022'
    }
    
    @classmethod
    def map_to_customer_type(cls, our_category: str) -> str:
        """
        Мапинг нашей категории на тип заказчика
        
        Args:
            our_category: Наша категория нарушения
            
        Returns:
            Тип заказчика (18-001 или 00-022)
        """
        category_lower = our_category.lower()
        
        for key, value in cls.VIOLATION_TYPE_MAPPING.items():
            if key in category_lower:
                return value
        
        # По умолчанию - нарушения недвижимости
        return '00-022'
    
    @classmethod
    def format_bbox(cls, bbox: Dict or List) -> Dict[str, int]:
        """
        Унифицирует bbox в формат датасета: {x, y, w, h}
        
        Args:
            bbox: Bounding box в любом формате
            
        Returns:
            Bbox в формате {x: int, y: int, w: int, h: int}
        """
        if isinstance(bbox, dict):
            # Если уже в нужном формате
            if all(k in bbox for k in ['x', 'y', 'w', 'h']):
                return {
                    'x': int(bbox['x']),
                    'y': int(bbox['y']),
                    'w': int(bbox['w']),
                    'h': int(bbox['h'])
                }
            # Если формат [x, y, width, height]
            elif 'x1' in bbox and 'y1' in bbox:
                return {
                    'x': int(bbox['x1']),
                    'y': int(bbox['y1']),
                    'w': int(bbox.get('x2', 0) - bbox.get('x1', 0)),
                    'h': int(bbox.get('y2', 0) - bbox.get('y1', 0))
                }
        
        elif isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
            return {
                'x': int(bbox[0]),
                'y': int(bbox[1]),
                'w': int(bbox[2]),
                'h': int(bbox[3])
            }
        
        # По умолчанию - пустой bbox
        return {'x': 0, 'y': 0, 'w': 0, 'h': 0}
    
    @classmethod
    def format_response(
        cls,
        violation_id: str,
        image_path: str,
        violations: List[Dict],
        location: Dict,
        reference_matches: Optional[List[Dict]] = None,
        validation: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Форматирование ответа в формат датасета заказчика
        
        Формат как в датасете:
        {
            "id": "uuid",
            "latitude": 55.89481,
            "longitude": 37.68944,
            "issues": [{
                "label": "18-001",
                "score": 0.88,
                "bbox": {"x": 1758, "y": 461, "w": 116, "h": 173},
                "category": "строительство",
                "description": "..."
            }],
            "image": "url",
            "create_timestamp": 1754012435,
            "reference_matches": [...],
            "validation": {...},
            "source": "geo_locator"
        }
        
        Args:
            violation_id: ID нарушения
            image_path: Путь к изображению
            violations: Список нарушений
            location: Данные о местоположении
            reference_matches: Совпадения в готовой базе
            validation: Результат валидации
            metadata: Дополнительные метаданные
            
        Returns:
            Унифицированный ответ
        """
        coords = location.get('coordinates', {})
        
        # Форматируем issues в формате датасета
        issues = []
        for v in violations:
            issue = {
                'label': cls.map_to_customer_type(v.get('category', '')),
                'score': float(v.get('confidence', 0.0)),
                'bbox': cls.format_bbox(v.get('bbox', {})),
                'category': v.get('category', ''),
                'description': v.get('description', ''),
                'source': v.get('source', 'unknown')
            }
            issues.append(issue)
        
        response = {
            'id': violation_id,
            'latitude': coords.get('latitude'),
            'longitude': coords.get('longitude'),
            'issues': issues,
            'image': image_path,
            'create_timestamp': int(datetime.utcnow().timestamp()),
            'source': 'geo_locator',
            'metadata': metadata or {}
        }
        
        # Добавляем reference_matches если есть
        if reference_matches:
            response['reference_matches'] = reference_matches
            response['reference_count'] = len(reference_matches)
        
        # Добавляем validation если есть
        if validation:
            response['validation'] = validation
            response['validated'] = validation.get('validated', False)
            response['validation_score'] = validation.get('validation_score', 0.0)
        
        return response
    
    @classmethod
    def format_batch_response(
        cls,
        batch_results: List[Dict]
    ) -> Dict[str, Any]:
        """
        Форматирование пакетного ответа
        
        Args:
            batch_results: Список результатов
            
        Returns:
            Пакетный ответ в формате датасета
        """
        return {
            'count': len(batch_results),
            'provider': 'geo_locator',
            'results': batch_results,
            'timestamp': int(datetime.utcnow().timestamp())
        }
