from flask import Blueprint, request, jsonify, current_app
import os
import time
import logging
from werkzeug.utils import secure_filename
from services.coordinate_detector import CoordinateDetector
from services.video_coordinate_detector import VideoCoordinateDetector
from models import db, Photo, Violation, DetectedObject

# Configure logging
logger = logging.getLogger(__name__)

# Import Image Database Service
try:
    from services.image_database_service import ImageDatabaseService
    image_db_service = ImageDatabaseService()
except ImportError as e:
    logger.warning(f"ImageDatabaseService not available: {e}")
    image_db_service = None

# Import Reference Database Service
try:
    from services.reference_database_service import ReferenceDatabaseService
    reference_db_service = ReferenceDatabaseService()
except ImportError as e:
    logger.warning(f"ReferenceDatabaseService not available: {e}")
    reference_db_service = None

# Create blueprint
bp = Blueprint('coordinate_api', __name__, url_prefix='/api/coordinates')

# Lazy initialization of detectors (will be created on first use)
_coordinate_detector = None
_video_detector = None

def get_coordinate_detector():
    """Get or create coordinate detector instance."""
    global _coordinate_detector
    if _coordinate_detector is None:
        _coordinate_detector = CoordinateDetector()
        logger.info("📍 Coordinate detector instance created for API")
    return _coordinate_detector

def get_video_detector():
    """Get or create video detector instance."""
    global _video_detector
    if _video_detector is None:
        _video_detector = VideoCoordinateDetector()
        logger.info("🎥 Video detector instance created for API")
    return _video_detector

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'}

