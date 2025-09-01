import os
import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
from ultralytics import YOLO
import torch
from .cache_service import DetectionCache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YOLOViolationDetector:
    """
    Service for detecting property violations in images using YOLOv8.
    Improved performance and accuracy compared to Faster R-CNN.
    """
    
    # Define violation categories
    VIOLATION_CATEGORIES = {
        0: 'illegal_construction',
        1: 'unauthorized_signage', 
        2: 'blocked_entrance',
        3: 'improper_waste_disposal',
        4: 'unauthorized_modification',
        5: 'parking_violation',
        6: 'structural_damage',
        7: 'unsafe_conditions'
    }
    
    # Category descriptions in Russian
    CATEGORY_DESCRIPTIONS = {
        'illegal_construction': 'Незаконное строительство',
        'unauthorized_signage': 'Несанкционированные вывески',
        'blocked_entrance': 'Заблокированный вход',
        'improper_waste_disposal': 'Неправильная утилизация отходов',
        'unauthorized_modification': 'Несанкционированные изменения',
        'parking_violation': 'Нарушение парковки',
        'structural_damage': 'Структурные повреждения',
        'unsafe_conditions': 'Небезопасные условия'
    }
    
    # Confidence threshold for detection
    CONFIDENCE_THRESHOLD = 0.5
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the YOLOv8 violation detector.
        
        Args:
            model_path: Path to a custom trained model. If None, uses YOLOv8n pretrained.
        """
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = self._load_model(model_path)
        logger.info(f"YOLOv8 Violation Detector initialized on {self.device}")
    
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
    
    def detect_violations(self, image_path: str) -> Dict[str, Any]:
        """
        Detect violations in an image with caching.
        
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
            violations = self._process_detections(results[0], image.shape)
            
            # Create annotated image
            annotated_image_path = self._create_annotated_image(
                image_path, violations
            )
            
            result = {
                'success': True,
                'violations': violations,
                'total_violations': len(violations),
                'annotated_image_path': annotated_image_path,
                'model_info': {
                    'model_type': 'YOLOv8',
                    'confidence_threshold': self.CONFIDENCE_THRESHOLD,
                    'device': self.device
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
                'violations': [],
                'total_violations': 0
            }
    
    def _process_detections(self, results, image_shape) -> List[Dict[str, Any]]:
        """Process YOLOv8 detection results into violation format."""
        violations = []
        
        if results.boxes is None:
            return violations
        
        boxes = results.boxes.xyxy.cpu().numpy()
        confidences = results.boxes.conf.cpu().numpy()
        classes = results.boxes.cls.cpu().numpy().astype(int)
        
        height, width = image_shape[:2]
        
        for i, (box, conf, cls) in enumerate(zip(boxes, confidences, classes)):
            # Map YOLO classes to violation categories
            # This is a simplified mapping - in production, use a model trained on violation data
            violation_category = self._map_class_to_violation(cls)
            
            if violation_category:
                x1, y1, x2, y2 = box
                
                violation = {
                    'id': i + 1,
                    'category': violation_category,
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
                    'description': self.CATEGORY_DESCRIPTIONS.get(violation_category, violation_category),
                    'severity': self._calculate_severity(conf, violation_category),
                    'source': 'yolo'
                }
                violations.append(violation)
        
        return violations
    
    def _map_class_to_violation(self, yolo_class: int) -> Optional[str]:
        """
        Map YOLO class IDs to violation categories.
        This is a simplified mapping for demonstration.
        In production, train YOLOv8 on violation-specific dataset.
        """
        # YOLO COCO classes that might indicate violations
        violation_mapping = {
            0: 'unauthorized_modification',  # person (might indicate unauthorized access)
            2: 'parking_violation',          # car (in wrong place)
            3: 'parking_violation',          # motorcycle
            5: 'parking_violation',          # bus
            7: 'parking_violation',          # truck
            9: 'blocked_entrance',           # traffic light (blocked)
            11: 'blocked_entrance',          # stop sign (blocked)
            13: 'blocked_entrance',          # bench (blocking entrance)
            15: 'improper_waste_disposal',   # cat (around waste)
            16: 'improper_waste_disposal',   # dog (around waste)
            39: 'improper_waste_disposal',   # bottle
            41: 'improper_waste_disposal',   # cup
            64: 'unauthorized_modification', # potted plant (unauthorized)
            67: 'improper_waste_disposal',   # dining table (dumped furniture)
            72: 'improper_waste_disposal',   # refrigerator (dumped appliance)
        }
        
        return violation_mapping.get(yolo_class)
    
    def _calculate_severity(self, confidence: float, category: str) -> str:
        """Calculate violation severity based on confidence and category."""
        severity_weights = {
            'illegal_construction': 1.0,
            'unsafe_conditions': 0.9,
            'structural_damage': 0.9,
            'blocked_entrance': 0.8,
            'unauthorized_modification': 0.7,
            'parking_violation': 0.6,
            'unauthorized_signage': 0.5,
            'improper_waste_disposal': 0.4
        }
        
        weight = severity_weights.get(category, 0.5)
        severity_score = confidence * weight
        
        if severity_score >= 0.8:
            return 'critical'
        elif severity_score >= 0.6:
            return 'high'
        elif severity_score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _create_annotated_image(self, original_image_path: str, violations: List[Dict[str, Any]]) -> str:
        """Create an annotated image with violation bounding boxes."""
        try:
            # Load original image
            image = cv2.imread(original_image_path)
            if image is None:
                return original_image_path
            
            # Convert BGR to RGB for PIL
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            draw = ImageDraw.Draw(pil_image)
            
            # Define colors for different violation types
            colors = {
                'illegal_construction': '#FF0000',      # Red
                'unauthorized_signage': '#FF8800',     # Orange
                'blocked_entrance': '#8800FF',         # Purple
                'improper_waste_disposal': '#8B4513',  # Brown
                'unauthorized_modification': '#607D8B', # Blue Grey
                'parking_violation': '#FFD700',        # Gold
                'structural_damage': '#DC143C',        # Crimson
                'unsafe_conditions': '#FF1493'         # Deep Pink
            }
            
            # Try to load a font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            # Draw bounding boxes and labels
            for violation in violations:
                bbox = violation['bbox']
                category = violation['category']
                confidence = violation['confidence']
                
                # Get color for this violation type
                color = colors.get(category, '#0000FF')  # Default to blue
                
                # Draw bounding box
                draw.rectangle([
                    bbox['x1'], bbox['y1'],
                    bbox['x2'], bbox['y2']
                ], outline=color, width=3)
                
                # Draw label background
                label = f"{violation['description']} ({confidence:.2f})"
                bbox_text = draw.textbbox((bbox['x1'], bbox['y1'] - 25), label, font=font)
                draw.rectangle(bbox_text, fill=color)
                
                # Draw label text
                draw.text((bbox['x1'], bbox['y1'] - 25), label, fill='white', font=font)
                
                # Draw severity indicator
                severity_colors = {
                    'critical': '#FF0000',
                    'high': '#FF8800', 
                    'medium': '#FFFF00',
                    'low': '#00FF00'
                }
                severity_color = severity_colors.get(violation['severity'], '#FFFFFF')
                draw.ellipse([
                    bbox['x2'] - 20, bbox['y1'],
                    bbox['x2'], bbox['y1'] + 20
                ], fill=severity_color, outline='white', width=2)
            
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
                            'violations': [],
                            'image_path': image_path
                        })
                        continue
                    
                    violations = self._process_detections(result, image.shape)
                    annotated_image_path = self._create_annotated_image(image_path, violations)
                    
                    results.append({
                        'success': True,
                        'violations': violations,
                        'total_violations': len(violations),
                        'annotated_image_path': annotated_image_path,
                        'image_path': image_path
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing {image_path}: {str(e)}")
                    results.append({
                        'success': False,
                        'error': str(e),
                        'violations': [],
                        'image_path': image_path
                    })
            
        except Exception as e:
            logger.error(f"Error in batch detection: {str(e)}")
            # Fallback to individual processing
            for image_path in image_paths:
                result = self.detect_violations(image_path)
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
