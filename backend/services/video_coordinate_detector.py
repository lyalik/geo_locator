import os
import logging
import cv2
import tempfile
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from .coordinate_detector import CoordinateDetector
from .cache_service import DetectionCache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoCoordinateDetector:
    """
    Service for analyzing video files to detect objects and determine coordinates.
    Extracts frames from video and processes them for geolocation.
    """
    
    def __init__(self):
        """Initialize the video coordinate detector."""
        self.coordinate_detector = CoordinateDetector()
        self.supported_formats = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
        
        # Frame quality filtering thresholds
        self.brightness_threshold = 30.0  # Minimum average brightness (0-255)
        self.sharpness_threshold = 100.0  # Minimum sharpness (blur detection)
        
        logger.info("Video Coordinate Detector initialized")
    
    def _is_frame_quality_acceptable(self, frame: np.ndarray, min_brightness: float = 30.0, 
                                   blur_threshold: float = 100.0) -> Tuple[bool, Dict[str, float]]:
        """
        Check if frame has acceptable quality for analysis.
        
        Args:
            frame: OpenCV frame (BGR format)
            min_brightness: Minimum average brightness (0-255)
            blur_threshold: Minimum Laplacian variance for sharpness
            
        Returns:
            Tuple of (is_acceptable, quality_metrics)
        """
        try:
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate brightness (average pixel intensity)
            brightness = np.mean(gray)
            
            # Calculate sharpness using Laplacian variance
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Check if frame meets quality criteria
            is_bright_enough = brightness >= min_brightness
            is_sharp_enough = laplacian_var >= blur_threshold
            
            quality_metrics = {
                'brightness': float(brightness),
                'sharpness': float(laplacian_var),
                'is_bright_enough': is_bright_enough,
                'is_sharp_enough': is_sharp_enough
            }
            
            is_acceptable = is_bright_enough and is_sharp_enough
            
            return is_acceptable, quality_metrics
            
        except Exception as e:
            logger.error(f"Error checking frame quality: {str(e)}")
            # If quality check fails, assume frame is acceptable
            return True, {'error': str(e)}
    
    def analyze_video(self, video_path: str, location_hint: Optional[str] = None,
                     frame_interval: int = 30, max_frames: int = 10) -> Dict[str, Any]:
        """
        Analyze video file to detect objects and determine coordinates.
        
        Args:
            video_path: Path to the video file
            location_hint: Optional location hint for better accuracy
            frame_interval: Extract every Nth frame (default: 30)
            max_frames: Maximum number of frames to process (default: 10)
            
        Returns:
            Dictionary with analysis results
        """
        try:
            logger.info(f"Starting video analysis: {video_path}")
            
            # Extract frames from video
            frames_data = self._extract_frames(video_path, frame_interval, max_frames)
            
            if not frames_data['frames']:
                return {
                    'success': False,
                    'error': 'No frames could be extracted from video',
                    'video_info': frames_data['video_info']
                }
            
            # Filter frames by quality before processing
            quality_filtered_frames = []
            quality_stats = {
                'total_frames': len(frames_data['frames']),
                'filtered_frames': 0,
                'quality_metrics': []
            }
            
            for frame_info in frames_data['frames']:
                try:
                    # Load frame for quality check
                    frame = cv2.imread(frame_info['path'])
                    if frame is None:
                        logger.warning(f"Could not load frame: {frame_info['path']}")
                        continue
                    
                    # Check frame quality
                    is_acceptable, quality_metrics = self._is_frame_quality_acceptable(frame)
                    quality_metrics['frame_number'] = frame_info['frame_number']
                    quality_stats['quality_metrics'].append(quality_metrics)
                    
                    if is_acceptable:
                        quality_filtered_frames.append(frame_info)
                        logger.info(f"Frame {frame_info['frame_number']}: brightness={quality_metrics['brightness']:.1f}, sharpness={quality_metrics['sharpness']:.1f} - ACCEPTED")
                    else:
                        quality_stats['filtered_frames'] += 1
                        logger.info(f"Frame {frame_info['frame_number']}: brightness={quality_metrics['brightness']:.1f}, sharpness={quality_metrics['sharpness']:.1f} - FILTERED OUT")
                        
                except Exception as e:
                    logger.error(f"Error checking quality for frame {frame_info['frame_number']}: {str(e)}")
                    # If quality check fails, include frame anyway
                    quality_filtered_frames.append(frame_info)
            
            logger.info(f"Quality filtering: {len(quality_filtered_frames)}/{quality_stats['total_frames']} frames passed quality check")
            
            if not quality_filtered_frames:
                return {
                    'success': False,
                    'error': 'All frames were filtered out due to poor quality (too dark or blurry)',
                    'video_info': frames_data['video_info'],
                    'quality_stats': quality_stats
                }
            
            # Process quality-filtered frames in parallel for better performance
            start_time = time.time()
            frame_results = []
            all_objects = []
            coordinate_candidates = []
            
            # Determine optimal number of workers (max 4 to avoid overloading)
            max_workers = min(4, len(quality_filtered_frames), os.cpu_count() or 1)
            
            def process_single_frame(frame_info):
                """Process a single frame and return results"""
                try:
                    frame_result = self.coordinate_detector.detect_coordinates_from_image(
                        frame_info['path'], location_hint
                    )
                    
                    # Ensure frame_result is a dictionary
                    if not isinstance(frame_result, dict):
                        logger.warning(f"Frame result is not a dict: {type(frame_result)}")
                        frame_result = {
                            'success': False,
                            'error': str(frame_result),
                            'coordinates': None,
                            'objects': []
                        }
                    
                    frame_result['timestamp'] = frame_info['timestamp']
                    frame_result['frame_number'] = frame_info['frame_number']
                    return frame_result
                    
                except Exception as e:
                    logger.error(f"Error processing frame {frame_info['frame_number']}: {str(e)}")
                    return {
                        'success': False,
                        'error': str(e),
                        'coordinates': None,
                        'objects': [],
                        'timestamp': frame_info['timestamp'],
                        'frame_number': frame_info['frame_number']
                    }
            
            # Execute parallel processing on quality-filtered frames
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all frame processing tasks
                future_to_frame = {executor.submit(process_single_frame, frame_info): frame_info 
                                 for frame_info in quality_filtered_frames}
                
                # Collect results as they complete
                for future in as_completed(future_to_frame):
                    frame_result = future.result()
                    frame_results.append(frame_result)
                    
                    # Collect objects and coordinates
                    if frame_result.get('success'):
                        objects = frame_result.get('objects', [])
                        if isinstance(objects, list):
                            for obj in objects:
                                if isinstance(obj, dict):
                                    obj['frame_number'] = frame_result['frame_number']
                                    obj['timestamp'] = frame_result['timestamp']
                            all_objects.extend(objects)
                        
                        coordinates = frame_result.get('coordinates')
                        if coordinates and isinstance(coordinates, dict):
                            coord = coordinates.copy()
                            coord['frame_number'] = frame_result['frame_number']
                            coord['timestamp'] = frame_result['timestamp']
                            coordinate_candidates.append(coord)
                            
            # Sort frame results by frame number to maintain order
            sorted_frame_results = sorted(frame_results, key=lambda x: x.get('frame_number', 0))
            processing_time = time.time() - start_time
            logger.info(f"Parallel processing completed in {processing_time:.2f} seconds")
            
            # Determine best coordinates from all frames
            best_coordinates = self._determine_best_coordinates(coordinate_candidates)
            
            # Aggregate object statistics
            object_stats = self._aggregate_object_statistics(all_objects)
            
            # Determine coordinate sources and confidence
            coordinate_sources = self._analyze_coordinate_sources(coordinate_candidates) if coordinate_candidates else {}
            confidence_score = self._calculate_confidence_score(coordinate_candidates, all_objects) if coordinate_candidates else 0.0
            
            # Create result summary
            result = {
                'success': True,
                'coordinates': best_coordinates,
                'objects': all_objects,
                'total_objects': len(all_objects),
                'frame_results': sorted_frame_results,
                'total_frames_processed': len(frame_results),
                'total_frames_extracted': quality_stats['total_frames'],
                'frames_filtered_out': quality_stats['filtered_frames'],
                'video_info': frames_data['video_info'],
                'processing_time_seconds': processing_time,
                'coordinate_sources': coordinate_sources,
                'confidence_score': confidence_score,
                'quality_stats': quality_stats
            }
            
            # Cleanup temporary frame files
            self._cleanup_temp_frames(frames_data['frames'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing video: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'coordinates': None,
                'objects': [],
                'total_objects': 0
            }
    
    def _determine_best_coordinates(self, coordinate_candidates: List[Dict]) -> Optional[Dict]:
        """Determine the best coordinates from multiple candidates."""
        if not coordinate_candidates:
            return None
        
        # Simple implementation: return the first valid coordinate
        # In a more sophisticated version, we could weight by confidence, consistency, etc.
        for coord in coordinate_candidates:
            if coord and coord.get('latitude') and coord.get('longitude'):
                return coord
        return None
    
    def _aggregate_object_statistics(self, all_objects: List[Dict]) -> Dict:
        """Aggregate statistics from all detected objects."""
        if not all_objects:
            return {'category_counts': {}, 'category_avg_confidence': {}}
        
        category_counts = {}
        category_confidences = {}
        
        for obj in all_objects:
            if isinstance(obj, dict):
                category = obj.get('category', 'unknown')
                confidence = obj.get('confidence', 0.0)
                
                if category not in category_counts:
                    category_counts[category] = 0
                    category_confidences[category] = []
                
                category_counts[category] += 1
                category_confidences[category].append(confidence)
        
        # Calculate average confidences
        category_avg_confidence = {}
        for category, confidences in category_confidences.items():
            category_avg_confidence[category] = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            'category_counts': category_counts,
            'category_avg_confidence': category_avg_confidence
        }
    
    def _analyze_coordinate_sources(self, coordinate_candidates: List[Dict]) -> Dict:
        """Analyze coordinate sources from candidates."""
        if not coordinate_candidates:
            return {}
        
        sources = {}
        for coord in coordinate_candidates:
            if isinstance(coord, dict):
                source = coord.get('source', 'unknown')
                if source not in sources:
                    sources[source] = 0
                sources[source] += 1
        
        return sources
    
    def _calculate_confidence_score(self, coordinate_candidates: List[Dict], all_objects: List[Dict]) -> float:
        """Calculate overall confidence score."""
        if not coordinate_candidates and not all_objects:
            return 0.0
        
        coord_confidence = 0.0
        if coordinate_candidates:
            confidences = [c.get('confidence', 0.0) for c in coordinate_candidates if isinstance(c, dict)]
            coord_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        obj_confidence = 0.0
        if all_objects:
            confidences = [o.get('confidence', 0.0) for o in all_objects if isinstance(o, dict)]
            obj_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Weighted average
        if coordinate_candidates and all_objects:
            return (coord_confidence * 0.7 + obj_confidence * 0.3)
        elif coordinate_candidates:
            return coord_confidence
        else:
            return obj_confidence
    
    def _cleanup_temp_frames(self, frames: List[Dict]):
        """Clean up temporary frame files."""
        for frame_info in frames:
            try:
                frame_path = frame_info.get('path')
                if frame_path and os.path.exists(frame_path):
                    os.remove(frame_path)
                    logger.debug(f"Cleaned up temporary frame: {frame_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup frame {frame_info.get('path')}: {str(e)}")
    
    def _extract_frames(self, video_path: str, frame_interval: int = 30, max_frames: int = 10) -> Dict[str, Any]:
        """Extract frames from video file."""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {
                    'frames': [],
                    'video_info': {'error': 'Could not open video file'},
                    'success': False
                }
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            video_info = {
                'fps': fps,
                'frame_count': frame_count,
                'duration_seconds': duration,
                'width': width,
                'height': height
            }
            
            frames = []
            frame_number = 0
            extracted_count = 0
            
            # Create temporary directory for frames
            temp_dir = tempfile.mkdtemp()
            
            while extracted_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Extract every frame_interval-th frame
                if frame_number % frame_interval == 0:
                    timestamp = frame_number / fps if fps > 0 else 0
                    frame_filename = f"frame_{frame_number:06d}.jpg"
                    frame_path = os.path.join(temp_dir, frame_filename)
                    
                    # Save frame
                    cv2.imwrite(frame_path, frame)
                    
                    frames.append({
                        'path': frame_path,
                        'frame_number': frame_number,
                        'timestamp': timestamp
                    })
                    
                    extracted_count += 1
                
                frame_number += 1
            
            cap.release()
            
            return {
                'frames': frames,
                'video_info': video_info,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error extracting frames: {str(e)}")
            return {
                'frames': [],
                'video_info': {'error': str(e)},
                'success': False
            }