def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_video_file(filename):
    """Check if file has allowed video extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in VIDEO_EXTENSIONS

@bp.route('/detect', methods=['POST'])
def detect_coordinates():
    """
    Detect objects and determine coordinates from uploaded image.
    
    Expected form data:
    - image: Image file
    - location_hint: Optional location hint string
    
    Returns:
    JSON response with detected objects and coordinates
    """
    try:
        logger.info(f"📥 Coordinate detection request - files: {list(request.files.keys())}, form: {list(request.form.keys())}")
        
        # Check if image file is provided
        if 'file' not in request.files:
            logger.error(f"❌ Missing file in request. Available files: {list(request.files.keys())}")
            return jsonify({
                'success': False,
                'message': 'No image file provided',
                'error': 'MISSING_IMAGE'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No image file selected',
                'error': 'EMPTY_FILENAME'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': 'Invalid file type. Allowed types: png, jpg, jpeg, gif, bmp, webp',
                'error': 'INVALID_FILE_TYPE'
            }), 400
        
        # Get location hint if provided
        location_hint = request.form.get('location_hint')
        
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'coordinates')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Add to Image Database for future similarity matching
        if image_db_service:
            try:
                logger.info(f"📸 Coordinates: Adding image to database: {filename}")
                image_db_result = image_db_service.add_image(
                    file_path, 
                    user_notes=f"Coordinate analysis - {location_hint or 'No location hint'}"
                )
                if image_db_result.get('success'):
                    logger.info(f"✅ Coordinates: Image added to database: {image_db_result.get('image_id')}")
                else:
                    logger.warning(f"⚠️ Coordinates: Failed to add image to database: {image_db_result.get('error')}")
            except Exception as e:
                logger.error(f"❌ Coordinates: Error adding image to database: {e}")
        
        # Process the image with coordinate detector
        start_time = time.time()
        result = get_coordinate_detector().detect_coordinates_from_image(file_path, location_hint)
        processing_time = time.time() - start_time
        logger.info(f"Coordinate detection result: success={result.get('success')}, coordinates={result.get('coordinates') is not None}, processing_time={processing_time:.2f} seconds")
        
        if result['success']:
            # Save to database if coordinates were found
            coordinates = result.get('coordinates')
            if coordinates:
                try:
                    # Create photo record
                    photo = Photo(
                        file_path=file_path,
                        user_id=1,  # Default user for coordinate detection
                        lat=coordinates['latitude'],
                        lon=coordinates['longitude'],
                        address_data={
                            'coordinate_source': coordinates.get('source', 'coordinate_detector'),
                            'confidence': coordinates.get('confidence', 0.7),
                            'location_hint': location_hint
                        }
                    )
                    db.session.add(photo)
                    
                    # НЕ создаем записи в таблице Violation для координатного анализа
                    # Объекты сохраняются только в metadata фото для справки
                    # Violation записи создаются только при ИИ-анализе нарушений
                    
                    db.session.commit()
                    
                    result['photo_id'] = photo.id
                    
                except Exception as e:
                    logger.error(f"Error saving to database: {str(e)}")
                    db.session.rollback()
        
        # Search reference database if coordinates found
        if result['success'] and result.get('coordinates') and reference_db_service:
            try:
                coords = result['coordinates']
                lat = coords.get('latitude')
                lon = coords.get('longitude')
                
                if lat and lon:
                    logger.info(f"🔍 Searching reference database for coordinates: ({lat}, {lon})")
                    reference_matches = reference_db_service.search_by_coordinates(
                        lat, lon, radius_km=0.1
                    )
                    result['reference_matches'] = reference_matches
                    result['reference_count'] = len(reference_matches)
                    logger.info(f"✅ Found {len(reference_matches)} reference matches")
            except Exception as e:
                logger.error(f"❌ Reference database search error: {e}")
        
        # Clean result data for JSON serialization
        def clean_data(obj):
            if isinstance(obj, bytes):
                return None  # Skip bytes objects
            elif isinstance(obj, dict):
                return {k: clean_data(v) for k, v in obj.items() if clean_data(v) is not None}
            elif isinstance(obj, list):
                return [clean_data(item) for item in obj if clean_data(item) is not None]
            else:
                return obj
        
        clean_result = clean_data(result)
        
        response_data = {
            'success': result['success'],
            'message': f"Detected {result.get('total_objects', 0)} objects" if result['success'] else result.get('error', 'Detection failed'),
            'data': clean_result,
            'error': result.get('error')
        }
        
        logger.info(f"API response: success={response_data['success']}, message='{response_data['message']}'")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in coordinate detection endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error during coordinate detection',
            'error': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/batch', methods=['POST'])
def batch_detect_coordinates():
    """
    Detect coordinates for multiple images.
    
    Expected form data:
    - images: Multiple image files
    - location_hints: Optional JSON array of location hints
    
    Returns:
    JSON response with results for each image
    """
    try:
        # Check if image files are provided
        if 'images' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No image files provided',
                'error': 'MISSING_IMAGES'
            }), 400
        
        files = request.files.getlist('images')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({
                'success': False,
                'message': 'No valid image files selected',
                'error': 'EMPTY_FILES'
            }), 400
        
        # Get location hints if provided
        location_hints_json = request.form.get('location_hints')
        location_hints = None
        if location_hints_json:
            try:
                import json
                location_hints = json.loads(location_hints_json)
            except:
                pass
        
        # Save uploaded files
        upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'coordinates')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_paths = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                file_paths.append(file_path)
                
                # Add to Image Database for future similarity matching
                if image_db_service:
                    try:
                        logger.info(f"📸 Batch Coordinates: Adding image to database: {filename}")
                        image_db_result = image_db_service.add_image(
                            file_path, 
                            user_notes=f"Batch coordinate analysis - {location_hint or 'No location hint'}"
                        )
                        if image_db_result.get('success'):
                            logger.info(f"✅ Batch Coordinates: Image added to database: {image_db_result.get('image_id')}")
                    except Exception as e:
                        logger.error(f"❌ Batch Coordinates: Error adding image to database: {e}")
        
        if not file_paths:
            return jsonify({
                'success': False,
                'message': 'No valid image files to process',
                'error': 'NO_VALID_FILES'
            }), 400
        
        # Batch detect coordinates
        results = get_coordinate_detector().batch_detect_coordinates(file_paths, location_hints)
        
        # Save successful results to database
        saved_count = 0
        for result in results:
            if result['success'] and result.get('coordinates'):
                try:
                    coordinates = result['coordinates']
                    photo = Photo(
                        file_path=result['image_path'],
                        lat=coordinates['latitude'],
                        lon=coordinates['longitude'],
                        address_data={
                            'coordinate_source': coordinates['source'],
                            'confidence': coordinates['confidence']
                        }
                    )
                    db.session.add(photo)
                    
                    # Add objects as detections
                    objects = result.get('objects', [])
                    for obj in objects:
                        detection = Violation(
                            photo=photo,
                            category=obj['category'],
                            confidence=obj['confidence'],
                            bbox_data=obj['bbox']
                        )
                        db.session.add(detection)
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Error saving batch result: {str(e)}")
        
        if saved_count > 0:
            try:
                db.session.commit()
            except Exception as e:
                logger.error(f"Error committing batch results: {str(e)}")
                db.session.rollback()
        
        successful_results = [r for r in results if r['success']]
        
        return jsonify({
            'success': True,
            'message': f"Processed {len(results)} images, {len(successful_results)} successful",
            'data': {
                'results': results,
                'total_processed': len(results),
                'successful': len(successful_results),
                'saved_to_database': saved_count
            }
        })
        
    except Exception as e:
        logger.error(f"Error in batch coordinate detection: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error during batch coordinate detection',
            'error': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/statistics', methods=['GET'])
def get_detection_statistics():
    """
    Get coordinate detection system statistics.
    
    Returns:
    JSON response with system information and capabilities
    """
    try:
        stats = get_coordinate_detector().get_detection_statistics()
        
        # Add database statistics
        total_photos = Photo.query.count()
        total_detections = Violation.query.count()
        
        stats['database_stats'] = {
            'total_photos': total_photos,
            'total_detections': total_detections
        }
        
        return jsonify({
            'success': True,
            'message': 'Detection statistics retrieved',
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting detection statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve detection statistics',
            'error': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/objects/<int:photo_id>', methods=['GET'])
def get_detected_objects(photo_id):
    """
    Get detected objects for a specific photo.
    
    Args:
        photo_id: ID of the photo
        
    Returns:
    JSON response with detected objects and coordinates
    """
    try:
        photo = Photo.query.get_or_404(photo_id)
        
        # Get all detections for this photo
        detections = Violation.query.filter_by(photo_id=photo.id).all()
        
        objects = []
        for detection in detections:
            objects.append({
                'id': detection.id,
                'category': detection.category,
                'confidence': detection.confidence,
                'bbox': detection.bbox_data,
                'description': get_coordinate_detector().yolo_detector.CATEGORY_DESCRIPTIONS.get(
                    detection.category, detection.category
                ) if get_coordinate_detector().yolo_detector else detection.category
            })
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(objects)} detected objects',
            'data': {
                'photo_id': photo.id,
                'coordinates': {
                    'latitude': photo.lat,
                    'longitude': photo.lon
                },
                'objects': objects,
                'total_objects': len(objects),
                'file_path': photo.file_path,
                'created_at': photo.created_at.isoformat() + 'Z'
            }
        })
        
    except Exception as e:
        logger.error(f"Error retrieving detected objects: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve detected objects',
            'error': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/video/analyze', methods=['POST'])
def analyze_video():
    """
    Analyze video file to detect objects and determine coordinates.
    
    Expected form data:
    - video: Video file
    - location_hint: Optional location hint string
    - frame_interval: Optional frame extraction interval (default: 30)
    - max_frames: Optional maximum frames to process (default: 10)
    
    Returns:
    JSON response with video analysis results
    """
    try:
        logger.info(f"📥 Video analysis request - files: {list(request.files.keys())}, form: {list(request.form.keys())}")
        
        # Check if video file is provided
        if 'file' not in request.files:
            logger.error(f"❌ Missing file in request. Available files: {list(request.files.keys())}")
            return jsonify({
                'success': False,
                'message': 'No video file provided',
                'error': 'MISSING_VIDEO'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No video file selected',
                'error': 'EMPTY_FILENAME'
            }), 400
        
        if not allowed_video_file(file.filename):
            return jsonify({
                'success': False,
                'message': f'Invalid file type. Allowed types: {", ".join(VIDEO_EXTENSIONS)}',
                'error': 'INVALID_FILE_TYPE'
            }), 400
        
        # Get optional parameters
        location_hint = request.form.get('location_hint')
        frame_interval = int(request.form.get('frame_interval', 30))
        max_frames = int(request.form.get('max_frames', 10))
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'videos')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Check video duration (limit to 10 seconds)
        try:
            import cv2
            cap = cv2.VideoCapture(file_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = frame_count / fps if fps > 0 else 0
            cap.release()
            
            logger.info(f"📹 Video duration: {duration:.1f}s (fps: {fps:.1f}, frames: {frame_count})")
            
            if duration > 10.0:
                logger.warning(f"⚠️ Video too long: {duration:.1f}s > 10s limit")
                os.remove(file_path)  # Clean up uploaded file
                return jsonify({
                    'success': False,
                    'message': f'Видео слишком длинное ({duration:.1f}с). Максимальная длительность: 10 секунд',
                    'error': 'VIDEO_TOO_LONG',
                    'duration': duration
                }), 400
                
        except Exception as e:
            logger.error(f"❌ Error checking video duration: {str(e)}")
            # Continue processing even if duration check fails
        
        # Analyze video with logging
        logger.info(f"🎬 Starting video analysis: {filename} (frame_interval={frame_interval}, max_frames={max_frames})")
        start_time = time.time()
        
        result = video_detector.analyze_video(
            file_path, location_hint, frame_interval, max_frames
        )
        
        duration = time.time() - start_time
        logger.info(f"✅ Video analysis completed in {duration:.1f}s: {result.get('success', False)}")
        
        if result['success']:
            # Save to database if coordinates were found
            coordinates = result.get('coordinates')
            if coordinates:
                try:
                    # Create photo record for video
                    # Use a default user_id of 1 for video analysis (or get from session if available)
                    user_id = getattr(request, 'user_id', 1)  # Default to user 1
                    
                    photo = Photo(
                        file_path=file_path,
                        user_id=user_id,
                        lat=coordinates['latitude'],
                        lon=coordinates['longitude'],
                        address_data={
                            'coordinate_source': coordinates['source'],
                            'confidence': coordinates['confidence'],
                            'location_hint': location_hint,
                            'video_analysis': True,
                            'frame_count': coordinates.get('frame_count', 0)
                        }
                    )
                    db.session.add(photo)
                    
                    # Create object records from video analysis (as DetectedObject, not Violation)
                    object_stats = result.get('object_statistics', {})
                    category_counts = object_stats.get('category_counts', {})
                    category_confidences = object_stats.get('category_avg_confidence', {})
                    
                    for category, count in category_counts.items():
                        confidence = category_confidences.get(category, 0.5)
                        detected_object = DetectedObject(
                            photo=photo,
                            category=category,
                            confidence=confidence,
                            bbox_data={'video_analysis': True, 'detection_count': count}
                        )
                        db.session.add(detected_object)
                    
                    db.session.commit()
                    
                    result['photo_id'] = photo.id
                    
                except Exception as e:
                    logger.error(f"Error saving video analysis to database: {str(e)}")
                    db.session.rollback()
        
        # Clean result from non-serializable objects recursively
        def clean_for_json(obj):
            """Recursively clean object for JSON serialization"""
            import numpy as np
            
            if isinstance(obj, bytes):
                return f"<bytes object of length {len(obj)}>"
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(item) for item in obj]
            elif hasattr(obj, '__dict__'):
                # Handle custom objects by converting to dict
                return clean_for_json(obj.__dict__)
            else:
                return obj
        
        clean_result = clean_for_json(result)
        
        return jsonify({
            'success': result['success'],
            'message': f"Analyzed video with {result.get('total_frames_processed', 0)} frames" if result['success'] else 'Video analysis failed',
            'data': clean_result,
            'error': result.get('error')
        })
        
    except Exception as e:
        logger.error(f"Error in video analysis endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error during video analysis',
            'error': 'INTERNAL_SERVER_ERROR'
        }), 500

@bp.route('/video/estimate', methods=['POST'])
def estimate_video_processing():
    """
    Estimate processing time for video analysis.
    
    Expected form data:
    - video: Video file
    - frame_interval: Optional frame extraction interval (default: 30)
    - max_frames: Optional maximum frames to process (default: 10)
    
    Returns:
    JSON response with processing time estimate
    """
    try:
        if 'video' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No video file provided',
                'error': 'MISSING_VIDEO'
            }), 400
        
        file = request.files['video']
        
        if not allowed_video_file(file.filename):
            return jsonify({
                'success': False,
                'message': f'Invalid file type. Allowed types: {", ".join(VIDEO_EXTENSIONS)}',
                'error': 'INVALID_FILE_TYPE'
            }), 400
        
        # Get optional parameters
        frame_interval = int(request.form.get('frame_interval', 30))
        max_frames = int(request.form.get('max_frames', 10))
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'temp')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Get processing estimate
        estimate = video_detector.estimate_processing_time(file_path, frame_interval, max_frames)
        
        # Clean up temporary file
        try:
            os.remove(file_path)
        except:
            pass
        
        if 'error' in estimate:
            return jsonify({
                'success': False,
                'message': 'Failed to estimate processing time',
                'error': estimate['error']
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Processing time estimated',
            'data': estimate
        })
        
    except Exception as e:
        logger.error(f"Error estimating video processing: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error during estimation',
            'error': 'INTERNAL_SERVER_ERROR'
        }), 500
