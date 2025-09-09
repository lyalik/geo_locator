"""
Сервис для работы с архивными фотографиями зданий и сооружений.
Обеспечивает поиск похожих объектов и извлечение метаданных.
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageStat
import hashlib

logger = logging.getLogger(__name__)

class ArchivePhotoService:
    """Сервис для работы с архивным датасетом фото зданий."""
    
    def __init__(self, archive_path: str = None):
        """
        Инициализация сервиса архивных фото.
        
        Args:
            archive_path: Путь к папке с архивными фото
        """
        if archive_path is None:
            # Путь относительно корня проекта
            current_dir = Path(__file__).parent.parent
            archive_path = current_dir / "data" / "archive_photos"
        
        self.archive_path = Path(archive_path)
        self.buildings_path = self.archive_path / "buildings"
        self.landmarks_path = self.archive_path / "landmarks"
        self.streets_path = self.archive_path / "streets"
        self.metadata_path = self.archive_path / "metadata"
        
        # Создаем папки если их нет
        for path in [self.buildings_path, self.landmarks_path, self.streets_path, self.metadata_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Кэш для метаданных
        self._metadata_cache = {}
        self._load_metadata_cache()
        
        logger.info(f"🏛️ Archive Photo Service initialized with {len(self._metadata_cache)} photos")
    
    def _load_metadata_cache(self):
        """Загружает все метаданные в кэш для быстрого доступа."""
        try:
            for metadata_file in self.metadata_path.glob("*.json"):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        filename = metadata.get('filename')
                        if filename:
                            self._metadata_cache[filename] = metadata
                except Exception as e:
                    logger.warning(f"Failed to load metadata from {metadata_file}: {e}")
        except Exception as e:
            logger.error(f"Failed to load metadata cache: {e}")
    
    def find_similar_buildings(self, image_path: str, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Находит похожие здания в архивном датасете.
        
        Args:
            image_path: Путь к изображению для поиска
            threshold: Порог схожести (0.0-1.0)
            
        Returns:
            Список похожих зданий с метаданными и оценкой схожести
        """
        try:
            if not os.path.exists(image_path):
                logger.warning(f"Image not found: {image_path}")
                return []
            
            # Извлекаем признаки из исходного изображения
            query_features = self._extract_image_features(image_path)
            if query_features is None:
                return []
            
            similar_buildings = []
            
            # Ищем во всех категориях
            for category_path in [self.buildings_path, self.landmarks_path, self.streets_path]:
                if not category_path.exists():
                    continue
                    
                for image_file in category_path.glob("*.{jpg,jpeg,png,bmp}"):
                    try:
                        # Извлекаем признаки из архивного изображения
                        archive_features = self._extract_image_features(str(image_file))
                        if archive_features is None:
                            continue
                        
                        # Вычисляем схожесть
                        similarity = self._calculate_similarity(query_features, archive_features)
                        
                        if similarity >= threshold:
                            # Получаем метаданные
                            metadata = self.get_building_metadata(image_file.name)
                            
                            similar_buildings.append({
                                'filename': image_file.name,
                                'similarity_score': similarity,
                                'category': category_path.name,
                                'image_path': str(image_file),
                                'metadata': metadata
                            })
                    
                    except Exception as e:
                        logger.debug(f"Error processing {image_file}: {e}")
                        continue
            
            # Сортируем по схожести
            similar_buildings.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            logger.info(f"🔍 Found {len(similar_buildings)} similar buildings (threshold: {threshold})")
            return similar_buildings[:10]  # Возвращаем топ-10
            
        except Exception as e:
            logger.error(f"Error finding similar buildings: {e}")
            return []
    
    def get_building_metadata(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Получает метаданные для конкретного здания.
        
        Args:
            filename: Имя файла изображения
            
        Returns:
            Словарь с метаданными или None
        """
        try:
            # Сначала проверяем кэш
            if filename in self._metadata_cache:
                return self._metadata_cache[filename]
            
            # Ищем JSON файл с метаданными
            metadata_file = self.metadata_path / f"{Path(filename).stem}.json"
            
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    # Добавляем в кэш
                    self._metadata_cache[filename] = metadata
                    return metadata
            
            logger.debug(f"No metadata found for {filename}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting metadata for {filename}: {e}")
            return None
    
    def search_by_architectural_features(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Поиск зданий по архитектурным особенностям.
        
        Args:
            features: Словарь с архитектурными особенностями
            
        Returns:
            Список подходящих зданий
        """
        try:
            matching_buildings = []
            
            for filename, metadata in self._metadata_cache.items():
                match_score = 0.0
                total_features = 0
                
                # Проверяем архитектурный стиль
                if 'architectural_style' in features and 'architectural_style' in metadata:
                    if features['architectural_style'].lower() in metadata['architectural_style'].lower():
                        match_score += 0.3
                    total_features += 1
                
                # Проверяем тип здания
                if 'building_type' in features and 'building_type' in metadata:
                    if features['building_type'].lower() in metadata['building_type'].lower():
                        match_score += 0.3
                    total_features += 1
                
                # Проверяем теги
                if 'tags' in features and 'tags' in metadata:
                    feature_tags = set(tag.lower() for tag in features['tags'])
                    metadata_tags = set(tag.lower() for tag in metadata['tags'])
                    
                    if feature_tags & metadata_tags:  # Есть пересечение
                        match_score += 0.4
                    total_features += 1
                
                # Если есть совпадения, добавляем в результат
                if total_features > 0 and match_score > 0:
                    final_score = match_score / total_features if total_features > 0 else 0
                    
                    matching_buildings.append({
                        'filename': filename,
                        'match_score': final_score,
                        'metadata': metadata
                    })
            
            # Сортируем по релевантности
            matching_buildings.sort(key=lambda x: x['match_score'], reverse=True)
            
            logger.info(f"🏗️ Found {len(matching_buildings)} buildings matching architectural features")
            return matching_buildings
            
        except Exception as e:
            logger.error(f"Error searching by architectural features: {e}")
            return []
    
    def get_coordinates_from_similar_buildings(self, image_path: str, threshold: float = 0.8) -> Optional[Dict[str, Any]]:
        """
        Получает координаты на основе похожих зданий из архива.
        
        Args:
            image_path: Путь к изображению
            threshold: Порог схожести
            
        Returns:
            Словарь с координатами и метаданными
        """
        try:
            similar_buildings = self.find_similar_buildings(image_path, threshold)
            
            if not similar_buildings:
                return None
            
            # Берем самое похожее здание
            best_match = similar_buildings[0]
            metadata = best_match.get('metadata', {})
            
            if 'coordinates' in metadata:
                return {
                    'latitude': metadata['coordinates']['latitude'],
                    'longitude': metadata['coordinates']['longitude'],
                    'source': 'archive_photo_match',
                    'confidence': best_match['similarity_score'],
                    'matched_building': {
                        'filename': best_match['filename'],
                        'category': best_match['category'],
                        'description': metadata.get('description', ''),
                        'address': metadata.get('address', '')
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting coordinates from similar buildings: {e}")
            return None
    
    def _extract_image_features(self, image_path: str) -> Optional[np.ndarray]:
        """
        Извлекает признаки из изображения для сравнения.
        Использует простые статистические признаки и гистограммы.
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Массив признаков или None
        """
        try:
            # Загружаем изображение
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            # Изменяем размер для единообразия
            image = cv2.resize(image, (256, 256))
            
            features = []
            
            # 1. Цветовые гистограммы
            for i in range(3):  # BGR каналы
                hist = cv2.calcHist([image], [i], None, [32], [0, 256])
                features.extend(hist.flatten())
            
            # 2. Текстурные признаки (простые)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Градиенты
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            
            features.extend([
                np.mean(grad_x),
                np.std(grad_x),
                np.mean(grad_y),
                np.std(grad_y)
            ])
            
            # 3. Статистические признаки
            features.extend([
                np.mean(gray),
                np.std(gray),
                np.median(gray)
            ])
            
            return np.array(features, dtype=np.float32)
            
        except Exception as e:
            logger.debug(f"Error extracting features from {image_path}: {e}")
            return None
    
    def _calculate_similarity(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """
        Вычисляет схожесть между двумя наборами признаков.
        
        Args:
            features1: Первый набор признаков
            features2: Второй набор признаков
            
        Returns:
            Оценка схожести от 0.0 до 1.0
        """
        try:
            # Нормализуем признаки
            norm1 = np.linalg.norm(features1)
            norm2 = np.linalg.norm(features2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Косинусное сходство
            similarity = np.dot(features1, features2) / (norm1 * norm2)
            
            # Приводим к диапазону [0, 1]
            similarity = (similarity + 1) / 2
            
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.debug(f"Error calculating similarity: {e}")
            return 0.0
    
    def add_building_to_archive(self, image_path: str, metadata: Dict[str, Any]) -> bool:
        """
        Добавляет новое здание в архив.
        
        Args:
            image_path: Путь к изображению
            metadata: Метаданные здания
            
        Returns:
            True если успешно добавлено
        """
        try:
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return False
            
            # Определяем категорию
            building_type = metadata.get('building_type', 'buildings')
            if building_type in ['landmark', 'monument']:
                category_path = self.landmarks_path
            elif building_type in ['street', 'intersection']:
                category_path = self.streets_path
            else:
                category_path = self.buildings_path
            
            # Генерируем уникальное имя файла
            original_name = Path(image_path).name
            filename = f"{hashlib.md5(original_name.encode()).hexdigest()[:8]}_{original_name}"
            
            # Копируем изображение
            target_image_path = category_path / filename
            import shutil
            shutil.copy2(image_path, target_image_path)
            
            # Сохраняем метаданные
            metadata['filename'] = filename
            metadata_file = self.metadata_path / f"{Path(filename).stem}.json"
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # Обновляем кэш
            self._metadata_cache[filename] = metadata
            
            logger.info(f"✅ Added building to archive: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding building to archive: {e}")
            return False
    
    def get_archive_statistics(self) -> Dict[str, Any]:
        """
        Получает статистику по архивному датасету.
        
        Returns:
            Словарь со статистикой
        """
        try:
            stats = {
                'total_photos': len(self._metadata_cache),
                'categories': {
                    'buildings': len(list(self.buildings_path.glob("*.{jpg,jpeg,png,bmp}"))),
                    'landmarks': len(list(self.landmarks_path.glob("*.{jpg,jpeg,png,bmp}"))),
                    'streets': len(list(self.streets_path.glob("*.{jpg,jpeg,png,bmp}")))
                },
                'architectural_styles': {},
                'building_types': {}
            }
            
            # Анализируем метаданные
            for metadata in self._metadata_cache.values():
                # Архитектурные стили
                style = metadata.get('architectural_style', 'unknown')
                stats['architectural_styles'][style] = stats['architectural_styles'].get(style, 0) + 1
                
                # Типы зданий
                building_type = metadata.get('building_type', 'unknown')
                stats['building_types'][building_type] = stats['building_types'].get(building_type, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting archive statistics: {e}")
            return {}
