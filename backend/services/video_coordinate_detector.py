import os
import logging
import cv2
import tempfile
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
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
        logger.info("Video Coordinate Detector initialized")
    
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
            Dictionary containing analysis results
        """
        try:
            # Validate video file
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            file_ext = os.path.splitext(video_path)[1].lower()
            if file_ext not in self.supported_formats:
                raise ValueError(f"Unsupported video format: {file_ext}")
            
            # Check cache first
            cache_key = f"video_{os.path.basename(video_path)}_{frame_interval}_{max_frames}"
            cached_result = DetectionCache.get_cached_detection_result(video_path, cache_key)
            if cached_result:
                logger.debug(f"Cache hit for video analysis: {video_path}")
                return cached_result
            
            # Extract frames from video
            frames_data = self._extract_frames(video_path, frame_interval, max_frames)
            
            if not frames_data['frames']:
                return {
                    'success': False,
                    'error': 'No frames could be extracted from video',
                    'video_info': frames_data['video_info']
                }
            
            # Process each frame for coordinate detection
            frame_results = []
            all_objects = []
            coordinate_candidates = []
            
            for frame_info in frames_data['frames']:
                frame_result = self.coordinate_detector.detect_coordinates_from_image(
                    frame_info['path'], location_hint
                )
                
                frame_result['timestamp'] = frame_info['timestamp']
                frame_result['frame_number'] = frame_info['frame_number']
                frame_results.append(frame_result)
                
                # Collect objects and coordinates
                if frame_result['success']:
                    objects = frame_result.get('objects', [])
                    for obj in objects:
                        obj['frame_number'] = frame_info['frame_number']
                        obj['timestamp'] = frame_info['timestamp']
                    all_objects.extend(objects)
                    
                    if frame_result.get('coordinates'):
                        coord = frame_result['coordinates'].copy()
                        coord['frame_number'] = frame_info['frame_number']
                        coord['timestamp'] = frame_info['timestamp']
                        coordinate_candidates.append(coord)
            
            # Determine best coordinates from all frames
            best_coordinates = self._determine_best_coordinates(coordinate_candidates)
            
            # Aggregate object statistics
            object_stats = self._aggregate_object_statistics(all_objects)
            
            # Create summary
            result = {
                'success': True,
                'video_info': frames_data['video_info'],
                'coordinates': best_coordinates,
                'frame_results': frame_results,
                'total_frames_processed': len(frame_results),
                'successful_frames': len([r for r in frame_results if r['success']]),
                'total_objects_detected': len(all_objects),
                'object_statistics': object_stats,
                'processing_parameters': {
                    'frame_interval': frame_interval,
                    'max_frames': max_frames,
                    'location_hint': location_hint
                }
            }
            
            # Cache the result
            DetectionCache.cache_detection_result(video_path, result, cache_key)
            
            # Cleanup temporary frame files
            self._cleanup_temp_frames(frames_data['frames'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing video: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'coordinates': None
            }
    
    def _extract_frames(self, video_path: str, frame_interval: int, max_frames: int) -> Dict[str, Any]:
        """Extract frames from video file."""
        frames = []
        video_info = {}
        
        try:
            # Open video file
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise ValueError("Could not open video file")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            video_info = {
                'fps': fps,
                'total_frames': total_frames,
                'duration_seconds': duration,
                'width': width,
                'height': height,
                'file_size': os.path.getsize(video_path)
            }
            
            # Create temporary directory for frames
            temp_dir = tempfile.mkdtemp(prefix='video_frames_')
            
            frame_count = 0
            extracted_count = 0
            
            while cap.isOpened() and extracted_count < max_frames:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # Extract frame at specified interval
                if frame_count % frame_interval == 0:
                    timestamp = frame_count / fps if fps > 0 else 0
                    
                    # Save frame as temporary image
                    frame_filename = f"frame_{frame_count:06d}.jpg"
                    frame_path = os.path.join(temp_dir, frame_filename)
                    
                    cv2.imwrite(frame_path, frame)
                    
                    frames.append({
                        'path': frame_path,
                        'frame_number': frame_count,
                        'timestamp': timestamp,
                        'filename': frame_filename
                    })
                    
                    extracted_count += 1
                
                frame_count += 1
            
            cap.release()
            
            logger.info(f"Extracted {extracted_count} frames from video")
            
            return {
                'frames': frames,
                'video_info': video_info,
                'temp_dir': temp_dir
            }
            
        except Exception as e:
            logger.error(f"Error extracting frames: {str(e)}")
            return {
                'frames': [],
                'video_info': video_info,
                'error': str(e)
            }
    
    def _determine_best_coordinates(self, coordinate_candidates: List[Dict]) -> Optional[Dict[str, Any]]:
        """Determine the best coordinates from multiple frame results."""
        if not coordinate_candidates:
            return None
        
        # Group coordinates by source and calculate confidence
        source_groups = {}
        for coord in coordinate_candidates:
            source = coord.get('source', 'unknown')
            if source not in source_groups:
                source_groups[source] = []
            source_groups[source].append(coord)
        
        # Find most reliable source
        best_source = None
        best_score = 0
        
        for source, coords in source_groups.items():
            # Calculate average confidence and consistency
            confidences = [c.get('confidence', 0) for c in coords]
            avg_confidence = sum(confidences) / len(confidences)
            
            # Calculate coordinate consistency (lower standard deviation is better)
            lats = [c.get('latitude', 0) for c in coords]
            lons = [c.get('longitude', 0) for c in coords]
            
            lat_std = np.std(lats) if len(lats) > 1 else 0
            lon_std = np.std(lons) if len(lons) > 1 else 0
            
            # Consistency score (lower std deviation = higher consistency)
            consistency_score = 1.0 / (1.0 + lat_std + lon_std)
            
            # Combined score
            score = avg_confidence * consistency_score * len(coords)
            
            if score > best_score:
                best_score = score
                best_source = source
        
        if not best_source:
            return coordinate_candidates[0]  # Fallback to first result
        
        # Return average coordinates from best source
        best_coords = source_groups[best_source]
        avg_lat = sum(c.get('latitude', 0) for c in best_coords) / len(best_coords)
        avg_lon = sum(c.get('longitude', 0) for c in best_coords) / len(best_coords)
        avg_confidence = sum(c.get('confidence', 0) for c in best_coords) / len(best_coords)
        
        return {
            'latitude': avg_lat,
            'longitude': avg_lon,
            'confidence': avg_confidence,
            'source': best_source,
            'frame_count': len(best_coords),
            'consistency_score': 1.0 / (1.0 + np.std([c.get('latitude', 0) for c in best_coords]) + 
                                      np.std([c.get('longitude', 0) for c in best_coords]))
        }
    
    def _aggregate_object_statistics(self, all_objects: List[Dict]) -> Dict[str, Any]:
        """Aggregate statistics about detected objects across all frames."""
        if not all_objects:
            return {}
        
        # Count objects by category
        category_counts = {}
        category_confidences = {}
        
        for obj in all_objects:
            category = obj.get('category', 'unknown')
            confidence = obj.get('confidence', 0)
            
            if category not in category_counts:
                category_counts[category] = 0
                category_confidences[category] = []
            
            category_counts[category] += 1
            category_confidences[category].append(confidence)
        
        # Calculate average confidences
        category_avg_confidence = {}
        for category, confidences in category_confidences.items():
            category_avg_confidence[category] = sum(confidences) / len(confidences)
        
        # Find most common objects
        sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate geolocation utility
        total_utility = 0
        for obj in all_objects:
            utility = obj.get('geolocation_utility', 0)
            total_utility += utility
        
        avg_utility = total_utility / len(all_objects) if all_objects else 0
        
        return {
            'total_objects': len(all_objects),
            'unique_categories': len(category_counts),
            'category_counts': category_counts,
            'category_avg_confidence': category_avg_confidence,
            'most_common_objects': sorted_categories[:5],
            'average_geolocation_utility': avg_utility,
            'high_utility_objects': len([obj for obj in all_objects if obj.get('geolocation_utility', 0) > 0.7])
        }
    
    def _cleanup_temp_frames(self, frames: List[Dict]):
        """Clean up temporary frame files."""
        try:
            for frame in frames:
                frame_path = frame.get('path')
                if frame_path and os.path.exists(frame_path):
                    os.remove(frame_path)
            
            # Remove temporary directory if empty
            if frames:
                temp_dir = os.path.dirname(frames[0]['path'])
                if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
                    
        except Exception as e:
            logger.warning(f"Error cleaning up temporary frames: {str(e)}")
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported video formats."""
        return list(self.supported_formats)
    
    def estimate_processing_time(self, video_path: str, frame_interval: int = 30, 
                               max_frames: int = 10) -> Dict[str, Any]:
        """Estimate processing time for a video file."""
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return {'error': 'Could not open video file'}
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            cap.release()
            
            # Estimate frames to be processed
            frames_to_process = min(max_frames, total_frames // frame_interval)
            
            # Estimate processing time (rough estimate: 2-5 seconds per frame)
            estimated_time_per_frame = 3.5  # seconds
            estimated_total_time = frames_to_process * estimated_time_per_frame
            
            return {
                'video_duration': duration,
                'total_frames': total_frames,
                'frames_to_process': frames_to_process,
                'estimated_processing_time': estimated_total_time,
                'frame_interval': frame_interval
            }
            
        except Exception as e:
            return {'error': str(e)}
