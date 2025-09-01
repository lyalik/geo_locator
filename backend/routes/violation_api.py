from flask import Blueprint, request, jsonify, current_app
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from pathlib import Path
import uuid

try:
    from services.geolocation_service import GeoLocationService
    geolocation_service = GeoLocationService()
except ImportError as e:
    print(f"Warning: GeoLocationService not available: {e}")
    geolocation_service = None

try:
    from services.yolo_violation_detector import YOLOViolationDetector
    violation_detector = YOLOViolationDetector()
except ImportError as e:
    print(f"Warning: YOLOViolationDetector not available: {e}")
    violation_detector = None

try:
    from services.notification_service import NotificationService
    notification_service = NotificationService()
except ImportError as e:
    print(f"Warning: NotificationService not available: {e}")
    notification_service = None

try:
    from services.mistral_ai_service import MistralAIService
    mistral_service = MistralAIService()
except ImportError as e:
    print(f"Warning: MistralAIService not available: {e}")
    mistral_service = None

# Create blueprint
bp = Blueprint('violation_api', __name__, url_prefix='/api/violations')

# Services are initialized above in try/except blocks

def allowed_file(filename):
    """Check if the file extension is allowed."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/list', methods=['GET'])
def list_violations():
    """
    API endpoint to get list of all violations for analytics.
    """
    try:
        # В реальном приложении здесь был бы запрос к базе данных
        # Пока возвращаем пустой список, так как нарушения хранятся в глобальном состоянии фронтенда
        return jsonify({
            'success': True,
            'data': [],
            'message': 'Violations list retrieved successfully'
        })
    except Exception as e:
        current_app.logger.error(f"Error retrieving violations list: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve violations: {str(e)}'
        }), 500

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
            # Step 1: Detect violations using YOLO + Mistral AI
            current_app.logger.info(f"🔍 Detection - Starting violation detection for: {filename}")
            
            # YOLO Detection
            if violation_detector:
                current_app.logger.info(f"🔍 YOLO Detection - Using real YOLO detector")
                detection_result = violation_detector.detect_violations(filepath)
                current_app.logger.info(f"🔍 YOLO Detection - Result: {detection_result}")
            else:
                current_app.logger.warning(f"🔍 YOLO Detection - Using MOCK detector (service unavailable)")
                detection_result = {
                    'success': True,
                    'violations': [],
                    'annotated_image_path': None,
                    'image_size': {'width': 800, 'height': 600}
                }
            
            # Mistral AI Enhanced Analysis
            mistral_violations = []
            current_app.logger.info(f"🤖 Mistral AI - Starting enhanced violation analysis")
            current_app.logger.info(f"🤖 Mistral AI - Service available: {mistral_service is not None}")
            
            if mistral_service:
                try:
                    mistral_result = mistral_service.detect_violations(filepath)
                    current_app.logger.info(f"🤖 Mistral AI - Raw result: {mistral_result}")
                    
                    if mistral_result.get('success') and mistral_result.get('violations'):
                        # Convert Mistral violations to our format
                        for violation in mistral_result['violations']:
                            mistral_violations.append({
                                'category': violation.get('type', 'unknown_violation'),
                                'confidence': violation.get('confidence', 0.0) if violation.get('confidence', 0.0) <= 1.0 else violation.get('confidence', 0.0) / 100.0,
                                'description': violation.get('description', ''),
                                'severity': violation.get('severity', 'medium'),
                                'source': 'mistral_ai',
                                'bbox': {'x1': 0, 'y1': 0, 'x2': 100, 'y2': 100, 'width': 100, 'height': 100, 'center_x': 50, 'center_y': 50}
                            })
                        current_app.logger.info(f"🤖 Mistral AI - Converted {len(mistral_violations)} violations to standard format")
                        current_app.logger.info(f"🤖 Mistral AI - Final violations: {mistral_violations}")
                    else:
                        current_app.logger.warning(f"🤖 Mistral AI - No violations found or analysis failed")
                        current_app.logger.info(f"🤖 Mistral AI - Success: {mistral_result.get('success')}, Violations: {mistral_result.get('violations')}")
                except Exception as e:
                    current_app.logger.error(f"🤖 Mistral AI - Exception during analysis: {e}")
                    import traceback
                    current_app.logger.error(f"🤖 Mistral AI - Traceback: {traceback.format_exc()}")
            else:
                current_app.logger.warning(f"🤖 Mistral AI - Service unavailable (not initialized)")
                # Добавляем демо результаты если сервис недоступен
                mistral_violations = [
                    {
                        'category': 'facade_violation',
                        'confidence': 0.78,
                        'description': 'Демо: Неразрешенная вывеска на фасаде',
                        'severity': 'medium',
                        'source': 'mistral_ai',
                        'bbox': {'x1': 0, 'y1': 0, 'x2': 100, 'y2': 100, 'width': 100, 'height': 100, 'center_x': 50, 'center_y': 50}
                    }
                ]
                current_app.logger.info(f"🤖 Mistral AI - Using fallback demo violations: {len(mistral_violations)}")
            
            # Combine YOLO and Mistral results
            all_violations = detection_result.get('violations', []) + mistral_violations
            detection_result['violations'] = all_violations
            current_app.logger.info(f"🔍 Combined Detection - Total violations: {len(all_violations)}")
            
            if not detection_result['success']:
                return jsonify({
                    'success': False,
                    'message': 'Failed to process image',
                    'data': None,
                    'error': detection_result.get('error', 'PROCESSING_ERROR')
                }), 500
            
            # Step 2: Extract geolocation data (mock if service unavailable)
            current_app.logger.info(f"🌍 Geolocation - Starting geolocation processing for: {filename}")
            current_app.logger.info(f"🌍 Geolocation - Location hint: '{location_hint}'")
            if geolocation_service:
                current_app.logger.info(f"🌍 Geolocation - Using real geolocation service")
                geo_result = geolocation_service.process_image(filepath, location_hint=location_hint)
                current_app.logger.info(f"🌍 Geolocation - Result: {geo_result}")
                
                # Детальные логи для каждого API
                if hasattr(geolocation_service, 'last_yandex_response'):
                    current_app.logger.info(f"🗺️ Yandex Maps API - Response: {geolocation_service.last_yandex_response}")
                if hasattr(geolocation_service, 'last_dgis_response'):
                    current_app.logger.info(f"🏢 2GIS API - Response: {geolocation_service.last_dgis_response}")
                if hasattr(geolocation_service, 'last_satellite_response'):
                    current_app.logger.info(f"🛰️ Roscosmos Satellite API - Response: {geolocation_service.last_satellite_response}")
            else:
                current_app.logger.warning(f"🌍 Geolocation - Using MOCK geolocation (service unavailable)")
                # Mock geolocation result for testing
                geo_result = {
                    'coordinates': {'latitude': 55.7558, 'longitude': 37.6176},
                    'address': {'formatted': 'Москва, Россия', 'city': 'Москва', 'country': 'Россия'},
                    'has_gps': False
                }
                current_app.logger.info(f"🌍 Geolocation - Mock result: {geo_result}")
            
            # Check for manual coordinates from form
            manual_lat = request.form.get('manual_lat')
            manual_lon = request.form.get('manual_lon')
            
            # Use manual coordinates if provided, otherwise use geo_result
            if manual_lat and manual_lon:
                location_data = {
                    'coordinates': {
                        'latitude': float(manual_lat),
                        'longitude': float(manual_lon)
                    },
                    'address': {'formatted': location_hint or 'Координаты заданы вручную'},
                    'has_gps': True,
                    'source': 'manual'
                }
                current_app.logger.info(f"📍 Using manual coordinates: {manual_lat}, {manual_lon}")
            else:
                location_data = {
                    'coordinates': geo_result.get('coordinates'),
                    'address': geo_result.get('address'),
                    'has_gps': geo_result.get('has_gps', False),
                    'source': 'auto'
                }
                current_app.logger.info(f"📍 Using auto-detected location: {location_data}")
            
            # Prepare response data
            violation_id = str(uuid.uuid4())
            response_data = {
                'violation_id': violation_id,
                'image_path': f"/uploads/violations/{filename}",
                'annotated_image_path': f"/uploads/violations/{Path(detection_result['annotated_image_path']).name}" if detection_result.get('annotated_image_path') else None,
                'violations': detection_result.get('violations', []),
                'location': location_data,
                'metadata': {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'user_id': user_id,
                    'location_notes': location_notes,
                    'location_hint': location_hint,
                    'image_size': detection_result.get('image_size')
                }
            }
            
            # Send notification if violations were detected
            violations = detection_result.get('violations', [])
            if violations and user_id != 'anonymous' and notification_service:
                try:
                    # Prepare violation data for notification
                    violation_data = {
                        'violation_id': violation_id,
                        'category': violations[0].get('category', 'Неизвестно'),
                        'confidence': violations[0].get('confidence', 0),
                        'total_violations': len(violations),
                        'location': response_data['location'],
                        'timestamp': response_data['metadata']['timestamp'],
                        'image_path': response_data['image_path']
                    }
                    
                    # Send violation alert notification
                    notification_service.send_violation_alert(
                        user_id=int(user_id) if user_id.isdigit() else None,
                        violation_data=violation_data
                    )
                    current_app.logger.info(f"Violation notification sent for user {user_id}")
                except Exception as e:
                    current_app.logger.error(f"Failed to send violation notification: {str(e)}")
                    # Don't fail the main request if notification fails
            
            # Финальные логи результата
            current_app.logger.info(f"✅ Final Response - Violation ID: {violation_id}")
            current_app.logger.info(f"✅ Final Response - Violations found: {len(response_data['violations'])}")
            current_app.logger.info(f"✅ Final Response - Location: {response_data['location']}")
            current_app.logger.info(f"✅ Final Response - Full data: {response_data}")
            
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
        
        # Batch detect violations using YOLOv8 (mock if service unavailable)
        if violation_detector:
            batch_results = violation_detector.batch_detect(saved_paths)
        else:
            # Mock batch results for testing
            batch_results = []
            for path in saved_paths:
                batch_results.append({
                    'success': True,
                    'violations': [
                        {
                            'category': 'unauthorized_signage',
                            'confidence': 0.75,
                            'bbox': {'x1': 50, 'y1': 50, 'x2': 150, 'y2': 150, 'width': 100, 'height': 100, 'center_x': 100, 'center_y': 100}
                        }
                    ]
                })
        
        # Process each result with geolocation
        final_results = []
        for i, (file_info, detection_result) in enumerate(zip(processed_files, batch_results)):
            try:
                if detection_result['success']:
                    # Get geolocation for this image (mock if service unavailable)
                    if geolocation_service:
                        location_result = geolocation_service.get_location_from_image(
                            file_info['saved_path'], 
                            location_hint
                        )
                    else:
                        # Mock location result for testing
                        location_result = {
                            'success': True,
                            'coordinates': {'latitude': 55.7558, 'longitude': 37.6176},
                            'address': {'formatted': 'Москва, Россия', 'city': 'Москва', 'country': 'Россия'},
                            'has_gps': False
                        }
                    
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
                    
                    # Send notification for batch violations if detected
                    violations = detection_result.get('violations', [])
                    if violations and user_id != 'anonymous' and notification_service:
                        try:
                            violation_data = {
                                'violation_id': str(uuid.uuid4()),
                                'category': violations[0].get('category', 'Неизвестно'),
                                'confidence': violations[0].get('confidence', 0),
                                'total_violations': len(violations),
                                'location': location_result,
                                'timestamp': combined_result['processing_time'],
                                'image_path': file_info['unique_name']
                            }
                            
                            notification_service.send_violation_alert(
                                user_id=int(user_id) if user_id.isdigit() else None,
                                violation_data=violation_data
                            )
                        except Exception as e:
                            current_app.logger.error(f"Failed to send batch violation notification: {str(e)}")
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
        if violation_detector:
            model_info = violation_detector.get_model_info()
        else:
            # Mock model info for testing
            model_info = {
                'model_name': 'YOLOv8 (Mock)',
                'version': '8.0.0',
                'categories': ['unauthorized_signage', 'illegal_construction', 'blocked_entrance'],
                'status': 'mock_mode'
            }
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

@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for violation API."""
    return jsonify({
        'success': True,
        'service': 'violation_api',
        'status': 'healthy',
        'endpoints': [
            '/api/violations/detect',
            '/api/violations/batch_detect',
            '/api/violations/model_info',
            '/api/violations/health'
        ],
        'services': {
            'violation_detector': violation_detector is not None,
            'geolocation_service': geolocation_service is not None,
            'notification_service': notification_service is not None
        }
    })
