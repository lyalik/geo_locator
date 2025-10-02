#!/usr/bin/env python3
"""
Скрипт для построения CLIP индекса из существующих фотографий в базе данных
Запуск: python build_clip_index.py
"""

import sys
import os
from pathlib import Path

# Добавляем путь к backend
sys.path.insert(0, str(Path(__file__).parent))

from app import app
from models import Photo
from services.clip_similarity_service import CLIPSimilarityService
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def build_index():
    """Построение CLIP индекса из фотографий в БД"""
    
    with app.app_context():
        logger.info("🚀 Starting CLIP index building...")
        
        # Получаем все фото с координатами
        photos = Photo.query.filter(
            Photo.lat.isnot(None),
            Photo.lon.isnot(None)
        ).all()
        
        logger.info(f"📊 Found {len(photos)} photos with coordinates in database")
        
        if not photos:
            logger.warning("⚠️ No photos with coordinates found. Upload some photos first!")
            return
        
        # Подготавливаем данные
        photos_data = []
        for photo in photos:
            if os.path.exists(photo.file_path):
                photos_data.append({
                    'id': photo.id,
                    'file_path': photo.file_path,
                    'lat': photo.lat,
                    'lon': photo.lon,
                    'address_data': photo.address_data
                })
            else:
                logger.warning(f"⚠️ File not found: {photo.file_path}")
        
        logger.info(f"✅ {len(photos_data)} photos have valid file paths")
        
        # Создаем CLIP service и строим индекс
        clip_service = CLIPSimilarityService()
        added_count = clip_service.build_index_from_database(photos_data)
        
        logger.info(f"🎉 Successfully built CLIP index with {added_count} images!")
        
        # Показываем статистику
        stats = clip_service.get_statistics()
        logger.info(f"📊 Index statistics:")
        logger.info(f"   Total images: {stats['total_images']}")
        logger.info(f"   Dimension: {stats['dimension']}")
        logger.info(f"   Model: {stats['model']}")
        logger.info(f"   Device: {stats['device']}")
        logger.info(f"   Cache exists: {stats['cache_exists']}")

if __name__ == '__main__':
    try:
        build_index()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        sys.exit(1)
