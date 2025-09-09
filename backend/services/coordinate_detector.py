import os
import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from PIL import Image
import cv2
from .yolo_violation_detector import YOLOObjectDetector
from .geo_aggregator_service import GeoAggregatorService
from .image_similarity_service import ImageSimilarityService
from .cache_service import DetectionCache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoordinateDetector:
    """
    Service for detecting objects in images and determining their geographic coordinates.
    Combines YOLO object detection with geolocation services for precise coordinate determination.
    """
    
    def __init__(self):
        """Initialize the coordinate detector with required services."""
        self.yolo_detector = YOLOObjectDetector()
        self.geo_aggregator = GeoAggregatorService()
        self.image_similarity = ImageSimilarityService()
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
            # Step 1: Detect objects using YOLO
            detection_result = self.yolo_detector.detect_objects(image_path)
            
            if not detection_result['success']:
                return {
                    'success': False,
                    'error': detection_result.get('error', 'Object detection failed'),
                    'coordinates': None,
                    'objects': []
                }
            
            objects = detection_result['objects']
            
            # Step 2: Extract image metadata (EXIF GPS if available)
            image_coords = self._extract_gps_coordinates(image_path)
            
            # Step 3: Use geolocation services to determine coordinates
            geo_result = None
            if location_hint:
                geo_result = self.geo_aggregator.get_location_info(location_hint)
            
            # Step 4: Try image similarity matching for better accuracy
            similarity_coords = self._find_similar_image_coordinates(image_path)
            
            # Step 5: Combine all coordinate sources
            final_coordinates = self._combine_coordinate_sources(
                image_coords, geo_result, similarity_coords, objects
            )
            
            # Step 6: Enhance objects with geolocation relevance
            enhanced_objects = self._enhance_objects_with_location(objects, final_coordinates)
            
            return {
                'success': True,
                'coordinates': final_coordinates,
                'objects': enhanced_objects,
                'total_objects': len(enhanced_objects),
                'coordinate_sources': {
                    'gps_metadata': image_coords is not None,
                    'geolocation_service': geo_result is not None,
                    'image_similarity': similarity_coords is not None
                },
                'annotated_image_path': detection_result.get('annotated_image_path')
            }
            
        except Exception as e:
            logger.error(f"Error in coordinate detection: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'coordinates': None,
                'objects': []
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
                'source': 'gps_metadata'
            }
            
        except Exception as e:
            logger.debug(f"No GPS data found in image: {str(e)}")
            return None
    
    def _find_similar_image_coordinates(self, image_path: str) -> Optional[Dict[str, float]]:
        """Find coordinates by matching with similar images in database."""
        try:
            # Use image similarity service to find matching images
            similar_images = self.image_similarity.find_similar_images(image_path, limit=3)
            
            if not similar_images:
                return None
            
            # Get coordinates from the most similar image
            best_match = similar_images[0]
            if best_match.get('similarity_score', 0) > 0.8:  # High similarity threshold
                return {
                    'latitude': best_match.get('latitude'),
                    'longitude': best_match.get('longitude'),
                    'source': 'image_similarity',
                    'similarity_score': best_match.get('similarity_score')
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Image similarity matching failed: {str(e)}")
            return None
    
    def _combine_coordinate_sources(self, gps_coords: Optional[Dict], geo_result: Optional[Dict], 
                                  similarity_coords: Optional[Dict], objects: List[Dict]) -> Optional[Dict[str, Any]]:
        """Combine coordinates from different sources with confidence weighting."""
        coordinate_candidates = []
        
        # Add GPS coordinates (highest priority)
        if gps_coords:
            coordinate_candidates.append({
                **gps_coords,
                'confidence': 0.95,
                'priority': 1
            })
        
        # Add geolocation service results
        if geo_result and geo_result.get('success'):
            locations = geo_result.get('locations', [])
            for location in locations[:1]:  # Take best result
                if location.get('coordinates'):
                    coordinate_candidates.append({
                        'latitude': location['coordinates']['lat'],
                        'longitude': location['coordinates']['lon'],
                        'source': 'geolocation_service',
                        'confidence': location.get('confidence', 0.7),
                        'priority': 2
                    })
        
        # Add image similarity coordinates
        if similarity_coords:
            coordinate_candidates.append({
                **similarity_coords,
                'confidence': similarity_coords.get('similarity_score', 0.6) * 0.8,
                'priority': 3
            })
        
        if not coordinate_candidates:
            return None
        
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
            enhanced_obj = obj.copy()
            
            # Add coordinate information
            enhanced_obj['location'] = {
                'latitude': coordinates['latitude'],
                'longitude': coordinates['longitude'],
                'confidence': coordinates['confidence']
            }
            
            # Calculate geolocation utility score
            enhanced_obj['geolocation_utility'] = self._calculate_geolocation_utility(obj)
            
            # Add location context
            enhanced_obj['location_context'] = self._get_location_context(
                obj, coordinates['latitude'], coordinates['longitude']
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
                'signage',
                'transportation',
                'urban_furniture',
                'natural_feature'
            ]
        }
