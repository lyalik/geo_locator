from flask import Blueprint, request, jsonify, current_app
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from pathlib import Path
import uuid

from services.geolocation_service import GeoLocationService
from services.yolo_violation_detector import YOLOViolationDetector

# Create blueprint
bp = Blueprint('violation_api', __name__, url_prefix='/api/violations')

# Initialize services
geolocation_service = GeoLocationService()
violation_detector = YOLOViolationDetector()

def allowed_file(filename):
    """Check if the file extension is allowed."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/detect', methods=['POST'])
def detect_violations():
    """
    API endpoint to upload an image and detect property violations.

    Request (multipart/form-data):
    - file: The image file to process
    - user_id: ID of the user submitting the image
    - location_notes: Optional notes about the location
    - location_hint: Optional text hint for location (e.g., "Moscow, Red Square, near Kremlin")
    
    Response (JSON):
    {
        'success': bool,
        'message': str,
        'data': {
            'violation_id': str,
            'image_path': str,
            'annotated_image_path': str,
            'violations': [
                {
                    'category': str,
                    'confidence': float,
                    'bbox': {
                        'x1': float, 'y1': float, 'x2': float, 'y2': float,
                        'width': float, 'height': float,
                        'center_x': float, 'center_y': float
                    }
                }
            ],
            'location': {
                'coordinates': {'latitude': float, 'longitude': float},
                'address': dict,
                'has_gps': bool
            },
            'metadata': {
                'timestamp': str,
                'user_id': str,
                'location_notes': str,
                'location_hint': str
            }
        },
        'error': str | None
    }
    """
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': 'No file part in the request',
            'data': None,
            'error': 'MISSING_FILE'
        }), 400
    
    file = request.files['file']
    
    # If user does not select file, browser also submit an empty part without filename
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': 'No selected file',
            'data': None,
            'error': 'NO_FILE_SELECTED'
        }), 400
    
    if file and allowed_file(file.filename):
        # Generate a unique filename
        file_ext = Path(file.filename).suffix
        filename = f"{uuid.uuid4()}{file_ext}"
        
        # Ensure upload directory exists
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'violations')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the original file
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Get additional form data
        user_id = request.form.get('user_id', 'anonymous')
        location_notes = request.form.get('location_notes', '')
        location_hint = request.form.get('location_hint', '')
        
        # Process the image
        try:
            # Step 1: Detect violations in the image
            detection_result = violation_detector.detect_violations(filepath)
            
            if not detection_result['success']:
                return jsonify({
                    'success': False,
                    'message': 'Failed to process image',
                    'data': None,
                    'error': detection_result.get('error', 'PROCESSING_ERROR')
                }), 500
            
            # Step 2: Extract geolocation data
            geo_result = geolocation_service.process_image(filepath, location_hint=location_hint)
            
            # Prepare response data
            response_data = {
                'violation_id': str(uuid.uuid4()),
                'image_path': f"/uploads/violations/{filename}",
                'annotated_image_path': f"/uploads/violations/{Path(detection_result['annotated_image_path']).name}" if detection_result.get('annotated_image_path') else None,
                'violations': detection_result.get('violations', []),
                'location': {
                    'coordinates': geo_result.get('coordinates'),
                    'address': geo_result.get('address'),
                    'has_gps': geo_result.get('has_gps', False)
                },
                'metadata': {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'user_id': user_id,
                    'location_notes': location_notes,
                    'location_hint': location_hint,
                    'image_size': detection_result.get('image_size')
                }
            }
            
            return jsonify({
                'success': True,
                'message': 'Image processed successfully',
                'data': response_data,
                'error': None
            })
            
        except Exception as e:
            current_app.logger.error(f"Error processing image: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'message': 'Internal server error',
                'data': None,
                'error': 'INTERNAL_SERVER_ERROR'
            }), 500
    
    return jsonify({
        'success': False,
        'message': 'Invalid file type',
        'data': None,
        'error': 'INVALID_FILE_TYPE'
    }), 400

@bp.route('/<violation_id>', methods=['GET'])
def get_violation(violation_id):
    """
    Get details of a specific violation by ID.
    In a real implementation, this would fetch from a database.
    """
    # TODO: Implement database lookup
    return jsonify({
        'success': False,
        'message': 'Not implemented',
        'data': None,
        'error': 'NOT_IMPLEMENTED'
    }), 501

@bp.route('/', methods=['GET'])
def list_violations():
    """
    List all violations with optional filtering.
    In a real implementation, this would query a database.
    """
    # TODO: Implement database query with filters
    return jsonify({
        'success': True,
        'message': 'List of violations',
        'data': {
            'violations': [],
            'total': 0,
            'page': 1,
            'per_page': 10
        },
        'error': None
    })

@bp.route('/batch_detect', methods=['POST'])
def batch_detect_violations():
    """
    API endpoint for batch processing multiple images.
    
    Request (multipart/form-data):
    - files: Multiple image files to process
    - location_hint: Optional location hint for all images
    - user_id: User identifier
    
    Returns:
    - JSON response with batch processing results
    """
    try:
        # Check if files are present
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No files provided',
                'data': []
            }), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({
                'success': False,
                'error': 'No files selected',
                'data': []
            }), 400
        
        # Get optional parameters
        location_hint = request.form.get('location_hint', '')
        user_id = request.form.get('user_id', 'anonymous')
        
        # Process files
        processed_files = []
        saved_paths = []
        
        for file in files:
            if file and allowed_file(file.filename):
                # Generate unique filename
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                
                # Save file
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                
                processed_files.append({
                    'original_name': filename,
                    'saved_path': file_path,
                    'unique_name': unique_filename
                })
                saved_paths.append(file_path)
        
        if not processed_files:
            return jsonify({
                'success': False,
                'error': 'No valid image files found',
                'data': []
            }), 400
        
        # Batch detect violations using YOLOv8
        batch_results = violation_detector.batch_detect(saved_paths)
        
        # Process each result with geolocation
        final_results = []
        for i, (file_info, detection_result) in enumerate(zip(processed_files, batch_results)):
            try:
                if detection_result['success']:
                    # Get geolocation for this image
                    location_result = geolocation_service.get_location_from_image(
                        file_info['saved_path'], 
                        location_hint
                    )
                    
                    # Combine results
                    combined_result = {
                        'file_info': {
                            'original_name': file_info['original_name'],
                            'unique_name': file_info['unique_name'],
                            'file_size': os.path.getsize(file_info['saved_path'])
                        },
                        'detection': detection_result,
                        'location': location_result,
                        'processing_time': datetime.utcnow().isoformat(),
                        'user_id': user_id
                    }
                else:
                    combined_result = {
                        'file_info': {
                            'original_name': file_info['original_name'],
                            'unique_name': file_info['unique_name']
                        },
                        'detection': detection_result,
                        'location': {'success': False, 'error': 'Detection failed'},
                        'processing_time': datetime.utcnow().isoformat(),
                        'user_id': user_id
                    }
                
                final_results.append(combined_result)
                
            except Exception as e:
                final_results.append({
                    'file_info': {
                        'original_name': file_info['original_name'],
                        'unique_name': file_info['unique_name']
                    },
                    'detection': {'success': False, 'error': str(e)},
                    'location': {'success': False, 'error': str(e)},
                    'processing_time': datetime.utcnow().isoformat(),
                    'user_id': user_id
                })
        
        # Calculate summary statistics
        total_files = len(final_results)
        successful_detections = sum(1 for r in final_results if r['detection']['success'])
        total_violations = sum(len(r['detection'].get('violations', [])) for r in final_results if r['detection']['success'])
        
        return jsonify({
            'success': True,
            'data': {
                'results': final_results,
                'summary': {
                    'total_files': total_files,
                    'successful_detections': successful_detections,
                    'failed_detections': total_files - successful_detections,
                    'total_violations_found': total_violations,
                    'processing_time': datetime.utcnow().isoformat()
                }
            },
            'error': None
        })
        
    except Exception as e:
        current_app.logger.error(f"Batch detection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Batch processing failed: {str(e)}',
            'data': []
        }), 500

@bp.route('/model_info', methods=['GET'])
def get_model_info():
    """Get information about the current detection model."""
    try:
        model_info = violation_detector.get_model_info()
        return jsonify({
            'success': True,
            'data': model_info,
            'error': None
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': None
        }), 500
