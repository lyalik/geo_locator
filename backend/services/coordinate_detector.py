import os
import logging
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import cv2
from PIL import Image

# Configure logging FIRST before any imports that use it
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# from .yolo_violation_detector import YOLOObjectDetector  # Временно отключено
# from .google_vision_service import GoogleVisionService  # Временно отключено
from .geo_aggregator_service import GeoAggregatorService
from .archive_photo_service import ArchivePhotoService
from .google_vision_service import GoogleVisionService
from .moscow_region_validator import MoscowRegionValidator
from services.cache_service import DetectionCache, ObjectDetectionCache
from .yandex_maps_service import YandexMapsService
from .dgis_service import DGISService
from .roscosmos_satellite_service import RoscosmosService
from .yandex_satellite_service import YandexSatelliteService
from .enhanced_coordinate_detector import EnhancedCoordinateDetector

# Import Reference Database and Image Database services
try:
    from services.reference_database_service import ReferenceDatabaseService
    REFERENCE_DB_AVAILABLE = True
except ImportError as e:
    REFERENCE_DB_AVAILABLE = False
    ReferenceDatabaseService = None
    logger.warning(f"ReferenceDatabaseService not available: {e}")

try:
    from services.image_database_service import ImageDatabaseService
    IMAGE_DB_AVAILABLE = True
except ImportError as e:
    IMAGE_DB_AVAILABLE = False
    ImageDatabaseService = None
    logger.warning(f"ImageDatabaseService not available: {e}")

# Import License Plate Detector
try:
    from services.license_plate_detector import LicensePlateDetector
    LICENSE_PLATE_AVAILABLE = True
except ImportError as e:
    LICENSE_PLATE_AVAILABLE = False
    LicensePlateDetector = None
    logger.warning(f"LicensePlateDetector not available: {e}")

# Import Yandex Vision Service
try:
    from services.yandex_vision_service import YandexVisionService
    YANDEX_VISION_AVAILABLE = True
except ImportError as e:
    YANDEX_VISION_AVAILABLE = False
    YandexVisionService = None
    logger.warning(f"YandexVisionService not available: {e}")

# Import Google services
try:
    from services.google_vision_service import GoogleVisionService
    GOOGLE_SERVICES_AVAILABLE = True
except ImportError as e:
    GOOGLE_SERVICES_AVAILABLE = False
    GoogleVisionService = None

