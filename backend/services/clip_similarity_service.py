"""
CLIP Image Similarity Service
Использует CLIP для создания векторных представлений изображений
и поиска похожих зданий в базе данных
"""

import os
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image
import torch
import open_clip
from pathlib import Path
import pickle

logger = logging.getLogger(__name__)

class CLIPSimilarityService:
    def __init__(self):
        """Инициализация CLIP модели и индекса"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.preprocess = None
        self.tokenizer = None
        self.index = None
        self.image_paths = []
        self.image_metadata = []
        
        # Путь к кэшу эмбеддингов
        self.cache_dir = Path("data/clip_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings_file = self.cache_dir / "embeddings.pkl"
        
        self._initialize_model()
        self._load_or_create_index()
        
    def _initialize_model(self):
        """Загрузка CLIP модели"""
        try:
            # Используем ViT-B/32 - хороший баланс скорости и качества
            model_name = 'ViT-B-32'
            pretrained = 'openai'
            
            logger.info(f"🤖 Loading CLIP model: {model_name}")
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                model_name, 
                pretrained=pretrained,
                device=self.device
            )
            self.tokenizer = open_clip.get_tokenizer(model_name)
            
            self.model.eval()  # Режим инференса
            
            logger.info(f"✅ CLIP model loaded on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise
    
    def _load_or_create_index(self):
        """Загрузка существующего индекса или создание нового"""
        try:
            if self.embeddings_file.exists():
                logger.info("📂 Loading existing CLIP embeddings...")
                with open(self.embeddings_file, 'rb') as f:
                    data = pickle.load(f)
                    self.image_paths = data['paths']
                    self.image_metadata = data['metadata']
                    embeddings = data['embeddings']
                
                # Создаем FAISS индекс
                import faiss
                dimension = embeddings.shape[1]
                self.index = faiss.IndexFlatL2(dimension)  # L2 distance
                self.index.add(embeddings)
                
                logger.info(f"✅ Loaded {len(self.image_paths)} image embeddings")
            else:
                logger.info("📝 No existing index found, will create on first use")
                import faiss
                self.index = faiss.IndexFlatL2(512)  # CLIP ViT-B/32 dimension
                
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            import faiss
            self.index = faiss.IndexFlatL2(512)
    
    def encode_image(self, image_path: str) -> np.ndarray:
        """
        Создание векторного представления изображения
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Вектор эмбеддинга (512-мерный для ViT-B/32)
        """
        try:
            # Загружаем и препроцессим изображение
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
            
            # Получаем эмбеддинг
            with torch.no_grad():
                image_features = self.model.encode_image(image_tensor)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)  # Нормализация
            
            return image_features.cpu().numpy()[0]
            
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {e}")
            return None
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        Создание векторного представления текста
        Полезно для поиска по описанию: "красное кирпичное здание с колоннами"
        
        Args:
            text: Текстовое описание
            
        Returns:
            Вектор эмбеддинга
        """
        try:
            text_tokens = self.tokenizer([text]).to(self.device)
            
            with torch.no_grad():
                text_features = self.model.encode_text(text_tokens)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            return text_features.cpu().numpy()[0]
            
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            return None
    
    def find_similar_images(self, 
                           image_path: str, 
                           top_k: int = 5,
                           similarity_threshold: float = 0.75) -> List[Dict[str, Any]]:
        """
        Поиск похожих изображений в индексе
        
        Args:
            image_path: Путь к изображению для поиска
            top_k: Количество похожих изображений
            similarity_threshold: Минимальный порог схожести (0-1)
            
        Returns:
            Список похожих изображений с метаданными
        """
        if self.index.ntotal == 0:
            logger.warning("Index is empty, no similar images to find")
            return []
        
        try:
            # Получаем эмбеддинг запроса
            query_embedding = self.encode_image(image_path)
            if query_embedding is None:
                return []
            
            # Поиск в индексе
            query_embedding = query_embedding.reshape(1, -1).astype('float32')
            distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
            
            # Конвертируем L2 distance в cosine similarity
            # similarity = 1 - (distance / 2)  для нормализованных векторов
            similarities = 1 - (distances[0] / 2)
            
            results = []
            for idx, similarity in zip(indices[0], similarities):
                if similarity >= similarity_threshold:
                    result = {
                        'image_path': self.image_paths[idx],
                        'similarity': float(similarity),
                        'metadata': self.image_metadata[idx] if idx < len(self.image_metadata) else {}
                    }
                    results.append(result)
            
            logger.info(f"🔍 Found {len(results)} similar images (threshold: {similarity_threshold})")
            return results
            
        except Exception as e:
            logger.error(f"Error finding similar images: {e}")
            return []
    
    def add_image_to_index(self, 
                          image_path: str, 
                          metadata: Dict[str, Any] = None) -> bool:
        """
        Добавление изображения в индекс
        
        Args:
            image_path: Путь к изображению
            metadata: Метаданные (координаты, адрес, и т.д.)
            
        Returns:
            True если успешно добавлено
        """
        try:
            embedding = self.encode_image(image_path)
            if embedding is None:
                return False
            
            # Добавляем в индекс
            embedding = embedding.reshape(1, -1).astype('float32')
            self.index.add(embedding)
            
            # Сохраняем метаданные
            self.image_paths.append(image_path)
            self.image_metadata.append(metadata or {})
            
            logger.debug(f"Added image to index: {image_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding image to index: {e}")
            return False
    
    def build_index_from_database(self, photos_with_coords: List[Dict[str, Any]]) -> int:
        """
        Построение индекса из фотографий в базе данных
        
        Args:
            photos_with_coords: Список фото с координатами из БД
            
        Returns:
            Количество добавленных изображений
        """
        logger.info(f"🏗️ Building CLIP index from {len(photos_with_coords)} photos...")
        
        added_count = 0
        embeddings_list = []
        
        for photo in photos_with_coords:
            image_path = photo.get('file_path')
            if not image_path or not os.path.exists(image_path):
                continue
            
            embedding = self.encode_image(image_path)
            if embedding is not None:
                embeddings_list.append(embedding)
                self.image_paths.append(image_path)
                self.image_metadata.append({
                    'lat': photo.get('lat'),
                    'lon': photo.get('lon'),
                    'address': photo.get('address_data'),
                    'photo_id': photo.get('id')
                })
                added_count += 1
                
                if added_count % 100 == 0:
                    logger.info(f"Processed {added_count} images...")
        
        if embeddings_list:
            # Создаем новый индекс
            embeddings_array = np.array(embeddings_list).astype('float32')
            
            import faiss
            dimension = embeddings_array.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings_array)
            
            # Сохраняем в кэш
            self._save_index(embeddings_array)
            
            logger.info(f"✅ Built index with {added_count} images")
        
        return added_count
    
    def _save_index(self, embeddings: np.ndarray):
        """Сохранение индекса в файл"""
        try:
            data = {
                'paths': self.image_paths,
                'metadata': self.image_metadata,
                'embeddings': embeddings
            }
            
            with open(self.embeddings_file, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"💾 Saved index to {self.embeddings_file}")
            
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики индекса"""
        return {
            'total_images': self.index.ntotal if self.index else 0,
            'dimension': 512,
            'model': 'ViT-B/32',
            'device': self.device,
            'cache_exists': self.embeddings_file.exists()
        }
