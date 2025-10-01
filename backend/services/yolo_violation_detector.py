import os
import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
from ultralytics import YOLO
import torch
from .cache_service import DetectionCache
from .dataset_search_service import DatasetSearchService
from .reference_database_service import ReferenceDatabaseService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YOLOObjectDetector:
    """
    Service for detecting objects in images using YOLOv8 for coordinate determination.
    Focuses on identifying landmarks, buildings, and infrastructure objects.
    """
    
    # Define object categories for geolocation
    OBJECT_CATEGORIES = {
        0: 'building',
        1: 'landmark', 
        2: 'infrastructure',
        3: 'transportation',
        4: 'natural_feature',
        5: 'urban_furniture',
        6: 'signage',
        7: 'monument'
    }
    
    # Category descriptions in Russian
    CATEGORY_DESCRIPTIONS = {
        'building': 'Здание',
        'landmark': 'Достопримечательность',
        'infrastructure': 'Инфраструктура',
        'transportation': 'Транспорт',
        'natural_feature': 'Природный объект',
        'urban_furniture': 'Городская мебель',
        'signage': 'Указатели и знаки',
        'monument': 'Памятник'
    }
    
    # Confidence threshold for detection (lowered for better detection)
    CONFIDENCE_THRESHOLD = 0.25
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the YOLOv8 object detector for geolocation.
        
        Args:
            model_path: Path to a custom trained model. If None, uses YOLOv8n pretrained.
        """
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = self._load_model(model_path)
        self.dataset_search = DatasetSearchService()
        self.reference_db = ReferenceDatabaseService()
        logger.info(f"YOLOv8 Object Detector initialized on {self.device}")
    
    def _load_model(self, model_path: Optional[str] = None):
        """Load the YOLOv8 model."""
        try:
            if model_path and os.path.exists(model_path):
                # Load custom trained model
                model = YOLO(model_path)
                logger.info(f"Loaded custom model from {model_path}")
            else:
                # Use pretrained YOLOv8n model for general object detection
                # In production, this should be replaced with a model trained on violation data
                model = YOLO('yolov8n.pt')
                logger.info("Loaded pretrained YOLOv8n model")
            
            return model
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            # Fallback to YOLOv8n
            return YOLO('yolov8n.pt')
    
    def detect_objects(self, image_path: str) -> Dict[str, Any]:
        """
        Detect objects in an image for coordinate determination with caching.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing detection results
        """
        # Check cache first
        cached_result = DetectionCache.get_cached_detection_result(image_path, "yolov8")
        if cached_result:
            logger.debug(f"Cache hit for detection {image_path}")
            return cached_result
        
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            # Load and preprocess image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Run inference
            results = self.model(image, conf=self.CONFIDENCE_THRESHOLD)
            
            # Process results
            objects = self._process_detections(results[0], image.shape)
            
            # Create annotated image
            annotated_image_path = self._create_annotated_image(
                image_path, objects
            )
            
            # Поиск похожих объектов в датасете для дообучения
            dataset_matches = []
            enhanced_objects = []
            
            for obj in objects:
                # Улучшаем детекцию с помощью датасета
                if obj['category'] in ['building', 'garbage']:
                    training_data = self.dataset_search.get_training_data(obj['category'])
                    if training_data:
                        # Повышаем уверенность если есть эталонные данные
                        obj['confidence'] = min(0.95, obj['confidence'] + 0.1)
                        obj['dataset_enhanced'] = True
                        dataset_matches.extend(training_data[:3])
                
                enhanced_objects.append(obj)
            
            # Валидация через готовую базу данных заказчика
            validation_result = None
            if hasattr(self, 'reference_db') and self.reference_db:
                # Создаем структуру для валидации
                validation_input = {
                    'violations': [{'category': obj['category']} for obj in enhanced_objects],
                    'coordinates': None  # Координаты будут добавлены позже в геолокации
                }
                # Пока сохраняем для последующей валидации
                validation_result = {'pending': True, 'message': 'Валидация будет выполнена после определения координат'}

            result = {
                'success': True,
                'objects': enhanced_objects,
                'total_objects': len(enhanced_objects),
                'annotated_image_path': annotated_image_path,
                'dataset_matches': dataset_matches,
                'reference_validation': validation_result,
                'model_info': {
                    'model_type': 'YOLOv8 + Dataset + Reference DB',
                    'confidence_threshold': self.CONFIDENCE_THRESHOLD,
                    'device': self.device,
                    'reference_db_records': getattr(self.reference_db, 'total_records', 0)
                }
            }
            
            # Cache the result
            DetectionCache.cache_detection_result(image_path, result, "yolov8")
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting violations: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'objects': [],
                'total_objects': 0
            }
    
    def _process_detections(self, results, image_shape) -> List[Dict[str, Any]]:
        """Process YOLOv8 detection results into object format for geolocation."""
        objects = []
        
        if results.boxes is None:
            return objects
        
        boxes = results.boxes.xyxy.cpu().numpy()
        confidences = results.boxes.conf.cpu().numpy()
        classes = results.boxes.cls.cpu().numpy().astype(int)
        
        height, width = image_shape[:2]
        
        for i, (box, conf, cls) in enumerate(zip(boxes, confidences, classes)):
            # Map YOLO classes to object categories for geolocation
            object_category = self._map_class_to_object(cls)
            
            if object_category:
                x1, y1, x2, y2 = box
                
                detected_object = {
                    'id': i + 1,
                    'category': object_category,
                    'confidence': float(conf),
                    'bbox': {
                        'x1': float(x1),
                        'y1': float(y1),
                        'x2': float(x2),
                        'y2': float(y2),
                        'width': float(x2 - x1),
                        'height': float(y2 - y1)
                    },
                    'bbox_normalized': {
                        'x1': float(x1 / width),
                        'y1': float(y1 / height),
                        'x2': float(x2 / width),
                        'y2': float(y2 / height)
                    },
                    'description': self.CATEGORY_DESCRIPTIONS.get(object_category, object_category),
                    'relevance': self._calculate_geolocation_relevance(conf, object_category),
                    'source': 'yolo'
                }
                objects.append(detected_object)
        
        return objects
    
    def _map_class_to_object(self, yolo_class: int) -> Optional[str]:
        """
        Map YOLO class IDs to object categories for geolocation.
        Focus on objects useful for coordinate determination.
        """
        # YOLO COCO classes mapped to geolocation-relevant objects
        object_mapping = {
            0: 'transportation',    # person (for scale/reference)
            2: 'transportation',    # car
            3: 'transportation',    # motorcycle  
            5: 'transportation',    # bus
            6: 'transportation',    # train
            7: 'transportation',    # truck
            8: 'transportation',    # boat
            9: 'infrastructure',    # traffic light
            10: 'infrastructure',   # fire hydrant
            11: 'signage',          # stop sign
            12: 'signage',          # parking meter
            13: 'urban_furniture',  # bench
            14: 'building',         # bird (on buildings)
            15: 'natural_feature',  # cat
            16: 'natural_feature',  # dog
            17: 'transportation',   # horse
            18: 'natural_feature',  # sheep
            19: 'natural_feature',  # cow
            20: 'natural_feature',  # elephant
            21: 'natural_feature',  # bear
            22: 'natural_feature',  # zebra
            23: 'natural_feature',  # giraffe
            24: 'urban_furniture',  # backpack
            25: 'urban_furniture',  # umbrella
            26: 'urban_furniture',  # handbag
            27: 'urban_furniture',  # tie
            28: 'transportation',   # suitcase
            29: 'transportation',   # frisbee
            30: 'transportation',   # skis
            31: 'transportation',   # snowboard
            32: 'transportation',   # sports ball
            33: 'transportation',   # kite
            34: 'transportation',   # baseball bat
            35: 'transportation',   # baseball glove
            36: 'transportation',   # skateboard
            37: 'transportation',   # surfboard
            38: 'transportation',   # tennis racket
            39: 'urban_furniture',  # bottle
            40: 'urban_furniture',  # wine glass
            41: 'urban_furniture',  # cup
            42: 'urban_furniture',  # fork
            43: 'urban_furniture',  # knife
            44: 'urban_furniture',  # spoon
            45: 'urban_furniture',  # bowl
            46: 'natural_feature',  # banana
            47: 'natural_feature',  # apple
            48: 'natural_feature',  # sandwich
            49: 'natural_feature',  # orange
            50: 'natural_feature',  # broccoli
            51: 'natural_feature',  # carrot
            52: 'natural_feature',  # hot dog
            53: 'natural_feature',  # pizza
            54: 'natural_feature',  # donut
            55: 'natural_feature',  # cake
            56: 'urban_furniture',  # chair
            57: 'urban_furniture',  # couch
            58: 'natural_feature',  # potted plant
            59: 'urban_furniture',  # bed
            60: 'urban_furniture',  # dining table
            61: 'urban_furniture',  # toilet
            62: 'infrastructure',   # tv
            63: 'infrastructure',   # laptop
            64: 'infrastructure',   # mouse
            65: 'infrastructure',   # remote
            66: 'infrastructure',   # keyboard
            67: 'infrastructure',   # cell phone
            68: 'infrastructure',   # microwave
            69: 'infrastructure',   # oven
            70: 'infrastructure',   # toaster
            71: 'infrastructure',   # sink
            72: 'infrastructure',   # refrigerator
            73: 'urban_furniture',  # book
            74: 'infrastructure',   # clock
            75: 'natural_feature',  # vase
            76: 'urban_furniture',  # scissors
            77: 'natural_feature',  # teddy bear
            78: 'urban_furniture',  # hair drier
            79: 'urban_furniture',  # toothbrush
        }
        
        return object_mapping.get(yolo_class)
    
    def _calculate_geolocation_relevance(self, confidence: float, category: str) -> str:
        """Calculate object relevance for geolocation based on confidence and category."""
        relevance_weights = {
            'landmark': 1.0,
            'monument': 1.0,
            'building': 0.9,
            'infrastructure': 0.8,
            'signage': 0.7,
            'transportation': 0.6,
            'urban_furniture': 0.5,
            'natural_feature': 0.4
        }
        
        weight = relevance_weights.get(category, 0.5)
        relevance_score = confidence * weight
        
        if relevance_score >= 0.8:
            return 'high'
        elif relevance_score >= 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _create_annotated_image(self, original_image_path: str, objects: List[Dict[str, Any]]) -> str:
        """Create an annotated image with detected objects highlighted."""
        try:
            # Load original image
            image = cv2.imread(original_image_path)
            if image is None:
                return original_image_path
            
            # Convert BGR to RGB for PIL
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            draw = ImageDraw.Draw(pil_image)
            
            # Define colors for different object types
            colors = {
                'building': '#FF0000',         # Red
                'landmark': '#FF8800',        # Orange
                'infrastructure': '#8800FF',   # Purple
                'transportation': '#8B4513',   # Brown
                'natural_feature': '#607D8B',  # Blue Grey
                'urban_furniture': '#FFD700',  # Gold
                'signage': '#DC143C',         # Crimson
                'monument': '#FF1493'         # Deep Pink
            }
            
            # Try to load a font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            # Draw bounding boxes and labels
            for obj in objects:
                bbox = obj['bbox']
                category = obj['category']
                confidence = obj['confidence']
                
                # Get color for this object type
                color = colors.get(category, '#0000FF')  # Default to blue
                
                # Draw bounding box
                draw.rectangle([
                    bbox['x1'], bbox['y1'],
                    bbox['x2'], bbox['y2']
                ], outline=color, width=3)
                
                # Draw label background
                label = f"{obj['description']} ({confidence:.2f})"
                bbox_text = draw.textbbox((bbox['x1'], bbox['y1'] - 25), label, font=font)
                draw.rectangle(bbox_text, fill=color)
                
                # Draw label text
                draw.text((bbox['x1'], bbox['y1'] - 25), label, fill='white', font=font)
                
                # Draw relevance indicator
                relevance_colors = {
                    'high': '#00FF00',     # Green
                    'medium': '#FFFF00',   # Yellow
                    'low': '#FF8800'       # Orange
                }
                relevance_color = relevance_colors.get(obj['relevance'], '#FFFFFF')
                draw.ellipse([
                    bbox['x2'] - 20, bbox['y1'],
                    bbox['x2'], bbox['y1'] + 20
                ], fill=relevance_color, outline='white', width=2)
            
            # Save annotated image
            base_name = os.path.splitext(os.path.basename(original_image_path))[0]
            annotated_path = os.path.join(
                os.path.dirname(original_image_path),
                f"{base_name}_annotated_yolo.jpg"
            )
            
            # Convert back to BGR for OpenCV
            annotated_bgr = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            cv2.imwrite(annotated_path, annotated_bgr)
            
            return annotated_path
            
        except Exception as e:
            logger.error(f"Error creating annotated image: {str(e)}")
            return original_image_path
    
    def batch_detect(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Detect violations in multiple images efficiently.
        
        Args:
            image_paths: List of paths to image files
            
        Returns:
            List of detection results for each image
        """
        results = []
        
        try:
            # YOLOv8 supports batch inference
            batch_results = self.model(image_paths, conf=self.CONFIDENCE_THRESHOLD)
            
            for i, (image_path, result) in enumerate(zip(image_paths, batch_results)):
                try:
                    image = cv2.imread(image_path)
                    if image is None:
                        results.append({
                            'success': False,
                            'error': f'Could not load image: {image_path}',
                            'objects': [],
                            'image_path': image_path
                        })
                        continue
                    
                    objects = self._process_detections(result, image.shape)
                    annotated_image_path = self._create_annotated_image(image_path, objects)
                    
                    results.append({
                        'success': True,
                        'objects': objects,
                        'total_objects': len(objects),
                        'annotated_image_path': annotated_image_path,
                        'image_path': image_path
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing {image_path}: {str(e)}")
                    results.append({
                        'success': False,
                        'error': str(e),
                        'objects': [],
                        'image_path': image_path
                    })
            
        except Exception as e:
            logger.error(f"Error in batch detection: {str(e)}")
            # Fallback to individual processing
            for image_path in image_paths:
                result = self.detect_objects(image_path)
                result['image_path'] = image_path
                results.append(result)
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            'model_type': 'YOLOv8',
            'framework': 'Ultralytics',
            'device': self.device,
            'confidence_threshold': self.CONFIDENCE_THRESHOLD,
            'supported_categories': list(self.CATEGORY_DESCRIPTIONS.keys()),
            'total_categories': len(self.CATEGORY_DESCRIPTIONS)
        }


# Alias for backward compatibility
YOLOViolationDetector = YOLOObjectDetector