class CoordinateDetector:
    """
    Service for detecting objects in images and determining their geographic coordinates.
    Combines YOLO object detection with geolocation services for precise coordinate determination.
    """
    
    def __init__(self):
        """Initialize the coordinate detector"""
        # Initialize services
        try:
            from .yolo_violation_detector import YOLOObjectDetector
            self.yolo_detector = YOLOObjectDetector()
            logger.info("✅ YOLO detector initialized")
        except ImportError as e:
            logger.warning(f"YOLO detector not available: {e}")
            self.yolo_detector = None
        self.geo_aggregator = GeoAggregatorService()
        self.cache = DetectionCache()
        
        # Initialize API services for enhanced coordinate analysis
        self.yandex_service = YandexMapsService()
        self.dgis_service = DGISService()
        self.roscosmos_service = RoscosmosService()
        self.yandex_satellite_service = YandexSatelliteService()
        logger.info("✅ API services initialized (Yandex, 2GIS, Roscosmos)")
        
        # Initialize Google services if available
        if GOOGLE_SERVICES_AVAILABLE:
            self.google_vision_service = GoogleVisionService()
            logger.info("✅ Google Vision service initialized")
        else:
            self.google_vision_service = None
            logger.info("⚠️ Google Vision service not available")
        
        # Initialize Archive Photo service
        try:
            self.archive_service = ArchivePhotoService()
            logger.info("🏛️ Archive Photo service initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Archive Photo service: {e}")
            self.archive_service = None
        
        # Initialize Enhanced Coordinate Detector
        self.enhanced_detector = EnhancedCoordinateDetector()
        logger.info("🎯 Enhanced Coordinate Detector initialized")
        
        # Initialize Reference Database Service
        if REFERENCE_DB_AVAILABLE:
            try:
                self.reference_db_service = ReferenceDatabaseService()
                logger.info("✅ Reference Database Service initialized (71,895 records)")
            except Exception as e:
                logger.warning(f"Failed to initialize Reference Database Service: {e}")
                self.reference_db_service = None
        else:
            self.reference_db_service = None
            logger.info("⚠️ Reference Database Service not available")
        
        # Initialize Image Database Service
        if IMAGE_DB_AVAILABLE:
            try:
                self.image_db_service = ImageDatabaseService()
                logger.info("✅ Image Database Service initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Image Database Service: {e}")
                self.image_db_service = None
        else:
            self.image_db_service = None
            logger.info("⚠️ Image Database Service not available")
        
        # Initialize License Plate Detector
        if LICENSE_PLATE_AVAILABLE:
            try:
                self.license_plate_detector = LicensePlateDetector()
                logger.info("✅ License Plate Detector initialized (автономера РФ)")
            except Exception as e:
                logger.warning(f"Failed to initialize License Plate Detector: {e}")
                self.license_plate_detector = None
        else:
            self.license_plate_detector = None
            logger.info("⚠️ License Plate Detector not available")
        
        # Initialize Yandex Vision Service
        if YANDEX_VISION_AVAILABLE:
            try:
                self.yandex_vision_service = YandexVisionService()
                logger.info("✅ Yandex Vision Service initialized (OCR + классификация)")
            except Exception as e:
                logger.warning(f"Failed to initialize Yandex Vision Service: {e}")
                self.yandex_vision_service = None
        else:
            self.yandex_vision_service = None
            logger.info("⚠️ Yandex Vision Service not available")
        
        logger.info("Coordinate Detector initialized")
    
    def detect_coordinates_from_image(self, image_path: str, location_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Detect objects in image and determine their coordinates.
        
        Args:
            image_path: Path to the image file
            location_hint: Optional location hint to improve accuracy
            
        Returns:
            Dictionary containing detected objects and their coordinates
        """
        try:
            detection_log = []  # Лог всех попыток определения координат
            
            # ШАГ 1: YOLO Detection (выполняется ОДИН раз!)
            objects = ObjectDetectionCache.get_cached_objects(image_path)
            if objects is None:
                if self.yolo_detector:
                    yolo_result = self.yolo_detector.detect_objects(image_path)
                    if yolo_result.get('success'):
                        objects = yolo_result.get('objects', [])
                        ObjectDetectionCache.cache_objects(image_path, objects)
                        detection_log.append({
                            'method': 'YOLO Detection',
                            'success': True,
                            'objects_count': len(objects),
                            'details': f'Detected {len(objects)} objects'
                        })
                        logger.info(f"🎯 YOLO detected and cached {len(objects)} objects")
                    else:
                        objects = []
                        detection_log.append({
                            'method': 'YOLO Detection',
                            'success': False,
                            'error': yolo_result.get('error', 'Detection failed')
                        })
                        logger.warning(f"YOLO detection failed: {yolo_result.get('error', 'unknown error')}")
                else:
                    objects = []
                    detection_log.append({
                        'method': 'YOLO Detection',
                        'success': False,
                        'error': 'Detector not available'
                    })
                    logger.info("YOLO detector not available, skipping object detection")
            else:
                detection_log.append({
                    'method': 'YOLO Detection',
                    'success': True,
                    'objects_count': len(objects),
                    'details': 'Used cached objects'
                })
                logger.info(f"🎯 Using cached YOLO objects: {len(objects)} objects")
            
            # ШАГ 2: Reference Database Search (НОВОЕ!)
            reference_coords = None
            if self.reference_db_service and objects:
                try:
                    # Поиск по категориям объектов
                    for obj in objects[:5]:  # Топ-5 объектов
                        category = obj.get('category', '')
                        if category:
                            matches = self.reference_db_service.search_by_description(
                                category, limit=10
                            )
                            if matches:
                                best_match = matches[0]
                                coords = best_match.get('coordinates')
                                if coords:
                                    reference_coords = {
                                        'latitude': coords.get('lat') or coords.get('latitude'),
                                        'longitude': coords.get('lon') or coords.get('longitude'),
                                        'source': 'reference_database',
                                        'confidence': best_match.get('similarity', 0.7),
                                        'matched_type': best_match.get('type')
                                    }
                                    detection_log.append({
                                        'method': 'Reference Database',
                                        'success': True,
                                        'matches_count': len(matches),
                                        'details': f'Found match for {category}'
                                    })
                                    logger.info(f"✅ Reference DB match: {category}")
                                    break
                    
                    if not reference_coords:
                        detection_log.append({
                            'method': 'Reference Database',
                            'success': False,
                            'error': 'No matches found'
                        })
                except Exception as e:
                    detection_log.append({
                        'method': 'Reference Database',
                        'success': False,
                        'error': str(e)
                    })
                    logger.error(f"Reference DB error: {e}")
            
            # Возвращаем координаты из Reference DB если найдены
            if reference_coords:
                return {
                    'success': True,
                    'coordinates': reference_coords,
                    'objects': objects,
                    'detection_log': detection_log,
                    'total_objects': len(objects)
                }
            
            # ШАГ 3: Image Database Similarity Search (НОВОЕ!)
            similarity_coords = None
            if self.image_db_service:
                try:
                    similar_images = self.image_db_service.search_similar(
                        image_path, top_k=5
                    )
                    if similar_images and similar_images[0].get('score', 0) > 0.8:
                        sim_img = similar_images[0]
                        coords = sim_img.get('coordinates')
                        if coords:
                            similarity_coords = {
                                'latitude': coords.get('lat') or coords.get('latitude'),
                                'longitude': coords.get('lon') or coords.get('longitude'),
                                'source': 'similar_image',
                                'confidence': sim_img.get('score', 0.8)
                            }
                            detection_log.append({
                                'method': 'Image Database',
                                'success': True,
                                'similar_count': len(similar_images),
                                'details': f'High similarity: {sim_img.get("score", 0):.2f}'
                            })
                            logger.info(f"✅ Image DB similarity match")
                        else:
                            detection_log.append({
                                'method': 'Image Database',
                                'success': False,
                                'error': 'Similar image has no coordinates'
                            })
                    else:
                        detection_log.append({
                            'method': 'Image Database',
                            'success': False,
                            'error': 'Low similarity score'
                        })
                except Exception as e:
                    detection_log.append({
                        'method': 'Image Database',
                        'success': False,
                        'error': str(e)
                    })
                    logger.error(f"Image DB error: {e}")
            
            # Возвращаем координаты из Image DB если найдены
            if similarity_coords:
                return {
                    'success': True,
                    'coordinates': similarity_coords,
                    'objects': objects,
                    'detection_log': detection_log,
                    'total_objects': len(objects)
                }
            
            # ШАГ 4: Enhanced Detector (включает Mistral AI, панорамы, OCR)
            enhanced_result = self.enhanced_detector.detect_coordinates_enhanced(image_path, location_hint)
            
            # Детальное логирование Enhanced Detector
            if enhanced_result['success']:
                source = enhanced_result.get('source', 'unknown')
                details = f"Source: {source}"
                
                # Специальное логирование для панорам
                if source == 'panorama_analysis':
                    details = f"Panorama analysis (Yandex + 2GIS): найдено совпадение"
                    detection_log.append({
                        'method': 'Panorama Analysis (Yandex + 2GIS)',
                        'success': True,
                        'details': 'Найдена похожая панорама с объектами'
                    })
                elif source == 'mistral_ocr':
                    detection_log.append({
                        'method': 'Mistral AI OCR',
                        'success': True,
                        'details': 'Извлечен адрес через Mistral AI'
                    })
                elif source == 'location_hint':
                    detection_log.append({
                        'method': 'Location Hint Processing',
                        'success': True,
                        'details': 'Использована подсказка пользователя'
                    })
                else:
                    detection_log.append({
                        'method': 'Enhanced Detector',
                        'success': True,
                        'details': details
                    })
            else:
                detection_log.append({
                    'method': 'Enhanced Detector',
                    'success': False,
                    'error': 'Не удалось определить координаты через Enhanced методы'
                })
            
            if enhanced_result['success'] and enhanced_result['coordinates']:
                logger.info(f"✅ Enhanced detector found coordinates via {enhanced_result.get('source')}")
                return {
                    'success': True,
                    'coordinates': enhanced_result['coordinates'],
                    'source': enhanced_result['source'],
                    'confidence': enhanced_result['confidence'],
                    'objects': objects,
                    'detection_log': detection_log,
                    'enhanced_detection': True
                }
            
            # Продолжаем даже если объекты не найдены - можем использовать другие источники координат
            logger.info("🔄 Continuing to additional detection methods (EXIF, License Plate, Yandex Vision)...")
            
            # ШАГ 5: Extract EXIF GPS metadata
            image_coords = self._extract_gps_coordinates(image_path)
            if image_coords:
                detection_log.append({
                    'method': 'EXIF GPS Metadata',
                    'success': True,
                    'details': f"GPS coords from camera"
                })
                logger.info(f"✅ EXIF GPS found")
                # Высокий приоритет - возвращаем сразу
                return {
                    'success': True,
                    'coordinates': image_coords,
                    'objects': objects,
                    'detection_log': detection_log,
                    'total_objects': len(objects)
                }
            else:
                detection_log.append({
                    'method': 'EXIF GPS Metadata',
                    'success': False,
                    'error': 'No GPS data in EXIF'
                })
            
            # ШАГ 5.5: License Plate Detection (НОВОЕ!)
            logger.info(f"🔍 Checking License Plate Detector: {self.license_plate_detector is not None}")
            if self.license_plate_detector:
                logger.info("🚗 Starting license plate detection...")
                try:
                    plate_result = self.license_plate_detector.detect_license_plates(image_path)
                    if plate_result.get('success') and plate_result.get('coordinates'):
                        coords = plate_result['coordinates']
                        detection_log.append({
                            'method': 'License Plate Detection',
                            'success': True,
                            'details': f"Регион {plate_result['region_code']}: {plate_result['region_name']}, номер: {plate_result['plate']}"
                        })
                        logger.info(f"🚗 License plate detected: {plate_result['plate']} → {plate_result['region_name']}")
                        return {
                            'success': True,
                            'coordinates': coords,
                            'objects': objects,
                            'detection_log': detection_log,
                            'total_objects': len(objects),
                            'license_plate_info': plate_result
                        }
                    else:
                        detection_log.append({
                            'method': 'License Plate Detection',
                            'success': False,
                            'error': plate_result.get('message', 'No plates detected')
                        })
                except Exception as e:
                    detection_log.append({
                        'method': 'License Plate Detection',
                        'success': False,
                        'error': str(e)
                    })
                    logger.error(f"License plate detection error: {e}")
            
            # ШАГ 5.6: Yandex Vision Analysis (НОВОЕ!)
            if self.yandex_vision_service:
                try:
                    vision_result = self.yandex_vision_service.analyze_image(image_path)
                    if vision_result.get('success'):
                        coords = self.yandex_vision_service.get_coordinates_from_analysis(vision_result)
                        if coords:
                            detection_log.append({
                                'method': 'Yandex Vision Analysis',
                                'success': True,
                                'details': f"Определено по {coords['detected_by']}: {coords.get('city', 'Неизвестно')}"
                            })
                            logger.info(f"🔤 Yandex Vision: coordinates from {coords['detected_by']}")
                            return {
                                'success': True,
                                'coordinates': coords,
                                'objects': objects,
                                'detection_log': detection_log,
                                'total_objects': len(objects),
                                'vision_analysis': vision_result
                            }
                        else:
                            detection_log.append({
                                'method': 'Yandex Vision Analysis',
                                'success': False,
                                'error': 'OCR completed but no coordinates found'
                            })
                    else:
                        detection_log.append({
                            'method': 'Yandex Vision Analysis',
                            'success': False,
                            'error': vision_result.get('error', 'Unknown error')
                        })
                except Exception as e:
                    detection_log.append({
                        'method': 'Yandex Vision Analysis',
                        'success': False,
                        'error': str(e)
                    })
                    logger.error(f"Yandex Vision analysis error: {e}")
            
            # ШАГ 5.7: Mistral AI OCR для номеров, адресов, улиц (НОВОЕ!)
            try:
                from services.mistral_ai_service import MistralAIService
                mistral_service = MistralAIService()
                
                logger.info("🤖 Starting Mistral AI OCR analysis...")
                mistral_result = mistral_service.extract_location_info(image_path)
                
                if mistral_result.get('success') and mistral_result.get('coordinates'):
                    coords = mistral_result['coordinates']
                    detection_log.append({
                        'method': 'Mistral AI OCR',
                        'success': True,
                        'details': f"Извлечено: {mistral_result.get('extracted_info', 'адрес/номер')}"
                    })
                    logger.info(f"🤖 Mistral AI: found {mistral_result.get('info_type', 'location')}")
                    return {
                        'success': True,
                        'coordinates': coords,
                        'objects': objects,
                        'detection_log': detection_log,
                        'total_objects': len(objects),
                        'mistral_ocr': mistral_result
                    }
                else:
                    detection_log.append({
                        'method': 'Mistral AI OCR',
                        'success': False,
                        'error': mistral_result.get('message', 'No location info found')
                    })
                    logger.info(f"⚠️ Mistral AI: {mistral_result.get('message', 'no info')}")
            except ImportError:
                logger.debug("Mistral AI service not available")
            except Exception as e:
                detection_log.append({
                    'method': 'Mistral AI OCR',
                    'success': False,
                    'error': str(e)
                })
                logger.error(f"Mistral AI OCR error: {e}")
            
            # ШАГ 6: Extract text and address info using Google Vision OCR
            google_ocr_coords = None
            if self.google_vision_service:
                try:
                    google_ocr_coords = self._extract_coordinates_from_text(image_path)
                    if google_ocr_coords:
                        detection_log.append({
                            'method': 'OCR Address Detection',
                            'success': True,
                            'details': google_ocr_coords.get('extracted_address', 'Address found')
                        })
                        logger.info(f"✅ OCR address found")
                        return {
                            'success': True,
                            'coordinates': google_ocr_coords,
                            'objects': objects,
                            'detection_log': detection_log,
                            'total_objects': len(objects)
                        }
                    else:
                        detection_log.append({
                            'method': 'OCR Address Detection',
                            'success': False,
                            'error': 'No address found in image'
                        })
                except Exception as e:
                    detection_log.append({
                        'method': 'OCR Address Detection',
                        'success': False,
                        'error': str(e)
                    })
                    logger.warning(f"Google Vision OCR failed: {e}")
                    google_ocr_coords = None
            
            # Step 4: Enhanced coordinate detection with Mistral AI (already integrated above)
            
            # Step 5: Use geolocation services to determine coordinates
            geo_result = None
            logger.info(f"🗺️ Location hint received: '{location_hint}' (type: {type(location_hint)}, bool: {bool(location_hint)})")
            
            # Try geolocation with hint combined with image analysis
            if location_hint and location_hint.strip():
                logger.info(f"🗺️ Processing location hint: '{location_hint}'")
                
                # Используем location hint напрямую для геолокации
                geo_result = self.geo_aggregator.locate_image(image_path, location_hint.strip())
                
                logger.info(f"🗺️ Geo result with hint: {geo_result}")
                
                # Не пропускаем fallback - может быть полезен для уточнения
                if geo_result and geo_result.get('success'):
                    logger.info("🗺️ Location hint processing successful")
                else:
                    logger.info("🗺️ Location hint processing failed, will try fallback")
            elif objects and len(objects) > 0:
                # Use detected objects to generate location context
                try:
                    # Safely get first 3 objects
                    limited_objects = objects[:3] if isinstance(objects, list) else []
                    object_descriptions = []
                    
                    for obj in limited_objects:
                        if isinstance(obj, dict):
                            desc = obj.get('description', obj.get('category', ''))
                            if desc and desc.lower() not in ['detected objects', 'none', 'null', '']:
                                object_descriptions.append(desc)
                    
                    # Создаем осмысленный контекст для поиска
                    if object_descriptions:
                        # Фильтруем и улучшаем описания объектов
                        filtered_descriptions = []
                        for desc in object_descriptions:
                            if len(desc) > 2 and desc not in ['object', 'item', 'thing']:
                                filtered_descriptions.append(desc)
                        
                        if filtered_descriptions:
                            object_context = ", ".join(filtered_descriptions[:2])  # Берем только 2 лучших
                            logger.info(f"🗺️ No location hint, trying with detected objects: {object_context}")
                            geo_result = self.geo_aggregator.locate_image(image_path, object_context)
                            logger.info(f"🗺️ Geo result with objects: {geo_result}")
                        else:
                            logger.info("🗺️ No meaningful objects detected, skipping geo search")
                            geo_result = None
                    else:
                        # Fallback: попробуем поиск по общим архитектурным терминам
                        logger.info("🗺️ No object descriptions available, trying fallback search")
                        fallback_terms = ["здание", "архитектура", "строение"]
                        for term in fallback_terms:
                            try:
                                geo_result = self.geo_aggregator.locate_image(image_path, term)
                                if geo_result and geo_result.get('success'):
                                    logger.info(f"🗺️ Fallback search successful with term: {term}")
                                    break
                            except Exception as e:
                                logger.debug(f"Fallback search failed for '{term}': {e}")
                                continue
                        else:
                            logger.info("🗺️ All fallback searches failed")
                            geo_result = None
                except Exception as e:
                    logger.error(f"Error processing objects for geolocation: {e}")
                    geo_result = None
            else:
                # Без подсказки - используем поиск по объектам
                logger.info("🗺️ No location hint, trying object-based search")
                if objects and len(objects) > 0:
                    try:
                        limited_objects = objects[:3] if isinstance(objects, list) else []
                        object_descriptions = []
                        
                        for obj in limited_objects:
                            if isinstance(obj, dict):
                                desc = obj.get('description', obj.get('category', ''))
                                if desc and desc.lower() not in ['detected objects', 'none', 'null', '']:
                                    object_descriptions.append(desc)
                        
                        if object_descriptions:
                            filtered_descriptions = []
                            for desc in object_descriptions:
                                if len(desc) > 2 and desc not in ['object', 'item', 'thing']:
                                    filtered_descriptions.append(desc)
                            
                            if filtered_descriptions:
                                object_context = ", ".join(filtered_descriptions[:2])
                                logger.info(f"🗺️ Trying with detected objects: {object_context}")
                                geo_result = self.geo_aggregator.locate_image(image_path, object_context)
                                logger.info(f"🗺️ Geo result with objects: {geo_result}")
                            else:
                                geo_result = None
                        else:
                            geo_result = None
                    except Exception as e:
                        logger.error(f"Error processing objects for geolocation: {e}")
                        geo_result = None
                else:
                    logger.info("🗺️ No objects available for geolocation")
                    geo_result = None
            
            # ШАГ 7: Geo Aggregator Services
            detection_log.append({
                'method': 'Geo Aggregator',
                'success': geo_result is not None and geo_result.get('success', False),
                'details': 'Using Yandex, 2GIS, OSM services'
            })
            
            # ШАГ 8: Archive Photo matching
            archive_coords = self._find_archive_coordinates(image_path)
            detection_log.append({
                'method': 'Archive Photo Match',
                'success': archive_coords is not None,
                'details': 'Historical image database'
            })
            
            # ШАГ 9: Image Similarity (уже проверено выше, но для старой логики)
            similarity_coords_old = self._find_similar_image_coordinates(image_path)
            
            # Combine all coordinate sources
            logger.info(f"📍 Coordinate sources: GPS={image_coords is not None}, Geo={geo_result is not None}, Archive={archive_coords is not None}")
            google_geo_coords = None
            final_coordinates = self._combine_coordinate_sources(
                image_coords, geo_result, similarity_coords_old, objects, 
                google_ocr_coords, google_geo_coords, archive_coords
            )
            logger.info(f"📍 Final coordinates: {final_coordinates}")
            
            # Enhance objects with geolocation relevance
            enhanced_objects = self._enhance_objects_with_location(objects, final_coordinates)
            
            # Get satellite imagery and additional location data
            satellite_data = None
            location_info = None
            if final_coordinates:
                satellite_data = self._get_satellite_imagery(final_coordinates)
                location_info = self._get_enhanced_location_info(final_coordinates, location_hint)
            
            # Cache the final coordinate result
            services_used = ['yolo', 'reference_db', 'image_db', 'enhanced', 'geo_services']
            if final_coordinates:
                ObjectDetectionCache.cache_coordinates(
                    image_path, final_coordinates, location_hint or "", services_used
                )
                logger.info("Cached coordinate analysis results")
            
            # Генерация рекомендаций и fallback объяснения
            fallback_reason = None
            recommendations = []
            
            if not final_coordinates or final_coordinates.get('source') == 'moscow_fallback':
                fallback_reason = self._generate_fallback_explanation(detection_log)
                recommendations = self._generate_recommendations(objects, detection_log, location_hint)
            
            # Return result with detection_log and recommendations
            result = {
                'success': True,
                'coordinates': final_coordinates,
                'objects': enhanced_objects,
                'total_objects': len(enhanced_objects),
                'satellite_data': satellite_data,
                'location_info': location_info,
                'detection_log': detection_log,  # НОВОЕ!
                'fallback_reason': fallback_reason,  # НОВОЕ!
                'recommendations': recommendations,  # НОВОЕ!
                'coordinate_sources': {
                    'gps_metadata': image_coords is not None,
                    'geolocation_service': geo_result is not None and geo_result.get('success', False),
                    'image_similarity': similarity_coords_old is not None,
                    'google_vision_ocr': google_ocr_coords is not None,
                    'mistral_ai_enhanced': enhanced_result is not None,
                    'archive_photo_match': archive_coords is not None,
                    'reference_database': reference_coords is not None
                },
                'annotated_image_path': None,
                'detection_status': 'no_objects_detected' if len(objects) == 0 else 'objects_detected',
                'cache_hit': False
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in coordinate detection: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'coordinates': None,
                'objects': [],
                'total_objects': 0
            }
    
    def _extract_gps_coordinates(self, image_path: str) -> Optional[Dict[str, float]]:
        """Extract GPS coordinates from image EXIF data."""
        try:
            from PIL.ExifTags import TAGS, GPSTAGS
            
            image = Image.open(image_path)
            exif_data = image._getexif()
            
            if not exif_data:
                return None
            
            gps_info = None
            for tag, value in exif_data.items():
                tag_name = TAGS.get(tag, tag)
                if tag_name == 'GPSInfo':
                    gps_info = value
                    break
            
            if not gps_info:
                return None
            
            # Convert GPS info to decimal coordinates
            def convert_to_degrees(value):
                d, m, s = value
                return d + (m / 60.0) + (s / 3600.0)
            
            lat = convert_to_degrees(gps_info[2])
            if gps_info[1] == 'S':
                lat = -lat
                
            lon = convert_to_degrees(gps_info[4])
            if gps_info[3] == 'W':
                lon = -lon
            
            return {
                'latitude': lat,
                'longitude': lon,
                'source': 'gps_metadata',
                'priority': 1
            }
        except Exception as e:
            logger.warning(f"Error extracting GPS coordinates: {e}")
            return None
    
    def _extract_coordinates_from_text(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Извлекает координаты из текста на изображении с помощью Google Vision OCR
        """
        if not self.google_vision_service:
            logger.info("Google Vision service not available for text extraction")
            return None
            
        try:
            # Используем Google Vision для извлечения текста
            ocr_result = self.google_vision_service.extract_text_with_vision(image_path)
            
            if ocr_result.get('success'):
                ocr_text = ocr_result.get('ocr_text', '')
                # Removed gemini_analysis - no longer used
                
                # Look for street names, house numbers, city names
                import re
                
                # Russian address patterns
                street_patterns = [
                    r'ул\.?\s*([А-Яа-я\s]+)',  # улица
                    r'пр\.?\s*([А-Яа-я\s]+)',  # проспект
                    r'пер\.?\s*([А-Яа-я\s]+)', # переулок
                    r'наб\.?\s*([А-Яа-я\s]+)', # набережная
                ]
                
                house_pattern = r'д\.?\s*(\d+[а-я]?)'  # дом
                
                extracted_address = []
                
                # Extract from OCR text
                for pattern in street_patterns:
                    matches = re.findall(pattern, ocr_text, re.IGNORECASE)
                    extracted_address.extend(matches)
                
                house_matches = re.findall(house_pattern, ocr_text, re.IGNORECASE)
                extracted_address.extend([f"дом {h}" for h in house_matches])
                
                if extracted_address:
                    # Try to geocode the extracted address
                    address_string = " ".join(extracted_address)
                    logger.info(f"🔍 Google Vision OCR extracted address: {address_string}")
                    
                    # Use geo_aggregator to convert address to coordinates
                    geo_result = self.geo_aggregator.locate_image(image_path, address_string)
                    
                    if geo_result and geo_result.get('success'):
                        locations = geo_result.get('locations', [])
                        if locations:
                            best_location = locations[0]
                            coords = best_location.get('coordinates')
                            if coords:
                                return {
                                    'latitude': coords.get('latitude', coords.get('lat')),
                                    'longitude': coords.get('longitude', coords.get('lon')),
                                    'source': 'google_vision_ocr',
                                    'confidence': best_location.get('confidence', 0.7) * 0.8,  # Slightly lower confidence
                                    'extracted_address': address_string
                                }
                
            return None
            
        except Exception as e:
            logger.debug(f"Google Vision OCR coordinate extraction failed: {str(e)}")
            return None
    
    def _analyze_geographical_features(self, image_path: str, location_hint: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Analyze geographical features using Google Gemini."""
        if not self.google_vision_service:
            logger.debug("Google Vision service not available for Gemini analysis")
            return None
            
        try:
            # Create specialized prompt for geographical analysis
            geo_prompt = f"""Проанализируй это изображение для определения географического местоположения.

Найди и опиши:
1. АРХИТЕКТУРНЫЕ ОСОБЕННОСТИ:
   - Стиль зданий (советский, современный, дореволюционный)
   - Материалы (кирпич, панель, монолит)
   - Этажность и планировка

2. ГЕОГРАФИЧЕСКИЕ ОРИЕНТИРЫ:
   - Названия улиц, проспектов, площадей
   - Номера домов
   - Названия магазинов, кафе, организаций
   - Вывески и указатели

3. ГОРОДСКОЙ КОНТЕКСТ:
   - Тип района (центр, спальный, промышленный)
   - Транспортная инфраструктура
   - Ландшафтные особенности

4. РЕГИОНАЛЬНЫЕ ПРИЗНАКИ:
   - Климатические особенности
   - Архитектурный стиль региона
   - Языковые особенности на вывесках

{f"Контекст местоположения: {location_hint}" if location_hint else ""}

Верни результат в JSON формате:
{{
  "architectural_style": "описание стиля",
  "building_materials": ["материал1", "материал2"],
  "street_names": ["название1", "название2"],
  "house_numbers": ["номер1", "номер2"],
  "business_names": ["название1", "название2"],
  "district_type": "тип района",
  "regional_features": ["особенность1", "особенность2"],
  "estimated_location": "предполагаемый город/район",
  "confidence": 0.0-1.0
}}"""

            result = self.google_vision_service.analyze_image_with_gemini(image_path, geo_prompt)
            
            if result.get('success') and result.get('analysis'):
                analysis_text = result['analysis']
                
                # Parse JSON from response
                import re
                import json
                
                json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                if json_match:
                    try:
                        parsed_data = json.loads(json_match.group())
                        
                        # Extract location information
                        estimated_location = parsed_data.get('estimated_location', '')
                        street_names = parsed_data.get('street_names', [])
                        house_numbers = parsed_data.get('house_numbers', [])
                        confidence = float(parsed_data.get('confidence', 0.6))
                        
                        # Try to create address from extracted data
                        address_parts = []
                        if street_names:
                            address_parts.extend(street_names)
                        if house_numbers:
                            address_parts.extend([f"дом {h}" for h in house_numbers])
                        if estimated_location:
                            address_parts.append(estimated_location)
                        
                        if address_parts:
                            address_string = " ".join(address_parts)
                            logger.info(f"🤖 Google Gemini extracted location: {address_string}")
                            
                            # Try to geocode
                            geo_result = self.geo_aggregator.locate_image(image_path, address_string)
                            
                            if geo_result and geo_result.get('success'):
                                locations = geo_result.get('locations', [])
                                if locations:
                                    best_location = locations[0]
                                    coords = best_location.get('coordinates')
                                    if coords:
                                        return {
                                            'latitude': coords.get('latitude', coords.get('lat')),
                                            'longitude': coords.get('longitude', coords.get('lon')),
                                            'source': 'google_gemini_geo',
                                            'confidence': confidence * best_location.get('confidence', 0.7) * 0.7,
                                            'extracted_features': parsed_data,
                                            'estimated_address': address_string
                                        }
                        
                        # Even if no coordinates found, return the analysis
                        return {
                            'source': 'google_gemini_geo',
                            'confidence': confidence * 0.5,  # Lower confidence without coordinates
                            'extracted_features': parsed_data,
                            'analysis_only': True
                        }
                        
                    except json.JSONDecodeError as e:
                        logger.debug(f"Failed to parse Gemini JSON response: {e}")
                
            return None
            
        except Exception as e:
            logger.debug(f"Google Gemini geographical analysis failed: {str(e)}")
            return None
    
    def _find_archive_coordinates(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Find coordinates by matching with archive photos."""
        logger.info(f"🏛️ Archive search - Service available: {self.archive_service is not None}")
        
        if not self.archive_service:
            logger.info("🏛️ Archive service not available, skipping archive matching")
            return None
            
        try:
            logger.info(f"🏛️ Archive search - Searching for similar buildings in archive...")
            # Search for similar buildings in archive
            archive_result = self.archive_service.get_coordinates_from_similar_buildings(
                image_path, threshold=0.75
            )
            
            logger.info(f"🏛️ Archive search - Result: {archive_result}")
            
            if archive_result:
                logger.info(f"🏛️ Found archive match: {archive_result.get('matched_building', {}).get('description', 'Unknown building')}")
                return archive_result
            else:
                logger.info("🏛️ Archive search - No matches found")
            
            return None
            
        except Exception as e:
            logger.error(f"🏛️ Archive photo matching failed: {str(e)}")
            return None
    
    def _find_similar_image_coordinates(self, image_path: str) -> Optional[Dict[str, float]]:
        """Find coordinates by matching with similar images in database."""
        try:
            # Image similarity service not available, skip this step
            logger.debug("Image similarity service not available, skipping similarity matching")
            return None
            
        except Exception as e:
            logger.debug(f"Image similarity matching failed: {str(e)}")
            return None
    
    def _combine_coordinate_sources(self, gps_coords: Optional[Dict], geo_result: Optional[Dict], 
                                  similarity_coords: Optional[Dict], objects: List[Dict],
                                  google_ocr_coords: Optional[Dict] = None, 
                                  google_geo_coords: Optional[Dict] = None,
                                  archive_coords: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Combine coordinates from different sources with confidence weighting."""
        logger.info(f"🔍 Combining coordinate sources:")
        logger.info(f"  GPS: {gps_coords}")
        logger.info(f"  Geo: {geo_result}")
        logger.info(f"  Archive: {archive_coords}")
        logger.info(f"  Google OCR: {google_ocr_coords}")
        logger.info(f"  Google Geo: {google_geo_coords}")
        logger.info(f"  Similarity: {similarity_coords}")
        
        coordinate_candidates = []
        
        # Add GPS coordinates (highest priority) - только если в Москве и МО
        if gps_coords:
            lat = gps_coords.get('latitude')
            lon = gps_coords.get('longitude')
            if lat and lon and MoscowRegionValidator.is_in_moscow_region(lat, lon):
                coordinate_candidates.append({
                    **gps_coords,
                    'confidence': 0.95,
                    'priority': 1
                })
            else:
                logger.warning(f"🚫 Filtered out GPS coordinates outside Moscow region: {lat}, {lon}")
        
        # Add geolocation service results
        if geo_result and geo_result.get('success'):
            final_location = geo_result.get('final_location')
            if final_location and final_location.get('coordinates'):
                coords = final_location['coordinates']
                lat = coords.get('latitude', coords.get('lat'))
                lon = coords.get('longitude', coords.get('lon'))
                
                # ОГРАНИЧЕНИЕ: Только координаты в Москве и МО
                if lat and lon and MoscowRegionValidator.is_in_moscow_region(lat, lon):
                    coordinate_candidates.append({
                        'latitude': lat,
                        'longitude': lon,
                        'source': 'geolocation_service',
                        'confidence': final_location.get('confidence', 0.7),
                        'priority': 2
                    })
                else:
                    logger.warning(f"🚫 Filtered out coordinates outside Moscow region: {lat}, {lon}")
        
        # Add Google Vision OCR coordinates
        if google_ocr_coords:
            coordinate_candidates.append({
                **google_ocr_coords,
                'priority': 3
            })
        
        # Add Google Gemini geographical analysis coordinates
        if google_geo_coords:
            coordinate_candidates.append({
                **google_geo_coords,
                'priority': 4
            })
        
        # Add archive photo matching coordinates
        if archive_coords:
            coordinate_candidates.append({
                **archive_coords,
                'priority': 3  # High priority for archive matches
            })
        
        # Add image similarity coordinates
        if similarity_coords:
            coordinate_candidates.append({
                **similarity_coords,
                'confidence': similarity_coords.get('similarity_score', 0.6) * 0.8,
                'priority': 6
            })
        
        if not coordinate_candidates:
            logger.warning("No valid coordinates found from any source, using Moscow center as fallback")
            # Fallback на центр Москвы
            return {
                'latitude': 55.7558,
                'longitude': 37.6176,
                'confidence': 0.3,
                'source': 'moscow_fallback',
                'all_sources': [{
                    'latitude': 55.7558,
                    'longitude': 37.6176,
                    'source': 'moscow_fallback',
                    'confidence': 0.3,
                    'priority': 99
                }]
            }
        
        # Sort by priority and confidence
        coordinate_candidates.sort(key=lambda x: (x['priority'], -x['confidence']))
        
        # Return the best coordinate with metadata
        best_coord = coordinate_candidates[0]
        
        return {
            'latitude': best_coord['latitude'],
            'longitude': best_coord['longitude'],
            'confidence': best_coord['confidence'],
            'source': best_coord['source'],
            'all_sources': coordinate_candidates
        }
    
    def _enhance_objects_with_location(self, objects: List[Dict], coordinates: Optional[Dict]) -> List[Dict]:
        """Enhance detected objects with location context and geolocation relevance."""
        if not coordinates:
            return objects
        
        enhanced_objects = []
        
        for obj in objects:
            # Ensure obj is a dictionary
            if isinstance(obj, str):
                enhanced_obj = {'name': obj, 'confidence': 0.5}
            elif isinstance(obj, dict):
                enhanced_obj = obj.copy()
            else:
                enhanced_obj = {'name': str(obj), 'confidence': 0.5}
            
            # Add coordinate information
            enhanced_obj['location'] = {
                'latitude': coordinates['latitude'],
                'longitude': coordinates['longitude'],
                'confidence': coordinates['confidence']
            }
            
            # Calculate geolocation utility score
            enhanced_obj['geolocation_utility'] = self._calculate_geolocation_utility(enhanced_obj)
            
            # Add location context
            enhanced_obj['location_context'] = self._get_location_context(
                enhanced_obj, coordinates['latitude'], coordinates['longitude']
            )
            
            enhanced_objects.append(enhanced_obj)
        
        # Sort by geolocation utility (most useful for location determination first)
        enhanced_objects.sort(key=lambda x: x['geolocation_utility'], reverse=True)
        
        return enhanced_objects
    
    def _calculate_geolocation_utility(self, obj: Dict) -> float:
        """Calculate how useful this object is for geolocation purposes."""
        category = obj.get('category', '')
        confidence = obj.get('confidence', 0)
        relevance = obj.get('relevance', 'low')
        
        # Base utility scores by category
        utility_scores = {
            'landmark': 1.0,
            'monument': 1.0,
            'building': 0.9,
            'infrastructure': 0.8,
            'signage': 0.7,
            'transportation': 0.5,
            'urban_furniture': 0.4,
            'natural_feature': 0.3
        }
        
        base_score = utility_scores.get(category, 0.2)
        
        # Relevance multiplier
        relevance_multiplier = {
            'high': 1.0,
            'medium': 0.8,
            'low': 0.6
        }.get(relevance, 0.5)
        
        return base_score * confidence * relevance_multiplier
    
    def _is_beijing_coordinates(self, lat: float, lon: float) -> bool:
        """Check if coordinates are Beijing (likely default values)"""
        return abs(lat - 39.9042) < 0.1 and abs(lon - 116.4074) < 0.1

    def _get_location_context(self, obj: Dict, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get additional location context for the detected object."""
        try:
            # Use geo aggregator to get area information
            area_info = self.geo_aggregator.analyze_area(latitude, longitude)
            
            return {
                'area_type': area_info.get('area_type', 'unknown'),
                'nearby_landmarks': area_info.get('landmarks', [])[:3],
                'administrative_area': area_info.get('administrative', {}),
                'urban_context': area_info.get('urban_analysis', {})
            }
            
        except Exception as e:
            logger.debug(f"Failed to get location context: {str(e)}")
            return {}
    
    def batch_detect_coordinates(self, image_paths: List[str], 
                               location_hints: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Detect coordinates for multiple images efficiently.
        
        Args:
            image_paths: List of paths to image files
            location_hints: Optional list of location hints for each image
            
        Returns:
            List of coordinate detection results
        """
        results = []
        
        if location_hints and len(location_hints) != len(image_paths):
            location_hints = None
        
        for i, image_path in enumerate(image_paths):
            hint = location_hints[i] if location_hints else None
            result = self.detect_coordinates_from_image(image_path, hint)
            result['image_path'] = image_path
            results.append(result)
        
        return results
    
    def get_detection_statistics(self) -> Dict[str, Any]:
        """Get statistics about coordinate detection performance."""
        return {
            'detector_info': self.yolo_detector.get_model_info(),
            'supported_object_categories': list(self.yolo_detector.CATEGORY_DESCRIPTIONS.keys()),
            'coordinate_sources': [
                'gps_metadata',
                'geolocation_service', 
                'image_similarity'
            ],
            'geolocation_utility_categories': [
                'landmark',
                'monument', 
                'building',
                'infrastructure',
                'vehicle'
            ]
        }
    
    def _get_satellite_imagery(self, coordinates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Получение спутниковых снимков для найденных координат
        """
        try:
            lat = coordinates['latitude']
            lon = coordinates['longitude']
            
            logger.info(f"🛰️ Getting satellite imagery for coordinates: {lat}, {lon}")
            
            # Приоритет источников: Роскосмос -> Яндекс -> публичные
            satellite_sources = []
            
            # 1. Роскосмос (основной источник)
            try:
                roscosmos_result = self.roscosmos_service.get_satellite_image(lat, lon, zoom=16)
                if roscosmos_result.get('success'):
                    satellite_sources.append({
                        'source': 'roscosmos',
                        'priority': 1,
                        'data': roscosmos_result
                    })
                    logger.info("✅ Roscosmos satellite image obtained")
            except Exception as e:
                logger.warning(f"Roscosmos satellite service failed: {e}")
            
            # 2. Яндекс Спутник (резервный)
            try:
                yandex_result = self.yandex_satellite_service.get_satellite_image(lat, lon, zoom=16)
                if yandex_result.get('success'):
                    satellite_sources.append({
                        'source': 'yandex_satellite',
                        'priority': 2,
                        'data': yandex_result
                    })
                    logger.info("✅ Yandex satellite image obtained")
            except Exception as e:
                logger.warning(f"Yandex satellite service failed: {e}")
            
            if satellite_sources:
                # Возвращаем лучший доступный источник
                best_source = min(satellite_sources, key=lambda x: x['priority'])
                
                # Определяем читаемое название источника
                source_names = {
                    'roscosmos': 'Роскосмос',
                    'yandex_satellite': 'Яндекс Спутник',
                    'esri': 'ESRI World Imagery'
                }
                
                return {
                    'success': True,
                    'primary_source': best_source['source'],
                    'primary_source_name': source_names.get(best_source['source'], best_source['source']),
                    'image_data': best_source['data'],
                    'available_sources': len(satellite_sources),
                    'all_sources': [source_names.get(s['source'], s['source']) for s in satellite_sources],
                    'coordinates': {'latitude': lat, 'longitude': lon}
                }
            else:
                # Fallback к ESRI World Imagery
                logger.warning("No satellite imagery available from primary sources, using ESRI fallback")
                return {
                    'success': True,
                    'primary_source': 'esri',
                    'primary_source_name': 'ESRI World Imagery',
                    'image_data': {
                        'image_url': f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/16/{int((1 - (lat + 90) / 180) * (2 ** 16))}/{int((lon + 180) / 360 * (2 ** 16))}',
                        'content_type': 'image/jpeg'
                    },
                    'available_sources': 1,
                    'all_sources': ['ESRI World Imagery'],
                    'coordinates': {'latitude': lat, 'longitude': lon}
                }
                
        except Exception as e:
            logger.error(f"Error getting satellite imagery: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_enhanced_location_info(self, coordinates: Dict[str, Any], location_hint: str = None) -> Optional[Dict[str, Any]]:
        """
        Получение дополнительной информации о местоположении через API сервисы
        """
        try:
            lat = coordinates['latitude']
            lon = coordinates['longitude']
            
            logger.info(f"🗺️ Getting enhanced location info for: {lat}, {lon}")
            
            location_data = {
                'coordinates': {'latitude': lat, 'longitude': lon},
                'yandex_data': None,
                'dgis_data': None,
                'reverse_geocoding': None,
                'nearby_places': []
            }
            
            # 1. Обратное геокодирование через Яндекс
            try:
                # Формируем запрос для обратного геокодирования
                coord_string = f"{lat},{lon}"
                yandex_geocode = self.yandex_service.geocode(coord_string)
                if yandex_geocode.get('success'):
                    location_data['reverse_geocoding'] = yandex_geocode
                    logger.info("✅ Yandex reverse geocoding successful")
            except Exception as e:
                logger.warning(f"Yandex reverse geocoding failed: {e}")
            
            # 2. Поиск ближайших мест через 2GIS
            try:
                dgis_nearby = self.dgis_service.search_places("", lat=lat, lon=lon, radius=500)
                if dgis_nearby.get('success'):
                    location_data['dgis_data'] = dgis_nearby
                    location_data['nearby_places'] = dgis_nearby.get('places', [])[:5]  # Топ 5 мест
                    logger.info(f"✅ 2GIS found {len(location_data['nearby_places'])} nearby places")
            except Exception as e:
                logger.warning(f"2GIS nearby search failed: {e}")
            
            # 3. Дополнительный поиск через Яндекс если есть подсказка
            if location_hint:
                try:
                    yandex_search = self.yandex_service.search_places(location_hint, lat=lat, lon=lon)
                    if yandex_search.get('success'):
                        location_data['yandex_data'] = yandex_search
                        logger.info("✅ Yandex location search successful")
                except Exception as e:
                    logger.warning(f"Yandex location search failed: {e}")
            
            return location_data
            
        except Exception as e:
            logger.error(f"Error getting enhanced location info: {e}")
            return {'error': str(e)}
    
    def _generate_fallback_explanation(self, detection_log: List[Dict]) -> str:
        """
        Генерация объяснения почему использован fallback
        
        Args:
            detection_log: Лог всех попыток определения координат
            
        Returns:
            Строка с объяснением причин
        """
        failed_methods = [log for log in detection_log if not log.get('success', False)]
        
        if not failed_methods:
            return "Координаты определены успешно"
        
        explanation = "Координаты не определены по следующим причинам:\n\n"
        
        for method_log in failed_methods:
            method = method_log.get('method', 'Unknown')
            error = method_log.get('error', 'Нет данных')
            explanation += f"• {method}: {error}\n"
        
        explanation += f"\nИспользованы координаты по умолчанию (Москва, центр)."
        
        return explanation
    
    def _generate_recommendations(self, objects: List[Dict], detection_log: List[Dict], location_hint: Optional[str]) -> List[Dict]:
        """
        Генерация рекомендаций для улучшения определения координат
        
        Args:
            objects: Обнаруженные объекты
            detection_log: Лог попыток определения
            location_hint: Подсказка местоположения (если была)
            
        Returns:
            Список рекомендаций
        """
        recommendations = []
        
        # Проверка: мало объектов
        if len(objects) == 0:
            recommendations.append({
                'type': 'no_objects',
                'priority': 'high',
                'message': 'На изображении не обнаружено характерных объектов',
                'action': 'Попробуйте загрузить фото с четкими зданиями, вывесками или ориентирами'
            })
        elif len(objects) < 3:
            recommendations.append({
                'type': 'few_objects',
                'priority': 'medium',
                'message': f'Обнаружено мало объектов ({len(objects)})',
                'action': 'Для лучшей точности сфотографируйте больше ориентиров'
            })
        
        # Проверка: нет подсказки местоположения
        if not location_hint or not location_hint.strip():
            recommendations.append({
                'type': 'no_location_hint',
                'priority': 'high',
                'message': 'Не указана подсказка местоположения',
                'action': 'Добавьте информацию о городе, районе или названии улицы в поле "Подсказка"'
            })
        
        # Проверка: нет GPS в EXIF
        exif_failed = any(log.get('method') == 'EXIF GPS Metadata' and not log.get('success') for log in detection_log)
        if exif_failed:
            recommendations.append({
                'type': 'no_exif_gps',
                'priority': 'low',
                'message': 'В фотографии отсутствуют GPS метаданные',
                'action': 'Включите геолокацию в настройках камеры для автоматического определения координат'
            })
        
        # Проверка: нет адресов на фото
        ocr_failed = any(log.get('method') == 'OCR Address Detection' and not log.get('success') for log in detection_log)
        if ocr_failed:
            recommendations.append({
                'type': 'no_text_addresses',
                'priority': 'medium',
                'message': 'Не удалось распознать адреса или названия на фото',
                'action': 'Сфотографируйте вывески с названиями улиц, номерами домов или названиями организаций'
            })
        
        # Проверка: все методы провалились
        all_failed = all(not log.get('success', False) for log in detection_log)
        if all_failed:
            recommendations.append({
                'type': 'all_methods_failed',
                'priority': 'critical',
                'message': 'Ни один метод определения координат не сработал',
                'action': 'Попробуйте: 1) Добавить подсказку местоположения, 2) Загрузить более четкое фото с ориентирами, 3) Включить GPS на камере'
            })
        
        # Сортируем по приоритету
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 3))
        
        return recommendations
