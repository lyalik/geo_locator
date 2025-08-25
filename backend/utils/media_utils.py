import os
import cv2
import numpy as np
from typing import Optional, Tuple, List, Dict, Union
import logging
import tempfile
import subprocess
from pathlib import Path
from PIL import Image, ImageOps, ExifTags
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MediaProcessor:
    """Class for processing images, videos, and panoramas."""
    
    def __init__(self, temp_dir: str = None):
        """Initialize the media processor with an optional temp directory."""
        self.temp_dir = temp_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def process_image(self, image_data: Union[bytes, str], 
                     target_size: Tuple[int, int] = (1024, 1024),
                     detect_features: bool = True) -> Dict:
        """
        Process an image file or binary data.
        
        Args:
            image_data: Either file path or binary data
            target_size: Target size for resizing (width, height)
            detect_features: Whether to detect features in the image
            
        Returns:
            Dict containing processed image and metadata
        """
        try:
            # Load image from path or binary data
            if isinstance(image_data, str) and os.path.isfile(image_data):
                img = cv2.imread(image_data)
            elif isinstance(image_data, bytes):
                img_array = np.frombuffer(image_data, np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            else:
                raise ValueError("Invalid image data. Provide either a file path or binary data.")
            
            if img is None:
                raise ValueError("Failed to load image")
            
            # Fix orientation based on EXIF data
            img = self._fix_image_orientation(img, image_data)
            
            # Resize image
            img = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)
            
            # Convert to RGB (OpenCV uses BGR by default)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            result = {
                'success': True,
                'image': img,
                'image_rgb': img_rgb,
                'size': (img.shape[1], img.shape[0]),  # width, height
                'channels': img.shape[2] if len(img.shape) > 2 else 1
            }
            
            # Detect features if requested
            if detect_features:
                result.update(self._detect_features(img))
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_video(self, video_path: str, 
                     frames_per_second: int = 1,
                     target_size: Tuple[int, int] = (640, 480)) -> Dict:
        """
        Extract frames from a video file.
        
        Args:
            video_path: Path to the video file
            frames_per_second: Number of frames to extract per second
            target_size: Target size for resizing frames (width, height)
            
        Returns:
            Dict containing extracted frames and metadata
        """
        try:
            if not os.path.isfile(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            # Open video file
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise ValueError(f"Could not open video: {video_path}")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            # Calculate frame interval
            frame_interval = max(1, int(round(fps / frames_per_second)))
            
            frames = []
            frame_timestamps = []
            frame_index = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Only process frames at the specified interval
                if frame_index % frame_interval == 0:
                    # Resize frame
                    frame = cv2.resize(frame, target_size, interpolation=cv2.INTER_AREA)
                    
                    # Convert to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    frames.append({
                        'frame': frame,
                        'frame_rgb': frame_rgb,
                        'frame_index': frame_index,
                        'timestamp': frame_index / fps if fps > 0 else 0
                    })
                    
                    frame_timestamps.append(frame_index / fps if fps > 0 else 0)
                
                frame_index += 1
            
            cap.release()
            
            return {
                'success': True,
                'frames': frames,
                'frame_timestamps': frame_timestamps,
                'frame_count': len(frames),
                'original_frame_count': frame_count,
                'fps': fps,
                'duration': duration,
                'resolution': (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 
                             int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            }
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_panorama(self, images: List[Union[str, bytes, np.ndarray]], 
                       method: str = 'opencv') -> Dict:
        """
        Create a panorama from multiple images.
        
        Args:
            images: List of image paths, binary data, or numpy arrays
            method: Stitching method ('opencv' or 'hugin')
            
        Returns:
            Dict containing the stitched panorama and metadata
        """
        try:
            if not images or len(images) < 2:
                raise ValueError("At least two images are required to create a panorama")
            
            # Process all images
            processed_images = []
            for img in images:
                if isinstance(img, str) and os.path.isfile(img):
                    processed = self.process_image(img, detect_features=True)
                elif isinstance(img, bytes) or isinstance(img, np.ndarray):
                    processed = self.process_image(img, detect_features=True)
                else:
                    raise ValueError(f"Unsupported image type: {type(img)}")
                
                if not processed.get('success'):
                    raise ValueError(f"Failed to process image: {processed.get('error')}")
                
                processed_images.append(processed)
            
            if method == 'opencv':
                return self._stitch_with_opencv(processed_images)
            elif method == 'hugin':
                return self._stitch_with_hugin(processed_images)
            else:
                raise ValueError(f"Unsupported stitching method: {method}")
                
        except Exception as e:
            logger.error(f"Error creating panorama: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _stitch_with_opencv(self, processed_images: List[Dict]) -> Dict:
        """Stitch images using OpenCV's built-in stitcher."""
        try:
            # Extract images
            images = [img['image'] for img in processed_images]
            
            # Create stitcher
            stitcher = cv2.Stitcher_create()
            status, panorama = stitcher.stitch(images)
            
            if status != cv2.Stitcher_OK:
                raise ValueError(f"Stitching failed with status: {status}")
            
            return {
                'success': True,
                'panorama': panorama,
                'method': 'opencv',
                'image_count': len(images)
            }
            
        except Exception as e:
            logger.error(f"OpenCV stitching error: {str(e)}")
            raise
    
    def _stitch_with_hugin(self, processed_images: List[Dict]) -> Dict:
        """Stitch images using Hugin (external tool)."""
        try:
            # Create temporary directory for processing
            with tempfile.TemporaryDirectory(dir=self.temp_dir) as temp_dir:
                temp_dir_path = Path(temp_dir)
                
                # Save images to temp directory
                image_paths = []
                for i, img_data in enumerate(processed_images):
                    img_path = temp_dir_path / f"img_{i:03d}.jpg"
                    cv2.imwrite(str(img_path), img_data['image'])
                    image_paths.append(str(img_path))
                
                # Output file
                output_path = temp_dir_path / "panorama.jpg"
                
                # Build Hugin command
                cmd = [
                    'hugin_executor',
                    '--stitching',
                    '--output', str(output_path)
                ]
                cmd.extend(image_paths)
                
                # Run Hugin
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=temp_dir
                )
                
                if result.returncode != 0:
                    raise RuntimeError(f"Hugin failed with error: {result.stderr}")
                
                if not output_path.exists():
                    raise FileNotFoundError("Hugin did not produce an output file")
                
                # Load and return the panorama
                panorama = cv2.imread(str(output_path))
                
                return {
                    'success': True,
                    'panorama': panorama,
                    'method': 'hugin',
                    'image_count': len(processed_images)
                }
                
        except Exception as e:
            logger.error(f"Hugin stitching error: {str(e)}")
            raise
    
    def _fix_image_orientation(self, img: np.ndarray, image_data: Union[bytes, str]) -> np.ndarray:
        """Fix image orientation based on EXIF data."""
        try:
            # Convert to PIL Image for EXIF handling
            if isinstance(image_data, bytes):
                image_pil = Image.open(io.BytesIO(image_data))
            else:
                image_pil = Image.open(image_data)
            
            # Check for EXIF data
            if hasattr(image_pil, '_getexif') and image_pil._getexif() is not None:
                exif = {ExifTags.TAGS[k]: v for k, v in image_pil._getexif().items() 
                       if k in ExifTags.TAGS}
                
                # Get orientation
                orientation = exif.get('Orientation', 1)
                
                # Apply orientation correction
                if orientation == 2:
                    img = cv2.flip(img, 0)  # vertical flip
                elif orientation == 3:
                    img = cv2.rotate(img, cv2.ROTATE_180)
                elif orientation == 4:
                    img = cv2.rotate(img, cv2.ROTATE_180)
                    img = cv2.flip(img, 0)  # vertical flip
                elif orientation == 5:
                    img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                    img = cv2.flip(img, 0)  # vertical flip
                elif orientation == 6:
                    img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                elif orientation == 7:
                    img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    img = cv2.flip(img, 0)  # vertical flip
                elif orientation == 8:
                    img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            
            return img
            
        except Exception as e:
            logger.warning(f"Could not fix image orientation: {str(e)}")
            return img
    
    def _detect_features(self, img: np.ndarray) -> Dict:
        """Detect features in an image."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Initialize feature detector
            orb = cv2.ORB_create()
            
            # Detect keypoints and descriptors
            keypoints, descriptors = orb.detectAndCompute(gray, None)
            
            # Draw keypoints on image
            img_with_keypoints = cv2.drawKeypoints(
                img, keypoints, None, 
                flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS
            )
            
            return {
                'keypoints': keypoints,
                'descriptors': descriptors,
                'keypoint_count': len(keypoints),
                'image_with_keypoints': img_with_keypoints
            }
            
        except Exception as e:
            logger.warning(f"Feature detection failed: {str(e)}")
            return {
                'keypoints': [],
                'descriptors': None,
                'keypoint_count': 0,
                'image_with_keypoints': img.copy()
            }


def extract_metadata(file_path: str) -> Dict:
    """Extract metadata from an image or video file."""
    try:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check file type
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in ('.jpg', '.jpeg', '.png', '.tiff', '.webp'):
            return _extract_image_metadata(file_path)
        elif file_ext in ('.mp4', '.mov', '.avi', '.mkv'):
            return _extract_video_metadata(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
            
    except Exception as e:
        logger.error(f"Error extracting metadata: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def _extract_image_metadata(file_path: str) -> Dict:
    """Extract metadata from an image file."""
    try:
        with Image.open(file_path) as img:
            # Basic metadata
            metadata = {
                'type': 'image',
                'format': img.format,
                'size': img.size,  # (width, height)
                'mode': img.mode,
                'info': img.info,
                'has_exif': hasattr(img, '_getexif') and img._getexif() is not None
            }
            
            # Extract EXIF data if available
            if metadata['has_exif']:
                exif_data = {}
                for tag, value in img._getexif().items():
                    decoded = ExifTags.TAGS.get(tag, tag)
                    exif_data[decoded] = value
                
                # Process GPS info if available
                if 'GPSInfo' in exif_data:
                    gps_info = {}
                    for tag in exif_data['GPSInfo'].keys():
                        decoded = ExifTags.GPSTAGS.get(tag, tag)
                        gps_info[decoded] = exif_data['GPSInfo'][tag]
                    exif_data['GPSInfo'] = gps_info
                
                metadata['exif'] = exif_data
            
            return {
                'success': True,
                'metadata': metadata
            }
            
    except Exception as e:
        raise Exception(f"Failed to extract image metadata: {str(e)}")


def _extract_video_metadata(file_path: str) -> Dict:
    """Extract metadata from a video file."""
    try:
        # Use OpenCV to get basic video info
        cap = cv2.VideoCapture(file_path)
        
        if not cap.isOpened():
            raise ValueError("Could not open video file")
        
        # Get video properties
        metadata = {
            'type': 'video',
            'frame_width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'frame_height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS) if cap.get(cv2.CAP_PROP_FPS) > 0 else 0,
            'codec': int(cap.get(cv2.CAP_PROP_FOURCC)),
            'format': int(cap.get(cv2.CAP_PROP_FORMAT))
        }
        
        cap.release()
        
        # Try to get additional metadata using ffprobe if available
        try:
            import subprocess
            import json
            
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                ffprobe_data = json.loads(result.stdout)
                metadata['ffprobe'] = ffprobe_data
        except Exception as e:
            logger.warning(f"Could not get ffprobe metadata: {str(e)}")
        
        return {
            'success': True,
            'metadata': metadata
        }
        
    except Exception as e:
        raise Exception(f"Failed to extract video metadata: {str(e)}")
    finally:
        if 'cap' in locals() and cap.isOpened():
            cap.release()
