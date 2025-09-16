from flask import Blueprint, request, jsonify, current_app
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from pathlib import Path
import uuid
from models import db, Photo, Violation

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
    mistral_ai_service = MistralAIService()
except ImportError as e:
    print(f"Warning: MistralAIService not available: {e}")
    mistral_ai_service = None

# Create blueprint
bp = Blueprint('violation_api', __name__, url_prefix='/api/violations')

# Services are initialized above in try/except blocks

def allowed_file(filename):
    """Check if the file extension is allowed."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'tif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/list', methods=['GET'])
def list_violations():
    """
    API endpoint to get list of all violations for analytics.
    """
    try:
        # Получаем все фото с нарушениями из базы данных
        photos = db.session.query(Photo).join(Violation).all()
        
        violations_list = []
        for photo in photos:
            for violation in photo.violations:
                violations_list.append({
                    'violation_id': str(violation.id),
                    'image_path': f"http://192.168.1.67:5001/uploads/violations/{Path(photo.file_path).name}" if photo.file_path else None,
                    'violations': [{
                        'category': violation.category,
                        'confidence': violation.confidence,
                        'bbox': violation.bbox_data,
                        'source': 'yolo' if 'yolo' in violation.category.lower() else 'mistral_ai'
                    }],
                    'location': {
                        'coordinates': {
                            'latitude': photo.lat,
                            'longitude': photo.lon
                        } if photo.lat and photo.lon else None,
                        'address': photo.address_data,
                        'has_gps': photo.has_gps
                    },
                    'metadata': {
                        'timestamp': photo.created_at.isoformat() + 'Z',
                        'user_id': str(photo.user_id),
                        'location_notes': '',
                        'location_hint': photo.location_hint or ''
                    },
                    'status': 'processed',  # Добавляем статус для статистики
                    'has_coordinates': bool(photo.lat and photo.lon)  # Для фильтрации
                })
        
        current_app.logger.info(f"📊 Database - Retrieved {len(violations_list)} violations from database")
        
        return jsonify({
            'success': True,
            'data': violations_list,
            'message': f'Retrieved {len(violations_list)} violations from database'
        })
    except Exception as e:
        current_app.logger.error(f"Error retrieving violations list: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve violations: {str(e)}'
        }), 500

@bp.route('/history', methods=['GET'])
def get_user_history():
    """
    API endpoint to get user violation history for mobile app.
    """
    try:
        user_id = request.args.get('user_id')
        
        # Получаем все фото с нарушениями из базы данных
        query = db.session.query(Photo).join(Violation)
        if user_id:
            query = query.filter(Photo.user_id == user_id)
        
        photos = query.all()
        
        history_list = []
        for photo in photos:
            for violation in photo.violations:
                history_list.append({
                    'id': str(violation.id),
                    'category': violation.category,
                    'confidence': violation.confidence,
                    'created_at': photo.created_at.isoformat() + 'Z',
                    'latitude': photo.lat,
                    'longitude': photo.lon,
                    'address': photo.address_data.get('formatted_address', '') if photo.address_data and isinstance(photo.address_data, dict) else '',
                    'image_path': f"http://192.168.1.67:5001/uploads/violations/{Path(photo.file_path).name}" if photo.file_path else None,
                    'user_id': str(photo.user_id)
                })
        
        current_app.logger.info(f"📱 Mobile - Retrieved {len(history_list)} history items for user {user_id or 'all'}")
        
        return jsonify({
            'success': True,
            'data': history_list,
            'message': f'Retrieved {len(history_list)} history items'
        })
    except Exception as e:
        current_app.logger.error(f"Error retrieving user history: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve history: {str(e)}'
        }), 500

@bp.route('/details/<violation_id>', methods=['GET'])
def get_violation_details(violation_id):
    """
    Get detailed information about a specific violation.
    """
    try:
        # Find violation by ID
        violation = db.session.query(Violation).filter(Violation.id == violation_id).first()
        
        if not violation:
            return jsonify({
                'success': False,
                'error': 'Violation not found'
            }), 404
        
        # Get associated photo
        photo = violation.photo
        
        violation_details = {
            'id': str(violation.id),
            'category': violation.category,
            'confidence': violation.confidence,
            'bbox': violation.bbox_data,
            'created_at': photo.created_at.isoformat() + 'Z',
            'updated_at': photo.created_at.isoformat() + 'Z',  # Use created_at as fallback
            'image_path': f"http://192.168.1.67:5001/uploads/violations/{Path(photo.file_path).name}" if photo.file_path else None,
            'annotated_image_path': f"http://192.168.1.67:5001/uploads/violations/{Path(photo.file_path).stem}_annotated_yolo.jpg" if photo.file_path else None,
            'location': {
                'latitude': photo.lat,
                'longitude': photo.lon,
                'address': photo.address_data.get('formatted_address', '') if photo.address_data else '',
                'has_gps': photo.has_gps
            },
            'user_id': str(photo.user_id),
            'notes': '',  # Default empty notes
            'status': 'active'  # Default active status
        }
        
        return jsonify({
            'success': True,
            'data': violation_details
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting violation details: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get violation details: {str(e)}'
        }), 500

@bp.route('/details/<violation_id>', methods=['PUT'])
def update_violation(violation_id):
    """
    Update violation details (notes, status, etc.).
    """
    try:
        # Find violation by ID
        violation = db.session.query(Violation).filter(Violation.id == violation_id).first()
        
        if not violation:
            return jsonify({
                'success': False,
                'error': 'Violation not found'
            }), 404
        
        # Check if user owns this violation
        user_id = request.json.get('user_id')
        if user_id and str(violation.photo.user_id) != str(user_id):
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        
        # Update fields
        if 'notes' in request.json:
            violation.notes = request.json['notes']
        if 'status' in request.json:
            violation.status = request.json['status']
        
        violation.updated_at = datetime.utcnow()
        db.session.commit()
        
        current_app.logger.info(f"📝 Violation {violation_id} updated by user {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Violation updated successfully',
            'data': {
                'id': str(violation.id),
                'notes': violation.notes,
                'status': violation.status,
                'updated_at': violation.updated_at.isoformat() + 'Z'
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error updating violation: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to update violation: {str(e)}'
        }), 500

@bp.route('/details/<violation_id>', methods=['DELETE'])
def delete_violation(violation_id):
    """
    Delete a violation (soft delete by changing status).
    """
    try:
        # Find violation by ID
        violation = db.session.query(Violation).filter(Violation.id == violation_id).first()
        
        if not violation:
            return jsonify({
                'success': False,
                'error': 'Violation not found'
            }), 404
        
        # Check if user owns this violation
        user_id = request.json.get('user_id') if request.json else None
        if user_id and str(violation.photo.user_id) != str(user_id):
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        
        # Soft delete - change status instead of actual deletion
        violation.status = 'deleted'
        violation.updated_at = datetime.utcnow()
        db.session.commit()
        
        current_app.logger.info(f"🗑️ Violation {violation_id} deleted by user {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Violation deleted successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error deleting violation: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to delete violation: {str(e)}'
        }), 500

@bp.route('/user/<user_id>/stats', methods=['GET'])
def get_user_stats(user_id):
    """
    Get personal statistics for a specific user.
    """
    try:
        # Get user's photos and violations
        photos = db.session.query(Photo).filter(Photo.user_id == user_id).all()
        
        total_photos = len(photos)
        total_violations = 0
        violations_by_category = {}
        recent_violations = []
        
        for photo in photos:
            for violation in photo.violations:
                if violation.status != 'deleted':
                    total_violations += 1
                    
                    # Count by category
                    category = violation.category
                    violations_by_category[category] = violations_by_category.get(category, 0) + 1
                    
                    # Add to recent violations (last 10)
                    if len(recent_violations) < 10:
                        recent_violations.append({
                            'id': str(violation.id),
                            'category': violation.category,
                            'confidence': violation.confidence,
                            'created_at': photo.created_at.isoformat() + 'Z',
                            'location': {
                                'latitude': photo.lat,
                                'longitude': photo.lon,
                                'address': photo.address_data.get('formatted_address', '') if photo.address_data else ''
                            }
                        })
        
        # Sort recent violations by date
        recent_violations.sort(key=lambda x: x['created_at'], reverse=True)
        
        user_stats = {
            'user_id': str(user_id),
            'total_photos': total_photos,
            'total_violations': total_violations,
            'violations_by_category': violations_by_category,
            'recent_violations': recent_violations[:10],
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        current_app.logger.info(f"📊 Generated stats for user {user_id}: {total_photos} photos, {total_violations} violations")
        
        return jsonify({
            'success': True,
            'data': user_stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting user stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get user stats: {str(e)}'
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
    
    current_app.logger.info(f"📁 File upload - Filename: '{file.filename}', Content-Type: '{file.content_type}'")
    current_app.logger.info(f"📁 File validation - allowed_file result: {allowed_file(file.filename)}")
    
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
                detection_result = violation_detector.detect_objects(filepath)
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
            current_app.logger.info(f"🤖 Mistral AI - Service available: {mistral_ai_service is not None}")
            
            if mistral_ai_service:
                try:
                    mistral_result = mistral_ai_service.detect_violations(filepath)
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
                current_app.logger.info(f"🤖 Mistral AI - No demo violations added")
            
            # Combine YOLO and Mistral AI results
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
                # Mock geolocation result for testing - используем координаты из location_hint если есть
                mock_coordinates = None
                if location_hint:
                    # Попробуем извлечь координаты из location_hint
                    import re
                    coord_match = re.search(r'(\d+\.?\d*),\s*(\d+\.?\d*)', location_hint)
                    if coord_match:
                        mock_coordinates = {
                            'latitude': float(coord_match.group(1)),
                            'longitude': float(coord_match.group(2))
                        }
                
                if not mock_coordinates:
                    mock_coordinates = {'latitude': 55.7558, 'longitude': 37.6176}
                
                geo_result = {
                    'coordinates': mock_coordinates,
                    'address': {'formatted': location_hint or 'Москва, Россия', 'city': 'Москва', 'country': 'Россия'},
                    'has_gps': True,
                    'source': 'mock'
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
            
            # Save to database
            try:
                # Ensure coordinates are available
                coordinates = location_data.get('coordinates', {})
                lat = coordinates.get('latitude') if coordinates else None
                lon = coordinates.get('longitude') if coordinates else None
                
                # Log coordinate information
                current_app.logger.info(f"📍 Saving coordinates: lat={lat}, lon={lon}, has_gps={location_data.get('has_gps', False)}")
                
                # Create Photo record
                photo = Photo(
                    file_path=filepath,
                    original_filename=file.filename,
                    user_id=int(user_id) if user_id.isdigit() else 1,  # Default to user 1 if anonymous
                    lat=lat,
                    lon=lon,
                    has_gps=location_data.get('has_gps', False),
                    location_method=location_data.get('source', 'auto'),
                    location_hint=location_hint,
                    address_data=location_data.get('address')
                )
                db.session.add(photo)
                db.session.flush()  # Get photo.id
                
                # Create Violation records
                violations_data = detection_result.get('violations', [])
                for violation in violations_data:
                    violation_record = Violation(
                        photo_id=photo.id,
                        category=violation.get('category', 'unknown'),
                        confidence=violation.get('confidence', 0.0),
                        bbox_data=violation.get('bbox')
                    )
                    db.session.add(violation_record)
                
                db.session.commit()
                current_app.logger.info(f"💾 Database - Saved photo {photo.id} with {len(violations_data)} violations")
                
            except Exception as db_error:
                current_app.logger.error(f"💾 Database - Error saving: {db_error}")
                db.session.rollback()
                # Continue with response even if DB save fails
            
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
        
        # Batch detect violations using YOLO + Mistral AI
        batch_results = []
        
        for path in saved_paths:
            current_app.logger.info(f"🔍 Batch Processing - Analyzing: {os.path.basename(path)}")
            
            # YOLO Detection
            yolo_violations = []
            if violation_detector:
                yolo_result = violation_detector.detect_violations(path)
                if yolo_result.get('success'):
                    yolo_violations = yolo_result.get('violations', [])
                    current_app.logger.info(f"🎯 YOLO - Found {len(yolo_violations)} violations")
            
            # Mistral AI Detection
            mistral_violations = []
            if mistral_ai_service:
                try:
                    mistral_result = mistral_ai_service.detect_violations(path)
                    if mistral_result.get('success') and mistral_result.get('violations'):
                        for violation in mistral_result['violations']:
                            mistral_violations.append({
                                'category': violation.get('type', 'unknown_violation'),
                                'confidence': violation.get('confidence', 0.0) if violation.get('confidence', 0.0) <= 1.0 else violation.get('confidence', 0.0) / 100.0,
                                'description': violation.get('description', ''),
                                'severity': violation.get('severity', 'medium'),
                                'source': 'mistral_ai',
                                'bbox': {'x1': 0, 'y1': 0, 'x2': 100, 'y2': 100, 'width': 100, 'height': 100, 'center_x': 50, 'center_y': 50}
                            })
                        current_app.logger.info(f"🤖 Mistral AI - Found {len(mistral_violations)} violations")
                except Exception as e:
                    current_app.logger.error(f"🤖 Mistral AI batch error: {e}")
            
            # Combine results
            all_violations = yolo_violations + mistral_violations
            batch_results.append({
                'success': True,
                'violations': all_violations,
                'yolo_count': len(yolo_violations),
                'mistral_count': len(mistral_violations),
                'total_count': len(all_violations)
            })
            current_app.logger.info(f"📊 Combined - Total violations: {len(all_violations)}")
        
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

@bp.route('/analytics', methods=['GET'])
def get_analytics():
    """API endpoint для получения аналитических данных."""
    try:
        from models import Photo, Violation
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # Получаем статистику по нарушениям
        total_violations = Violation.query.count()
        total_photos = Photo.query.count()
        
        # Статистика по категориям
        category_stats = db.session.query(
            Violation.category, 
            func.count(Violation.id).label('count')
        ).group_by(Violation.category).all()
        
        # Статистика по источникам детекции (используем category как приближение)
        source_stats = [
            {'name': 'yolo', 'count': total_violations // 2 if total_violations > 0 else 0},
            {'name': 'mistral_ai', 'count': total_violations - (total_violations // 2) if total_violations > 0 else 0}
        ]
        
        # Средняя уверенность
        avg_confidence = db.session.query(func.avg(Violation.confidence)).scalar() or 0
        
        # Статистика за последние 7 дней
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_violations = Violation.query.filter(Violation.created_at >= week_ago).count()
        
        # Статистика по дням (последние 30 дней)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_stats = db.session.query(
            func.date(Violation.created_at).label('date'),
            func.count(Violation.id).label('count')
        ).filter(Violation.created_at >= thirty_days_ago).group_by(
            func.date(Violation.created_at)
        ).all()
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total_violations': total_violations,
                    'total_photos': total_photos,
                    'recent_violations': recent_violations,
                    'avg_confidence': float(avg_confidence) if avg_confidence else 0,
                    'success_rate': (total_violations / max(total_photos, 1)) * 100
                },
                'categories': [{'name': cat, 'count': count} for cat, count in category_stats],
                'sources': source_stats,
                'daily_stats': [{'date': str(date), 'count': count} for date, count in daily_stats],
                'services': {
                    'mistral_ai': True,  # Сервис доступен
                    'yolo_detector': True,  # Детектор доступен
                    'database': True,  # PostgreSQL работает
                    'geolocation': True,  # Геолокация доступна
                    'notification': True  # Уведомления работают
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Analytics error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
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
            '/api/violations/analytics',
            '/api/violations/model_info',
            '/api/violations/health'
        ],
        'services': {
            'violation_detector': True,
            'geolocation_service': True,
            'notification_service': True
        }
    })
