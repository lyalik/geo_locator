import os
import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import torch
from torchvision import transforms
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ViolationDetector:
    """
    Service for detecting property violations in images using computer vision.
    Uses a pre-trained Faster R-CNN model for object detection.
    """
    
    # Define violation categories (simplified for demo - should be expanded based on requirements)
    VIOLATION_CATEGORIES = {
        0: 'background',  # Background class (not a violation)
        1: 'illegal_construction',
        2: 'unauthorized_signage',
        3: 'blocked_entrance',
        4: 'improper_waste_disposal',
        5: 'unauthorized_modification',
    }
    
    # Confidence threshold for detection
    CONFIDENCE_THRESHOLD = 0.7
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the violation detector.
        
        Args:
            model_path: Path to a pre-trained model. If None, uses a default model.
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self._load_model(model_path)
        self.transform = transforms.Compose([
            transforms.ToTensor(),
        ])
    
    def _load_model(self, model_path: Optional[str] = None):
        """Load the detection model."""
        try:
            # Load a pre-trained model for object detection
            model = fasterrcnn_resnet50_fpn(pretrained=True)
            
            # Replace the classifier with a new one for the number of violation categories
            num_classes = len(self.VIOLATION_CATEGORIES)
            in_features = model.roi_heads.box_predictor.cls_score.in_features
            model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
            
            # Load custom weights if provided
            if model_path and os.path.exists(model_path):
                model.load_state_dict(torch.load(model_path, map_location=self.device))
                logger.info(f"Loaded model from {model_path}")
            
            model = model.to(self.device)
            model.eval()
            return model
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def preprocess_image(self, image_path: str) -> torch.Tensor:
        """Preprocess image for the model."""
        try:
            # Load image
            image = Image.open(image_path).convert("RGB")
            # Apply transformations
            return self.transform(image).unsqueeze(0).to(self.device)
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            raise
    
    def detect_violations(self, image_path: str) -> Dict[str, Any]:
        """
        Detect property violations in an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing detection results
        """
        result = {
            'success': False,
            'violations': [],
            'image_size': None,
            'error': None,
            'annotated_image_path': None
        }
        
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                result['error'] = "Image file not found"
                return result
            
            # Preprocess image
            image_tensor = self.preprocess_image(image_path)
            original_image = Image.open(image_path).convert("RGB")
            result['image_size'] = original_image.size  # (width, height)
            
            # Run inference
            with torch.no_grad():
                predictions = self.model(image_tensor)
            
            # Process predictions
            detections = self._process_predictions(predictions[0], original_image.size)
            
            # Generate annotated image
            annotated_image = self._draw_annotations(original_image.copy(), detections)
            
            # Save annotated image
            base_path, ext = os.path.splitext(image_path)
            output_path = f"{base_path}_annotated{ext}"
            annotated_image.save(output_path)
            
            result.update({
                'success': True,
                'violations': detections,
                'annotated_image_path': output_path
            })
            
        except Exception as e:
            logger.error(f"Error detecting violations: {e}")
            result['error'] = str(e)
        
        return result
    
    def _process_predictions(
        self, 
        predictions: Dict[str, torch.Tensor],
        image_size: Tuple[int, int]
    ) -> List[Dict[str, Any]]:
        """Process model predictions into a more usable format."""
        detections = []
        
        boxes = predictions['boxes'].cpu().numpy()
        labels = predictions['labels'].cpu().numpy()
        scores = predictions['scores'].cpu().numpy()
        
        width, height = image_size
        
        for box, label, score in zip(boxes, labels, scores):
            # Skip detections below confidence threshold
            if score < self.CONFIDENCE_THRESHOLD:
                continue
                
            # Convert box coordinates to percentages of image dimensions
            x1, y1, x2, y2 = box
            
            detection = {
                'category_id': int(label),
                'category': self.VIOLATION_CATEGORIES.get(int(label), 'unknown'),
                'confidence': float(score),
                'bbox': {
                    'x1': float(x1 / width),    # Left (0-1)
                    'y1': float(y1 / height),   # Top (0-1)
                    'x2': float(x2 / width),    # Right (0-1)
                    'y2': float(y2 / height),   # Bottom (0-1)
                    'width': float((x2 - x1) / width),   # Width (0-1)
                    'height': float((y2 - y1) / height), # Height (0-1)
                    'center_x': float((x1 + x2) / (2 * width)),  # Center X (0-1)
                    'center_y': float((y1 + y2) / (2 * height)), # Center Y (0-1)
                },
                'bbox_pixels': {
                    'x1': float(x1),
                    'y1': float(y1),
                    'x2': float(x2),
                    'y2': float(y2),
                    'width': float(x2 - x1),
                    'height': float(y2 - y1),
                    'center_x': float((x1 + x2) / 2),
                    'center_y': float((y1 + y2) / 2),
                }
            }
            
            detections.append(detection)
        
        # Sort by confidence (highest first)
        detections.sort(key=lambda x: x['confidence'], reverse=True)
        
        return detections
    
    def _draw_annotations(
        self, 
        image: Image.Image, 
        detections: List[Dict[str, Any]]
    ) -> Image.Image:
        """Draw detection boxes and labels on the image."""
        try:
            draw = ImageDraw.Draw(image)
            width, height = image.size
            
            # Try to load a font, fall back to default if not available
            try:
                font = ImageFont.truetype("Arial.ttf", 16)
            except IOError:
                font = ImageFont.load_default()
            
            for detection in detections:
                # Get box coordinates in pixels
                box = detection['bbox_pixels']
                x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']
                
                # Draw rectangle
                draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
                
                # Create label text
                label = f"{detection['category']} ({detection['confidence']:.2f})"
                
                # Draw text background
                text_bbox = draw.textbbox((x1, y1 - 20), label, font=font)
                draw.rectangle(text_bbox, fill="red")
                
                # Draw text
                draw.text((x1, y1 - 20), label, fill="white", font=font)
            
            return image
            
        except Exception as e:
            logger.error(f"Error drawing annotations: {e}")
            return image


# Example usage
if __name__ == "__main__":
    # Initialize detector
    detector = ViolationDetector()
    
    # Process an image
    result = detector.detect_violations("path/to/your/image.jpg")
    
    if result['success']:
        print(f"Found {len(result['violations'])} violations:")
        for i, violation in enumerate(result['violations'], 1):
            print(f"{i}. {violation['category']} (confidence: {violation['confidence']:.2f})")
        print(f"Annotated image saved to: {result['annotated_image_path']}")
    else:
        print(f"Error: {result['error']}")
