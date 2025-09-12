from flask import Blueprint, request, jsonify, current_app
import os
import logging
from werkzeug.utils import secure_filename
from services.coordinate_detector import CoordinateDetector
from services.video_coordinate_detector import VideoCoordinateDetector
from models import db, Photo, DetectedObject
import json

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('object_group_api', __name__, url_prefix='/api/object-groups')

# Initialize detectors
coordinate_detector = CoordinateDetector()
video_detector = VideoCoordinateDetector()

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

@bp.route('/analyze', methods=['POST'])
def analyze_object_groups():
    """
    Analyze multiple photo groups representing different objects.
    
    Expected form data:
    - objects: JSON string with object definitions
    - files: Multiple files organized by object groups
    - location_hint: Optional location hint string
    
    Returns:
    JSON response with analysis results for each object group
    """
    try:
        logger.info(f"📥 Object group analysis request - files: {len(request.files)}, form: {list(request.form.keys())}")
        
        # Parse objects data
        objects_json = request.form.get('objects')
        if not objects_json:
            return jsonify({
                'success': False,
                'message': 'No objects data provided',
                'error': 'MISSING_OBJECTS_DATA'
            }), 400
        
        try:
            objects_data = json.loads(objects_json)
        except json.JSONDecodeError:
            return jsonify({
                'success': False,
                'message': 'Invalid objects JSON format',
                'error': 'INVALID_OBJECTS_JSON'
            }), 400
        
        # Get location hint
        location_hint = request.form.get('location_hint')
        
        # Process each object group
        results = []
        upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'object_groups')
        os.makedirs(upload_dir, exist_ok=True)
        
        for obj_data in objects_data:
            object_id = obj_data.get('id')
            object_name = obj_data.get('name', f'Object_{object_id}')
            object_description = obj_data.get('description', '')
            file_keys = obj_data.get('file_keys', [])
            
            logger.info(f"🔍 Processing object: {object_name} with {len(file_keys)} files")
            
            # Collect files for this object
            object_files = []
            for file_key in file_keys:
                if file_key in request.files:
                    file = request.files[file_key]
                    if file and file.filename != '':
                        if allowed_file(file.filename) or allowed_video_file(file.filename):
                            # Save file
                            filename = secure_filename(f"{object_id}_{file.filename}")
                            file_path = os.path.join(upload_dir, filename)
                            file.save(file_path)
                            object_files.append({
                                'path': file_path,
                                'name': file.filename,
                                'type': 'image' if allowed_file(file.filename) else 'video'
                            })
            
            if not object_files:
                results.append({
                    'object_id': object_id,
                    'object_name': object_name,
                    'success': False,
                    'message': 'No valid files found for this object',
                    'error': 'NO_FILES'
                })
                continue
            
            # Analyze object group
            object_result = analyze_single_object_group(
                object_files, object_name, object_description, location_hint
            )
            
            object_result.update({
                'object_id': object_id,
                'object_name': object_name,
                'object_description': object_description,
                'files_processed': len(object_files)
            })
            
            results.append(object_result)
        
        # Calculate overall statistics
        successful_objects = [r for r in results if r.get('success')]
        objects_with_coordinates = [r for r in successful_objects if r.get('coordinates')]
        
        return jsonify({
            'success': True,
            'message': f"Processed {len(results)} objects, {len(objects_with_coordinates)} with coordinates found",
            'data': {
                'objects': results,
                'statistics': {
                    'total_objects': len(results),
                    'successful_objects': len(successful_objects),
                    'objects_with_coordinates': len(objects_with_coordinates),
                    'total_files_processed': sum(r.get('files_processed', 0) for r in results)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error in object group analysis: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error during object group analysis',
            'error': 'INTERNAL_SERVER_ERROR'
        }), 500

def analyze_single_object_group(files, object_name, object_description, location_hint):
    """
    Analyze a single object group with multiple photos/videos.
    
    Args:
        files: List of file dictionaries with 'path', 'name', 'type'
        object_name: Name of the object
        object_description: Description of the object
        location_hint: Location hint for better accuracy
    
    Returns:
        Dictionary with analysis results
    """
    try:
        logger.info(f"🎯 Analyzing object group: {object_name} ({len(files)} files)")
        
        coordinate_candidates = []
        all_objects_detected = []
        analysis_details = []
        
        # Analyze each file in the group
        for file_info in files:
            file_path = file_info['path']
            file_type = file_info['type']
            
            try:
                if file_type == 'image':
                    # Analyze image
                    result = coordinate_detector.detect_coordinates_from_image(file_path, location_hint)
                elif file_type == 'video':
                    # Analyze video
                    result = video_detector.analyze_video(file_path, location_hint)
                else:
                    continue
                
                analysis_details.append({
                    'file_name': file_info['name'],
                    'file_type': file_type,
                    'success': result.get('success', False),
                    'coordinates': result.get('coordinates'),
                    'objects': result.get('objects', []),
                    'confidence': result.get('confidence', 0)
                })
                
                # Collect coordinate candidates
                if result.get('success') and result.get('coordinates'):
                    coordinate_candidates.append({
                        'coordinates': result['coordinates'],
                        'source': f"{file_info['name']} ({result.get('source', 'unknown')})",
                        'confidence': result.get('confidence', 0.5),
                        'file_name': file_info['name']
                    })
                
                # Collect detected objects
                if result.get('objects'):
                    all_objects_detected.extend(result['objects'])
                
            except Exception as e:
                logger.error(f"Error analyzing file {file_info['name']}: {str(e)}")
                analysis_details.append({
                    'file_name': file_info['name'],
                    'file_type': file_type,
                    'success': False,
                    'error': str(e)
                })
        
        # Aggregate coordinates from multiple sources
        final_coordinates = None
        final_confidence = 0
        coordinate_sources = []
        
        if coordinate_candidates:
            final_coordinates, final_confidence, coordinate_sources = aggregate_coordinates(
                coordinate_candidates
            )
        
        # Aggregate object statistics
        object_stats = aggregate_object_statistics(all_objects_detected)
        
        # Save to database if coordinates found
        photo_id = None
        if final_coordinates:
            try:
                photo = Photo(
                    file_path=files[0]['path'],  # Use first file as representative
                    user_id=1,  # Default user
                    lat=final_coordinates['latitude'],
                    lon=final_coordinates['longitude'],
                    address_data={
                        'object_name': object_name,
                        'object_description': object_description,
                        'coordinate_sources': coordinate_sources,
                        'files_count': len(files),
                        'group_analysis': True
                    }
                )
                db.session.add(photo)
                db.session.commit()
                photo_id = photo.id
                
                # Save detected objects
                for category, stats in object_stats.items():
                    detected_object = DetectedObject(
                        photo=photo,
                        category=category,
                        confidence=stats['avg_confidence'],
                        bbox_data={
                            'group_analysis': True,
                            'detection_count': stats['count'],
                            'files_detected': stats['files']
                        }
                    )
                    db.session.add(detected_object)
                
                db.session.commit()
                
            except Exception as e:
                logger.error(f"Error saving object group to database: {str(e)}")
                db.session.rollback()
        
        return {
            'success': bool(final_coordinates),
            'coordinates': final_coordinates,
            'confidence': final_confidence,
            'source': 'multi_photo_analysis',
            'coordinate_sources': coordinate_sources,
            'objects': object_stats,
            'analysis_details': analysis_details,
            'photo_id': photo_id,
            'message': f"Analyzed {len(files)} files, found coordinates from {len(coordinate_candidates)} sources" if final_coordinates else "No coordinates found in any file"
        }
        
    except Exception as e:
        logger.error(f"Error in single object group analysis: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to analyze object group'
        }

def aggregate_coordinates(candidates):
    """
    Aggregate coordinates from multiple sources using weighted average.
    
    Args:
        candidates: List of coordinate candidates with confidence scores
    
    Returns:
        Tuple of (final_coordinates, final_confidence, sources_used)
    """
    if not candidates:
        return None, 0, []
    
    # Sort by confidence (highest first)
    candidates.sort(key=lambda x: x['confidence'], reverse=True)
    
    # Use weighted average of top candidates
    total_weight = 0
    weighted_lat = 0
    weighted_lon = 0
    sources_used = []
    
    for candidate in candidates:
        weight = candidate['confidence']
        coords = candidate['coordinates']
        
        weighted_lat += coords['latitude'] * weight
        weighted_lon += coords['longitude'] * weight
        total_weight += weight
        sources_used.append({
            'source': candidate['source'],
            'confidence': candidate['confidence'],
            'coordinates': coords
        })
    
    if total_weight > 0:
        final_coordinates = {
            'latitude': weighted_lat / total_weight,
            'longitude': weighted_lon / total_weight
        }
        final_confidence = min(1.0, total_weight / len(candidates))
        
        return final_coordinates, final_confidence, sources_used
    
    return None, 0, []

def aggregate_object_statistics(all_objects):
    """
    Aggregate object detection statistics from multiple files.
    
    Args:
        all_objects: List of all detected objects from all files
    
    Returns:
        Dictionary with aggregated object statistics
    """
    object_stats = {}
    
    for obj in all_objects:
        category = obj.get('category', 'unknown')
        confidence = obj.get('confidence', 0)
        
        if category not in object_stats:
            object_stats[category] = {
                'count': 0,
                'total_confidence': 0,
                'avg_confidence': 0,
                'files': []
            }
        
        object_stats[category]['count'] += 1
        object_stats[category]['total_confidence'] += confidence
    
    # Calculate averages
    for category, stats in object_stats.items():
        if stats['count'] > 0:
            stats['avg_confidence'] = stats['total_confidence'] / stats['count']
    
    return object_stats
