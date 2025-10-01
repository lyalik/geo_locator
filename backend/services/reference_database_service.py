"""
Сервис работы с готовой базой данных нарушений заказчика
Используется для валидации и сравнения результатов нашей системы
"""

import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import math
from datetime import datetime

logger = logging.getLogger(__name__)

class ReferenceDatabaseService:
    """Сервис для работы с готовой базой данных нарушений заказчика"""
    
    def __init__(self):
        self.data_path = Path("uploads/data")
        self.reference_data = {}
        self.violation_types = {
            '00-022': 'Объекты недвижимости, не соответствующие градостроительным нормам',
            '18-001': 'Строительная площадка'
        }
        self.total_records = 0
        self._load_reference_data()
    
    def _load_reference_data(self):
        """Загрузка готовой базы данных заказчика"""
        try:
            logger.info("📊 Загружаем готовую базу данных заказчика...")
            
            for json_file in self.data_path.glob("*.json"):
                logger.info(f"🔍 Загружаем {json_file.name}")
                
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Определяем тип нарушения из имени файла
                if '00-022' in json_file.name:
                    violation_type = '00-022'
                elif '18-001' in json_file.name:
                    violation_type = '18-001'
                else:
                    continue
                
                # Определяем период
                period = 'Август' if 'Август' in json_file.name else 'Июль'
                
                key = f"{violation_type}_{period}"
                self.reference_data[key] = data
                
                count = data.get('count', 0)
                self.total_records += count
                logger.info(f"✅ Загружено {count} записей типа {violation_type} за {period}")
            
            logger.info(f"🎯 Всего загружено {self.total_records} записей из готовой базы заказчика")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки готовой базы: {e}")
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Вычисление расстояния между двумя точками в км"""
        R = 6371  # Радиус Земли в км
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def search_by_coordinates(self, latitude: float, longitude: float, 
                            radius_km: float = 0.1) -> List[Dict]:
        """Поиск нарушений в готовой базе по координатам"""
        try:
            results = []
            
            for key, data in self.reference_data.items():
                if 'results' not in data:
                    continue
                
                for record in data['results']:
                    ref_lat = record.get('latitude')
                    ref_lon = record.get('longitude')
                    
                    if ref_lat is None or ref_lon is None:
                        continue
                    
                    # Вычисляем расстояние
                    distance = self._calculate_distance(latitude, longitude, ref_lat, ref_lon)
                    
                    if distance <= radius_km:
                        # Извлекаем информацию о нарушении
                        issues = record.get('issues', [])
                        if issues:
                            issue = issues[0]  # Берем первое нарушение
                            
                            result = {
                                'id': record.get('id'),
                                'violation_type': issue.get('label'),
                                'violation_name': self.violation_types.get(issue.get('label'), 'Unknown'),
                                'confidence': issue.get('score', 0),
                                'latitude': ref_lat,
                                'longitude': ref_lon,
                                'distance_km': distance,
                                'image_url': record.get('image'),
                                'bbox': issue.get('bbox', {}),
                                'camera_id': record.get('camera'),
                                'timestamp': record.get('create_timestamp'),
                                'source': 'reference_database'
                            }
                            results.append(result)
            
            # Сортируем по расстоянию
            results.sort(key=lambda x: x['distance_km'])
            
            logger.info(f"🔍 Найдено {len(results)} записей в готовой базе рядом с {latitude}, {longitude}")
            return results[:20]  # Ограничиваем результаты
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска в готовой базе: {e}")
            return []
    
    def validate_detection(self, our_result: Dict) -> Dict[str, Any]:
        """Валидация нашего результата против готовой базы заказчика"""
        try:
            validation_result = {
                'validated': False,
                'confidence_match': False,
                'location_match': False,
                'type_match': False,
                'reference_records': [],
                'validation_score': 0.0,
                'message': ''
            }
            
            # Получаем координаты нашего результата
            if 'coordinates' not in our_result or not our_result['coordinates']:
                validation_result['message'] = 'Нет координат для валидации'
                return validation_result
            
            lat = our_result['coordinates'].get('latitude')
            lon = our_result['coordinates'].get('longitude')
            
            if not lat or not lon:
                validation_result['message'] = 'Некорректные координаты'
                return validation_result
            
            # Ищем похожие записи в готовой базе
            reference_records = self.search_by_coordinates(lat, lon, radius_km=0.05)
            
            if reference_records:
                validation_result['reference_records'] = reference_records
                validation_result['location_match'] = True
                
                # Проверяем соответствие типов нарушений
                our_violations = our_result.get('violations', [])
                if our_violations:
                    # Маппинг наших типов к типам заказчика
                    type_mapping = {
                        'building_violations': '00-022',
                        'construction_violations': '18-001',
                        'Нарушения фасадов': '00-022',
                        'Строительство': '18-001'
                    }
                    
                    our_types = [type_mapping.get(v.get('category', ''), v.get('category', '')) 
                                for v in our_violations]
                    ref_types = [r.get('violation_type', '') for r in reference_records]
                    
                    # Проверяем пересечение типов
                    if any(our_type in ref_types for our_type in our_types):
                        validation_result['type_match'] = True
                
                # Вычисляем общий score валидации
                score = 0
                if validation_result['location_match']:
                    score += 0.5
                if validation_result['type_match']:
                    score += 0.5
                
                validation_result['validation_score'] = score
                validation_result['validated'] = score >= 0.5
                validation_result['message'] = f'Найдено {len(reference_records)} совпадений в готовой базе'
            else:
                validation_result['message'] = 'Нет совпадений в готовой базе заказчика'
            
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ Ошибка валидации: {e}")
            return {'validated': False, 'error': str(e)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики готовой базы данных"""
        try:
            stats = {
                'total_records': self.total_records,
                'violation_types': {},
                'periods': {},
                'confidence_stats': {
                    'min': 1.0,
                    'max': 0.0,
                    'avg': 0.0
                }
            }
            
            all_confidences = []
            
            for key, data in self.reference_data.items():
                violation_type = key.split('_')[0]
                period = key.split('_')[1]
                count = data.get('count', 0)
                
                stats['violation_types'][violation_type] = stats['violation_types'].get(violation_type, 0) + count
                stats['periods'][period] = stats['periods'].get(period, 0) + count
                
                # Собираем статистику по уверенности
                if 'results' in data:
                    for record in data['results'][:1000]:  # Ограничиваем для производительности
                        issues = record.get('issues', [])
                        if issues:
                            confidence = issues[0].get('score', 0)
                            all_confidences.append(confidence)
            
            if all_confidences:
                stats['confidence_stats']['min'] = min(all_confidences)
                stats['confidence_stats']['max'] = max(all_confidences)
                stats['confidence_stats']['avg'] = sum(all_confidences) / len(all_confidences)
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}
    
    def get_sample_records(self, violation_type: str = None, limit: int = 10) -> List[Dict]:
        """Получение примеров записей из готовой базы"""
        try:
            samples = []
            
            for key, data in self.reference_data.items():
                if violation_type and violation_type not in key:
                    continue
                
                if 'results' in data:
                    for record in data['results'][:limit]:
                        issues = record.get('issues', [])
                        if issues:
                            issue = issues[0]
                            sample = {
                                'id': record.get('id'),
                                'violation_type': issue.get('label'),
                                'violation_name': self.violation_types.get(issue.get('label'), 'Unknown'),
                                'confidence': issue.get('score', 0),
                                'latitude': record.get('latitude'),
                                'longitude': record.get('longitude'),
                                'image_url': record.get('image'),
                                'bbox': issue.get('bbox', {}),
                                'timestamp': record.get('create_timestamp')
                            }
                            samples.append(sample)
                        
                        if len(samples) >= limit:
                            break
                
                if len(samples) >= limit:
                    break
            
            return samples
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения примеров: {e}")
            return []
