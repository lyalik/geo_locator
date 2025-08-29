#!/usr/bin/env python3
"""
Сервис базы данных изображений с геотегами
Управление локальной и облачной базой фотографий для геолокации
"""
import os
import hashlib
import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import exifread
try:
    from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.dialects.postgresql import UUID
    import uuid
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

logger = logging.getLogger(__name__)

if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()

    class GeoImage(Base):
        """Модель изображения с геотегами"""
        __tablename__ = 'geo_images'
        
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        filename = Column(String(255), nullable=False)
        file_path = Column(String(500), nullable=False)
        file_hash = Column(String(64), unique=True, nullable=False)
        file_size = Column(Integer)
        
        # Геолокация
        latitude = Column(Float)
        longitude = Column(Float)
        altitude = Column(Float)
        accuracy = Column(Float)
    
    # Метаданные изображения
    width = Column(Integer)
    height = Column(Integer)
    format = Column(String(10))
    camera_make = Column(String(100))
    camera_model = Column(String(100))
    
    # Временные метки
    date_taken = Column(DateTime)
    date_uploaded = Column(DateTime, default=datetime.utcnow)
    date_modified = Column(DateTime, default=datetime.utcnow)
    
    # Адресная информация
    address = Column(Text)
    city = Column(String(100))
    region = Column(String(100))
    country = Column(String(100))
    
    # Теги и описание
    tags = Column(Text)  # JSON array
    description = Column(Text)
    user_notes = Column(Text)
    
    # Статус обработки
    processed = Column(Boolean, default=False)
    has_gps = Column(Boolean, default=False)
    geo_source = Column(String(50))  # 'exif', 'manual', 'api_match'
    
    # Связанные данные
    yandex_place_id = Column(String(100))
    dgis_place_id = Column(String(100))
    satellite_match_score = Column(Float)

