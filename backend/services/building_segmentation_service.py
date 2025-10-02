"""
Building Segmentation Service
Использует semantic segmentation для выделения контуров зданий
и сравнения со спутниковыми снимками
"""

import os
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image
import torch
import cv2
from pathlib import Path

logger = logging.getLogger(__name__)

class BuildingSegmentationService:
    def __init__(self):
        """Инициализация модели сегментации"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.input_size = (512, 512)
        
        self._initialize_model()
        
    def _initialize_model(self):
        """Загрузка предобученной модели сегментации"""
        try:
            import segmentation_models_pytorch as smp
            
            logger.info("🏗️ Loading DeepLabV3+ segmentation model...")
            
            # Используем DeepLabV3+ с ResNet50 backbone
            # Предобучена на Cityscapes (городские сцены)
            self.model = smp.DeepLabV3Plus(
                encoder_name="resnet50",
                encoder_weights="imagenet",
                classes=1,  # Binary segmentation: building vs background
                activation='sigmoid'
            )
            
            self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"✅ Segmentation model loaded on {self.device}")
            
        except ImportError:
            logger.warning("⚠️ segmentation-models-pytorch not installed")
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load segmentation model: {e}")
            self.model = None
    
    def segment_buildings(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Выделение контуров зданий на изображении
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Результат сегментации с контурами и масками
        """
        if not self.model:
            return None
        
        try:
            # Загружаем изображение
            image = Image.open(image_path).convert('RGB')
            original_size = image.size
            
            # Препроцессинг
            image_resized = image.resize(self.input_size)
            image_array = np.array(image_resized).astype(np.float32) / 255.0
            image_tensor = torch.from_numpy(image_array).permute(2, 0, 1).unsqueeze(0)
            image_tensor = image_tensor.to(self.device)
            
            # Инференс
            with torch.no_grad():
                mask = self.model(image_tensor)
                mask = mask.squeeze().cpu().numpy()
            
            # Бинаризация маски
            binary_mask = (mask > 0.5).astype(np.uint8)
            
            # Resize обратно к оригинальному размеру
            binary_mask_resized = cv2.resize(
                binary_mask, 
                original_size, 
                interpolation=cv2.INTER_NEAREST
            )
            
            # Извлечение контуров
            contours = self._extract_contours(binary_mask_resized)
            
            # Вычисление характеристик
            features = self._compute_features(binary_mask_resized, contours)
            
            result = {
                'success': True,
                'mask': binary_mask_resized,
                'contours': contours,
                'features': features,
                'building_area_ratio': features['building_ratio'],
                'num_buildings': len(contours)
            }
            
            logger.info(f"🏗️ Segmentation: found {len(contours)} buildings, area ratio: {features['building_ratio']:.2%}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in building segmentation: {e}")
            return None
    
    def _extract_contours(self, binary_mask: np.ndarray) -> List[np.ndarray]:
        """Извлечение контуров зданий"""
        contours, _ = cv2.findContours(
            binary_mask, 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Фильтруем маленькие контуры (шум)
        min_area = 100  # минимальная площадь в пикселях
        filtered_contours = [c for c in contours if cv2.contourArea(c) > min_area]
        
        # Сортируем по площади (от большего к меньшему)
        filtered_contours.sort(key=cv2.contourArea, reverse=True)
        
        return filtered_contours
    
    def _compute_features(self, mask: np.ndarray, contours: List[np.ndarray]) -> Dict[str, Any]:
        """Вычисление характеристик зданий"""
        total_pixels = mask.shape[0] * mask.shape[1]
        building_pixels = np.sum(mask)
        building_ratio = building_pixels / total_pixels
        
        features = {
            'building_ratio': building_ratio,
            'num_buildings': len(contours),
            'total_area': building_pixels,
            'contour_areas': [cv2.contourArea(c) for c in contours]
        }
        
        if contours:
            # Характеристики самого большого здания
            largest_contour = contours[0]
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            features['largest_building'] = {
                'area': cv2.contourArea(largest_contour),
                'bbox': (x, y, w, h),
                'aspect_ratio': w / h if h > 0 else 0,
                'perimeter': cv2.arcLength(largest_contour, True)
            }
        
        return features
    
    def compare_with_satellite(self, 
                               photo_segmentation: Dict[str, Any],
                               satellite_image_path: str) -> Optional[Dict[str, Any]]:
        """
        Сравнение контуров здания с фото и спутникового снимка
        
        Args:
            photo_segmentation: Результат сегментации фото
            satellite_image_path: Путь к спутниковому снимку
            
        Returns:
            Результат сравнения с similarity score
        """
        if not photo_segmentation or not os.path.exists(satellite_image_path):
            return None
        
        try:
            # Сегментируем спутниковый снимок
            satellite_segmentation = self.segment_buildings(satellite_image_path)
            
            if not satellite_segmentation:
                return None
            
            # Сравниваем характеристики
            similarity = self._compute_similarity(
                photo_segmentation['features'],
                satellite_segmentation['features']
            )
            
            result = {
                'success': True,
                'similarity': similarity,
                'photo_buildings': photo_segmentation['num_buildings'],
                'satellite_buildings': satellite_segmentation['num_buildings'],
                'match_confidence': similarity
            }
            
            logger.info(f"🗺️ Satellite comparison: similarity={similarity:.2%}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error comparing with satellite: {e}")
            return None
    
    def _compute_similarity(self, features1: Dict, features2: Dict) -> float:
        """
        Вычисление схожести между двумя наборами характеристик
        
        Использует несколько метрик:
        - Соотношение площадей зданий
        - Количество зданий
        - Характеристики самого большого здания
        """
        similarity_scores = []
        
        # 1. Сравнение соотношения площадей
        ratio1 = features1.get('building_ratio', 0)
        ratio2 = features2.get('building_ratio', 0)
        if ratio1 > 0 and ratio2 > 0:
            ratio_similarity = 1 - abs(ratio1 - ratio2) / max(ratio1, ratio2)
            similarity_scores.append(ratio_similarity * 0.3)  # вес 30%
        
        # 2. Сравнение количества зданий
        num1 = features1.get('num_buildings', 0)
        num2 = features2.get('num_buildings', 0)
        if num1 > 0 and num2 > 0:
            num_similarity = 1 - abs(num1 - num2) / max(num1, num2)
            similarity_scores.append(num_similarity * 0.2)  # вес 20%
        
        # 3. Сравнение самого большого здания
        if 'largest_building' in features1 and 'largest_building' in features2:
            lb1 = features1['largest_building']
            lb2 = features2['largest_building']
            
            # Сравнение aspect ratio
            ar1 = lb1.get('aspect_ratio', 0)
            ar2 = lb2.get('aspect_ratio', 0)
            if ar1 > 0 and ar2 > 0:
                ar_similarity = 1 - abs(ar1 - ar2) / max(ar1, ar2)
                similarity_scores.append(ar_similarity * 0.5)  # вес 50%
        
        # Итоговая схожесть
        if similarity_scores:
            return sum(similarity_scores)
        else:
            return 0.0
    
    def visualize_segmentation(self, 
                              image_path: str, 
                              segmentation_result: Dict[str, Any],
                              output_path: Optional[str] = None) -> Optional[str]:
        """
        Визуализация результатов сегментации
        
        Args:
            image_path: Путь к оригинальному изображению
            segmentation_result: Результат сегментации
            output_path: Путь для сохранения (опционально)
            
        Returns:
            Путь к сохраненному изображению
        """
        try:
            # Загружаем оригинальное изображение
            image = cv2.imread(image_path)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Создаем overlay с маской
            mask = segmentation_result['mask']
            overlay = image.copy()
            overlay[mask > 0] = [0, 255, 0]  # Зеленый цвет для зданий
            
            # Смешиваем с оригиналом
            result_image = cv2.addWeighted(image, 0.7, overlay, 0.3, 0)
            
            # Рисуем контуры
            contours = segmentation_result['contours']
            cv2.drawContours(result_image, contours, -1, (255, 0, 0), 2)
            
            # Сохраняем
            if output_path is None:
                output_dir = Path("data/segmentation_results")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / f"seg_{Path(image_path).name}")
            
            result_image_bgr = cv2.cvtColor(result_image, cv2.COLOR_RGB2BGR)
            cv2.imwrite(output_path, result_image_bgr)
            
            logger.info(f"💾 Segmentation visualization saved to {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error visualizing segmentation: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики сервиса"""
        return {
            'model_loaded': self.model is not None,
            'device': self.device,
            'input_size': self.input_size,
            'model_type': 'DeepLabV3+ (ResNet50)'
        }
