"""
Сервис анализа панорам для улучшения определения координат
Интегрирует Yandex Panorama API с YOLO детекцией объектов
"""

import logging
import requests
import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import tempfile
import os
from PIL import Image
import io

from .yandex_maps_service import YandexMapsService
from .dgis_panorama_service import DGISPanoramaService
from .yolo_violation_detector import YOLOObjectDetector

logger = logging.getLogger(__name__)

class PanoramaAnalyzer:
    """
    Анализатор панорам для поиска объектов и уточнения координат
    """
    
    def __init__(self, yandex_service: YandexMapsService = None):
        self.yandex_service = yandex_service or YandexMapsService()
        self.dgis_service = DGISPanoramaService()
        self.yolo_detector = YOLOObjectDetector()
        
    def analyze_location_with_panoramas(self, 
                                      target_image_path: str, 
                                      lat: float, 
                                      lon: float, 
                                      search_radius: int = 300) -> Dict[str, Any]:
        """
        Анализ локации с использованием панорам для уточнения координат
        
        Args:
            target_image_path: Путь к целевому изображению
            lat: Широта примерной локации
            lon: Долгота примерной локации
            search_radius: Радиус поиска панорам в метрах
            
        Returns:
            Результат анализа с уточненными координатами
        """
        try:
            logger.info(f"🔍 Starting panorama analysis for {lat}, {lon}")
            
            # 1. Поиск ближайших панорам из разных источников
            all_panoramas = []
            
            # Поиск панорам Yandex
            yandex_result = self.yandex_service.get_panorama_nearby(lat, lon, search_radius)
            if yandex_result.get('success') and yandex_result.get('panoramas'):
                all_panoramas.extend(yandex_result['panoramas'])
                logger.info(f"📍 Found {len(yandex_result['panoramas'])} Yandex panoramas")
            
            # Поиск панорам 2GIS
            dgis_result = self.dgis_service.get_panorama_nearby(lat, lon, search_radius)
            if dgis_result.get('success') and dgis_result.get('panoramas'):
                all_panoramas.extend(dgis_result['panoramas'])
                logger.info(f"📍 Found {len(dgis_result['panoramas'])} 2GIS panoramas")
            
            if not all_panoramas:
                logger.warning("No panoramas found from any source")
                return {
                    'success': False,
                    'message': 'No panoramas available in the area from any source',
                    'panoramas_found': 0,
                    'sources_checked': ['yandex', '2gis']
                }
            
            # Сортируем все панорамы по расстоянию
            all_panoramas.sort(key=lambda x: x.get('distance', float('inf')))
            panoramas = all_panoramas
            logger.info(f"📸 Found {len(panoramas)} panoramas to analyze")
            
            # 2. Анализ целевого изображения
            target_objects = self._analyze_image_objects(target_image_path)
            
            if not target_objects:
                logger.warning("No objects detected in target image")
                return {
                    'success': False,
                    'message': 'No objects detected in target image',
                    'panoramas_found': len(panoramas)
                }
            
            # 3. Анализ каждой панорамы
            panorama_matches = []
            
            for i, panorama in enumerate(panoramas[:3]):  # Ограничиваем до 3 панорам
                logger.info(f"🔍 Analyzing panorama {i+1}/{min(3, len(panoramas))}")
                
                match_result = self._analyze_panorama_match(
                    panorama, target_objects, target_image_path
                )
                
                if match_result['success']:
                    panorama_matches.append(match_result)
            
            # 4. Определение лучшего совпадения
            best_match = self._find_best_match(panorama_matches)
            
            if best_match:
                logger.info(f"✅ Best match found with confidence {best_match['confidence']:.2f}")
                return {
                    'success': True,
                    'source': 'panorama_analysis',
                    'confidence': best_match['confidence'],
                    'coordinates': {
                        'latitude': best_match['latitude'],
                        'longitude': best_match['longitude']
                    },
                    'panorama_id': best_match['panorama_id'],
                    'panorama_source': best_match.get('panorama_source', 'unknown'),
                    'matched_objects': best_match['matched_objects'],
                    'panoramas_analyzed': len(panorama_matches),
                    'total_panoramas_found': len(panoramas),
                    'sources_used': {
                        'yandex': len([p for p in panoramas if p.get('source') != '2gis']),
                        '2gis': len([p for p in panoramas if p.get('source') == '2gis'])
                    },
                    'analysis_details': {
                        'target_objects': len(target_objects),
                        'panorama_objects': best_match.get('panorama_objects', 0),
                        'similarity_score': best_match.get('similarity_score', 0)
                    }
                }
            else:
                logger.info("No good matches found in panoramas")
                return {
                    'success': False,
                    'message': 'No matching objects found in panoramas',
                    'panoramas_analyzed': len(panorama_matches),
                    'total_panoramas_found': len(panoramas),
                    'target_objects': len(target_objects)
                }
                
        except Exception as e:
            logger.error(f"Error in panorama analysis: {e}")
            return {
                'success': False,
                'error': str(e),
                'source': 'panorama_analysis'
            }
    
    def _analyze_image_objects(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Анализ объектов на изображении с помощью YOLO
        """
        try:
            # Используем YOLO для детекции объектов
            results = self.yolo_detector.detect_objects(image_path)
            
            objects = []
            if results.get('success') and results.get('objects'):
                for obj in results['objects']:
                    objects.append({
                        'class': obj.get('category', 'unknown'),
                        'confidence': obj.get('confidence', 0),
                        'bbox': obj.get('bbox', {}),
                        'area': self._calculate_bbox_area(obj.get('bbox', {}))
                    })
            
            # Сортируем по уверенности и размеру
            objects.sort(key=lambda x: (x['confidence'], x['area']), reverse=True)
            
            logger.info(f"🎯 Detected {len(objects)} objects in target image")
            return objects[:10]  # Ограничиваем до 10 объектов
            
        except Exception as e:
            logger.error(f"Error analyzing target image objects: {e}")
            return []
    
    def _analyze_panorama_match(self, 
                               panorama: Dict[str, Any], 
                               target_objects: List[Dict[str, Any]], 
                               target_image_path: str) -> Dict[str, Any]:
        """
        Анализ совпадения объектов между панорамой и целевым изображением
        """
        try:
            # Скачиваем изображение панорамы
            panorama_image_path = self._download_panorama_image(panorama)
            
            if not panorama_image_path:
                return {'success': False, 'error': 'Failed to download panorama'}
            
            try:
                # Анализируем объекты на панораме
                panorama_objects = self._analyze_image_objects(panorama_image_path)
                
                if not panorama_objects:
                    return {'success': False, 'error': 'No objects detected in panorama'}
                
                # Сравниваем объекты
                matches = self._compare_objects(target_objects, panorama_objects)
                
                # Вычисляем общий скор совпадения
                confidence = self._calculate_match_confidence(matches, target_objects, panorama_objects)
                
                # Вычисляем визуальное сходство
                similarity_score = self._calculate_visual_similarity(target_image_path, panorama_image_path)
                
                # Комбинированная уверенность
                combined_confidence = (confidence * 0.7 + similarity_score * 0.3)
                
                return {
                    'success': True,
                    'panorama_id': panorama['id'],
                    'latitude': panorama['latitude'],
                    'longitude': panorama['longitude'],
                    'confidence': combined_confidence,
                    'panorama_source': panorama.get('source', 'yandex'),
                    'matched_objects': matches,
                    'panorama_objects': len(panorama_objects),
                    'similarity_score': similarity_score,
                    'distance_from_center': panorama['distance']
                }
                
            finally:
                # Удаляем временный файл
                if os.path.exists(panorama_image_path):
                    os.unlink(panorama_image_path)
                    
        except Exception as e:
            logger.error(f"Error analyzing panorama match: {e}")
            return {'success': False, 'error': str(e)}
    
    def _download_panorama_image(self, panorama: Dict[str, Any]) -> Optional[str]:
        """
        Скачивание изображения панорамы во временный файл
        Поддерживает разные источники (Yandex, 2GIS)
        """
        try:
            image_url = None
            
            # Определяем URL изображения в зависимости от источника
            if panorama.get('source') == '2gis':
                # Для 2GIS используем первое фото из списка
                if panorama.get('photos') and len(panorama['photos']) > 0:
                    image_url = panorama['photos'][0].get('url')
            else:
                # Для Yandex используем стандартный image_url
                image_url = panorama.get('image_url')
            
            if not image_url:
                logger.warning(f"No image URL found for panorama from {panorama.get('source', 'unknown')}")
                return None
            
            logger.info(f"📥 Downloading panorama from {panorama.get('source', 'unknown')}: {image_url}")
            response = requests.get(image_url, timeout=15)
            response.raise_for_status()
            
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(response.content)
                return tmp_file.name
                
        except Exception as e:
            logger.error(f"Error downloading panorama image from {panorama.get('source', 'unknown')}: {e}")
            return None
    
    def _compare_objects(self, 
                        target_objects: List[Dict[str, Any]], 
                        panorama_objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Сравнение объектов между целевым изображением и панорамой
        """
        matches = []
        
        for target_obj in target_objects:
            best_match = None
            best_score = 0
            
            for pano_obj in panorama_objects:
                # Сравниваем классы объектов
                if target_obj['class'] == pano_obj['class']:
                    # Учитываем уверенность детекции
                    score = min(target_obj['confidence'], pano_obj['confidence'])
                    
                    # Учитываем размер объектов (похожие размеры = выше скор)
                    size_ratio = min(target_obj['area'], pano_obj['area']) / max(target_obj['area'], pano_obj['area'])
                    score *= (0.5 + 0.5 * size_ratio)
                    
                    if score > best_score:
                        best_score = score
                        best_match = pano_obj
            
            if best_match and best_score > 0.3:  # Минимальный порог
                matches.append({
                    'target_object': target_obj,
                    'panorama_object': best_match,
                    'match_score': best_score
                })
        
        return matches
    
    def _calculate_match_confidence(self, 
                                  matches: List[Dict[str, Any]], 
                                  target_objects: List[Dict[str, Any]], 
                                  panorama_objects: List[Dict[str, Any]]) -> float:
        """
        Вычисление общей уверенности совпадения
        """
        if not matches or not target_objects:
            return 0.0
        
        # Процент совпавших объектов
        match_ratio = len(matches) / len(target_objects)
        
        # Средний скор совпадений
        avg_match_score = sum(match['match_score'] for match in matches) / len(matches)
        
        # Комбинированная уверенность
        confidence = match_ratio * avg_match_score
        
        # Бонус за количество совпадений
        if len(matches) >= 3:
            confidence *= 1.2
        elif len(matches) >= 2:
            confidence *= 1.1
        
        return min(confidence, 1.0)
    
    def _calculate_visual_similarity(self, image1_path: str, image2_path: str) -> float:
        """
        Вычисление визуального сходства между изображениями
        """
        try:
            # Загружаем изображения
            img1 = cv2.imread(image1_path)
            img2 = cv2.imread(image2_path)
            
            if img1 is None or img2 is None:
                return 0.0
            
            # Приводим к одному размеру
            img1 = cv2.resize(img1, (256, 256))
            img2 = cv2.resize(img2, (256, 256))
            
            # Вычисляем гистограммы
            hist1 = cv2.calcHist([img1], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
            hist2 = cv2.calcHist([img2], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
            
            # Сравниваем гистограммы
            similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            
            return max(0.0, similarity)
            
        except Exception as e:
            logger.error(f"Error calculating visual similarity: {e}")
            return 0.0
    
    def _find_best_match(self, panorama_matches: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Поиск лучшего совпадения среди панорам
        """
        if not panorama_matches:
            return None
        
        # Сортируем по уверенности
        panorama_matches.sort(key=lambda x: x['confidence'], reverse=True)
        
        best_match = panorama_matches[0]
        
        # Проверяем минимальный порог уверенности
        if best_match['confidence'] < 0.4:
            return None
        
        return best_match
    
    def _calculate_bbox_area(self, bbox: Dict[str, Any]) -> float:
        """
        Вычисление площади bounding box
        """
        try:
            width = bbox.get('width', 0)
            height = bbox.get('height', 0)
            return width * height
        except:
            return 0.0