class ImageDatabaseService:
    """Сервис для работы с базой данных изображений"""
    
    def __init__(self, db_url: str = None):
        if not SQLALCHEMY_AVAILABLE:
            logger.warning("SQLAlchemy not available, using mock database service")
            self.engine = None
            self.session = None
            return
            
        try:
            if not db_url:
                db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost/geo_locator')
            
            self.engine = create_engine(db_url)
            Base.metadata.create_all(self.engine)
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            self.engine = None
            self.session = None
        
        # Директории для хранения изображений
        self.upload_dir = os.path.join(os.getcwd(), 'uploads', 'images')
        self.thumbnail_dir = os.path.join(os.getcwd(), 'uploads', 'thumbnails')
        
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.thumbnail_dir, exist_ok=True)
    
    def add_image(self, file_path: str, user_notes: str = None) -> Dict[str, Any]:
        """
        Добавление изображения в базу данных с извлечением метаданных
        """
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'error': 'File not found'}
            
            # Вычисляем хеш файла
            file_hash = self._calculate_file_hash(file_path)
            
            # Проверяем, не существует ли уже такое изображение
            existing = self.session.query(GeoImage).filter_by(file_hash=file_hash).first()
            if existing:
                return {'success': False, 'error': 'Image already exists', 'image_id': str(existing.id)}
            
            # Извлекаем метаданные
            metadata = self._extract_metadata(file_path)
            
            # Создаем запись в БД
            geo_image = GeoImage(
                filename=os.path.basename(file_path),
                file_path=file_path,
                file_hash=file_hash,
                file_size=os.path.getsize(file_path),
                width=metadata.get('width'),
                height=metadata.get('height'),
                format=metadata.get('format'),
                camera_make=metadata.get('camera_make'),
                camera_model=metadata.get('camera_model'),
                date_taken=metadata.get('date_taken'),
                latitude=metadata.get('latitude'),
                longitude=metadata.get('longitude'),
                altitude=metadata.get('altitude'),
                has_gps=metadata.get('has_gps', False),
                geo_source='exif' if metadata.get('has_gps') else None,
                user_notes=user_notes
            )
            
            self.session.add(geo_image)
            self.session.commit()
            
            # Создаем миниатюру
            self._create_thumbnail(file_path, str(geo_image.id))
            
            # Если есть GPS координаты, получаем адрес
            if geo_image.has_gps:
                self._update_address_info(geo_image)
            
            return {
                'success': True,
                'image_id': str(geo_image.id),
                'has_gps': geo_image.has_gps,
                'coordinates': {
                    'latitude': geo_image.latitude,
                    'longitude': geo_image.longitude
                } if geo_image.has_gps else None
            }
            
        except Exception as e:
            logger.error(f"Error adding image: {e}")
            self.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def find_similar_images(self, lat: float, lon: float, radius: float = 1000) -> List[Dict]:
        """
        Поиск похожих изображений в радиусе от указанных координат
        """
        try:
            # Простой поиск по прямоугольной области
            # В реальном проекте лучше использовать PostGIS для точного поиска по радиусу
            lat_delta = radius / 111000  # Примерное преобразование метров в градусы
            lon_delta = radius / (111000 * abs(lat / 90))
            
            images = self.session.query(GeoImage).filter(
                GeoImage.latitude.between(lat - lat_delta, lat + lat_delta),
                GeoImage.longitude.between(lon - lon_delta, lon + lon_delta),
                GeoImage.has_gps == True
            ).all()
            
            results = []
            for img in images:
                distance = self._calculate_distance(lat, lon, img.latitude, img.longitude)
                if distance <= radius:
                    results.append({
                        'id': str(img.id),
                        'filename': img.filename,
                        'coordinates': {'latitude': img.latitude, 'longitude': img.longitude},
                        'distance': round(distance, 2),
                        'date_taken': img.date_taken.isoformat() if img.date_taken else None,
                        'address': img.address,
                        'thumbnail_url': f"/api/images/{img.id}/thumbnail"
                    })
            
            # Сортируем по расстоянию
            results.sort(key=lambda x: x['distance'])
            
            return results
            
        except Exception as e:
            logger.error(f"Error finding similar images: {e}")
            return []
    
    def search_images(self, query: str = None, has_gps: bool = None, 
                     city: str = None, date_from: datetime = None, 
                     date_to: datetime = None) -> List[Dict]:
        """
        Поиск изображений по различным критериям
        """
        try:
            q = self.session.query(GeoImage)
            
            if query:
                q = q.filter(
                    (GeoImage.description.ilike(f'%{query}%')) |
                    (GeoImage.tags.ilike(f'%{query}%')) |
                    (GeoImage.user_notes.ilike(f'%{query}%')) |
                    (GeoImage.address.ilike(f'%{query}%'))
                )
            
            if has_gps is not None:
                q = q.filter(GeoImage.has_gps == has_gps)
            
            if city:
                q = q.filter(GeoImage.city.ilike(f'%{city}%'))
            
            if date_from:
                q = q.filter(GeoImage.date_taken >= date_from)
            
            if date_to:
                q = q.filter(GeoImage.date_taken <= date_to)
            
            images = q.order_by(GeoImage.date_taken.desc()).limit(100).all()
            
            results = []
            for img in images:
                results.append({
                    'id': str(img.id),
                    'filename': img.filename,
                    'coordinates': {
                        'latitude': img.latitude, 
                        'longitude': img.longitude
                    } if img.has_gps else None,
                    'date_taken': img.date_taken.isoformat() if img.date_taken else None,
                    'address': img.address,
                    'city': img.city,
                    'description': img.description,
                    'has_gps': img.has_gps,
                    'thumbnail_url': f"/api/images/{img.id}/thumbnail"
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching images: {e}")
            return []
    
    def update_location(self, image_id: str, lat: float, lon: float, 
                       source: str = 'manual') -> Dict[str, Any]:
        """
        Обновление геолокации изображения
        """
        try:
            image = self.session.query(GeoImage).filter_by(id=image_id).first()
            if not image:
                return {'success': False, 'error': 'Image not found'}
            
            image.latitude = lat
            image.longitude = lon
            image.has_gps = True
            image.geo_source = source
            image.date_modified = datetime.utcnow()
            
            # Обновляем адресную информацию
            self._update_address_info(image)
            
            self.session.commit()
            
            return {
                'success': True,
                'image_id': image_id,
                'coordinates': {'latitude': lat, 'longitude': lon},
                'address': image.address
            }
            
        except Exception as e:
            logger.error(f"Error updating location: {e}")
            self.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_image_info(self, image_id: str) -> Optional[Dict]:
        """
        Получение полной информации об изображении
        """
        try:
            image = self.session.query(GeoImage).filter_by(id=image_id).first()
            if not image:
                return None
            
            return {
                'id': str(image.id),
                'filename': image.filename,
                'file_path': image.file_path,
                'file_size': image.file_size,
                'dimensions': {'width': image.width, 'height': image.height},
                'format': image.format,
                'camera': {
                    'make': image.camera_make,
                    'model': image.camera_model
                },
                'coordinates': {
                    'latitude': image.latitude,
                    'longitude': image.longitude,
                    'altitude': image.altitude
                } if image.has_gps else None,
                'address': {
                    'full': image.address,
                    'city': image.city,
                    'region': image.region,
                    'country': image.country
                },
                'dates': {
                    'taken': image.date_taken.isoformat() if image.date_taken else None,
                    'uploaded': image.date_uploaded.isoformat(),
                    'modified': image.date_modified.isoformat()
                },
                'metadata': {
                    'has_gps': image.has_gps,
                    'geo_source': image.geo_source,
                    'processed': image.processed,
                    'tags': json.loads(image.tags) if image.tags else [],
                    'description': image.description,
                    'user_notes': image.user_notes
                },
                'external_ids': {
                    'yandex_place_id': image.yandex_place_id,
                    'dgis_place_id': image.dgis_place_id
                },
                'satellite_match_score': image.satellite_match_score
            }
            
        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            return None
    
    def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Извлечение метаданных из изображения"""
        metadata = {}
        
        try:
            # Основные метаданные через PIL
            with Image.open(file_path) as img:
                metadata['width'] = img.width
                metadata['height'] = img.height
                metadata['format'] = img.format
                
                # EXIF данные
                exif = img._getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        
                        if tag == 'Make':
                            metadata['camera_make'] = str(value)
                        elif tag == 'Model':
                            metadata['camera_model'] = str(value)
                        elif tag == 'DateTime':
                            try:
                                metadata['date_taken'] = datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S')
                            except:
                                pass
                        elif tag == 'GPSInfo':
                            gps_data = self._extract_gps_from_exif(value)
                            if gps_data:
                                metadata.update(gps_data)
                                metadata['has_gps'] = True
            
            # Дополнительное извлечение GPS через exifread
            if not metadata.get('has_gps'):
                with open(file_path, 'rb') as f:
                    tags = exifread.process_file(f, details=False)
                    gps_data = self._extract_gps_from_exifread(tags)
                    if gps_data:
                        metadata.update(gps_data)
                        metadata['has_gps'] = True
                        
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
        
        return metadata
    
    def _extract_gps_from_exif(self, gps_info: Dict) -> Optional[Dict]:
        """Извлечение GPS координат из EXIF данных PIL"""
        try:
            if not gps_info:
                return None
            
            def convert_to_degrees(value):
                d, m, s = value
                return d + (m / 60.0) + (s / 3600.0)
            
            lat = convert_to_degrees(gps_info[2])
            if gps_info[1] == 'S':
                lat = -lat
            
            lon = convert_to_degrees(gps_info[4])
            if gps_info[3] == 'W':
                lon = -lon
            
            result = {'latitude': lat, 'longitude': lon}
            
            if 6 in gps_info:  # Altitude
                result['altitude'] = float(gps_info[6])
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting GPS from EXIF: {e}")
            return None
    
    def _extract_gps_from_exifread(self, tags: Dict) -> Optional[Dict]:
        """Извлечение GPS координат через exifread"""
        try:
            if not all(k in tags for k in ['GPS GPSLatitude', 'GPS GPSLongitude', 
                                          'GPS GPSLatitudeRef', 'GPS GPSLongitudeRef']):
                return None
            
            def convert_to_degrees(value):
                parts = str(value).strip('[]').split(',')
                d = float(parts[0].strip())
                m = float(parts[1].strip()) if len(parts) > 1 else 0.0
                s = float(parts[2].strip()) if len(parts) > 2 else 0.0
                return d + (m / 60.0) + (s / 3600.0)
            
            lat = convert_to_degrees(tags['GPS GPSLatitude'])
            if str(tags['GPS GPSLatitudeRef']) == 'S':
                lat = -lat
            
            lon = convert_to_degrees(tags['GPS GPSLongitude'])
            if str(tags['GPS GPSLongitudeRef']) == 'W':
                lon = -lon
            
            result = {'latitude': lat, 'longitude': lon}
            
            if 'GPS GPSAltitude' in tags:
                result['altitude'] = float(str(tags['GPS GPSAltitude']))
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting GPS from exifread: {e}")
            return None
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Вычисление SHA-256 хеша файла"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _create_thumbnail(self, file_path: str, image_id: str):
        """Создание миниатюры изображения"""
        try:
            with Image.open(file_path) as img:
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                thumbnail_path = os.path.join(self.thumbnail_dir, f"{image_id}.jpg")
                img.save(thumbnail_path, "JPEG", quality=85)
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
    
    def _update_address_info(self, image: GeoImage):
        """Обновление адресной информации через геокодирование"""
        try:
            from .yandex_maps_service import YandexMapsService
            
            yandex = YandexMapsService()
            result = yandex.reverse_geocode(image.latitude, image.longitude)
            
            if result.get('success'):
                image.address = result.get('formatted_address', '')
                components = result.get('components', {})
                image.city = components.get('city', '')
                image.region = components.get('region', '')
                image.country = components.get('country', '')
                
                self.session.commit()
                
        except Exception as e:
            logger.error(f"Error updating address info: {e}")
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Вычисление расстояния между двумя точками в метрах"""
        import math
        
        R = 6371000  # Радиус Земли в метрах
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) * math.sin(delta_lon / 2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c


# Пример использования
if __name__ == "__main__":
    service = ImageDatabaseService()
    
    # Добавление изображения
    result = service.add_image("/path/to/image.jpg", "Тестовое изображение")
    print("Add result:", result)
    
    # Поиск похожих изображений
    similar = service.find_similar_images(55.7558, 37.6176, 1000)
    print("Similar images:", similar)
