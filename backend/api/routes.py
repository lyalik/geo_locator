from flask import Blueprint, request, jsonify, current_app
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
from ..models import db, SearchRequest, User, Comparison
from ..utils.ml_utils import GeminiProcessor
from ..utils.integration_utils import YandexMapsAPI, DgisAPI, compare_locations
from ..utils.media_utils import MediaProcessor, extract_metadata
from .. import tasks
import json

# Create a Blueprint for the API routes
api_bp = Blueprint('api', __name__)

# Initialize API clients
yandex_maps = YandexMapsAPI()
dgis = DgisAPI()
media_processor = MediaProcessor()

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@api_bp.route('/search/text', methods=['POST'])
def search_by_text():
    """
    Search for a location using text query.
    
    Request body:
    {
        "query": "search query",
        "user_id": 1  # optional
    }
    """
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing query parameter'}), 400
    
    query = data['query']
    user_id = data.get('user_id')
    
    # Create a new search request in the database
    search_request = SearchRequest(
        user_id=user_id,
        search_type='text',
        query=query,
        status='processing'
    )
    
    db.session.add(search_request)
    db.session.commit()
    
    try:
        # Process the search asynchronously
        tasks.process_search_request.delay(search_request.id)
        
        return jsonify({
            'status': 'processing',
            'request_id': search_request.id,
            'message': 'Search request is being processed'
        }), 202
        
    except Exception as e:
        search_request.status = 'failed'
        search_request.completed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@api_bp.route('/search/image', methods=['POST'])
def search_by_image():
    """
    Search for a location using an image.
    
    Request form data:
    - file: image file
    - user_id: optional user ID
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    user_id = request.form.get('user_id')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Generate a unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Ensure upload directory exists
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save the file
        file.save(filepath)
        
        # Create a new search request in the database
        search_request = SearchRequest(
            user_id=user_id,
            search_type='image',
            file_path=filepath,
            status='processing'
        )
        
        db.session.add(search_request)
        db.session.commit()
        
        try:
            # Process the image asynchronously
            tasks.process_search_request.delay(search_request.id)
            
            return jsonify({
                'status': 'processing',
                'request_id': search_request.id,
                'message': 'Image is being processed',
                'file_path': filepath
            }), 202
            
        except Exception as e:
            search_request.status = 'failed'
            search_request.completed_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

@api_bp.route('/search/video', methods=['POST'])
def search_by_video():
    """
    Search for a location using a video.
    
    Request form data:
    - file: video file
    - user_id: optional user ID
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    user_id = request.form.get('user_id')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Generate a unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Ensure upload directory exists
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save the file
        file.save(filepath)
        
        # Create a new search request in the database
        search_request = SearchRequest(
            user_id=user_id,
            search_type='video',
            file_path=filepath,
            status='processing'
        )
        
        db.session.add(search_request)
        db.session.commit()
        
        try:
            # Process the video asynchronously
            tasks.process_search_request.delay(search_request.id)
            
            return jsonify({
                'status': 'processing',
                'request_id': search_request.id,
                'message': 'Video is being processed',
                'file_path': filepath
            }), 202
            
        except Exception as e:
            search_request.status = 'failed'
            search_request.completed_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

@api_bp.route('/search/panorama', methods=['POST'])
def search_by_panorama():
    """
    Search for a location using a panorama image.
    
    Request form data:
    - file: panorama image file
    - user_id: optional user ID
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    user_id = request.form.get('user_id')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Generate a unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Ensure upload directory exists
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save the file
        file.save(filepath)
        
        # Create a new search request in the database
        search_request = SearchRequest(
            user_id=user_id,
            search_type='panorama',
            file_path=filepath,
            status='processing'
        )
        
        db.session.add(search_request)
        db.session.commit()
        
        try:
            # Process the panorama asynchronously
            tasks.process_search_request.delay(search_request.id)
            
            return jsonify({
                'status': 'processing',
                'request_id': search_request.id,
                'message': 'Panorama is being processed',
                'file_path': filepath
            }), 202
            
        except Exception as e:
            search_request.status = 'failed'
            search_request.completed_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

@api_bp.route('/search/status/<int:request_id>', methods=['GET'])
def get_search_status(request_id):
    """Get the status of a search request."""
    search_request = SearchRequest.query.get_or_404(request_id)
    
    return jsonify({
        'request_id': search_request.id,
        'status': search_request.status,
        'search_type': search_request.search_type,
        'created_at': search_request.created_at.isoformat() if search_request.created_at else None,
        'completed_at': search_request.completed_at.isoformat() if search_request.completed_at else None,
        'result': {
            'yandex': search_request.yandex_result,
            '2gis': search_request.dgis_result,
            'sentinel': search_request.sentinel_result,
            'gemini_analysis': search_request.gemini_analysis,
            'latitude': search_request.latitude,
            'longitude': search_request.longitude,
            'address': search_request.address
        }
    })

@api_bp.route('/search/compare', methods=['POST'])
def compare_locations_api():
    """
    Compare locations from different sources.
    
    Request body:
    {
        "yandex_data": { ... },
        "dgis_data": { ... },
        "request_id": 1  # optional
    }
    """
    data = request.get_json()
    
    if not data or 'yandex_data' not in data or 'dgis_data' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    yandex_data = data['yandex_data']
    dgis_data = data['dgis_data']
    request_id = data.get('request_id')
    
    try:
        # Compare locations
        comparison_result = compare_locations(yandex_data, dgis_data)
        
        # Save comparison to database if request_id is provided
        if request_id:
            comparison = Comparison(
                request_id=request_id,
                source='composite',
                confidence=comparison_result.get('match_confidence', 0) / 100.0,  # Convert to 0-1 scale
                result_data=comparison_result,
                latitude=comparison_result.get('latitude'),
                longitude=comparison_result.get('longitude'),
                address=comparison_result.get('address')
            )
            
            db.session.add(comparison)
            db.session.commit()
            
            comparison_result['comparison_id'] = comparison.id
        
        return jsonify({
            'status': 'success',
            'result': comparison_result
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@api_bp.route('/search/history', methods=['GET'])
def get_search_history():
    """Get search history for a user."""
    user_id = request.args.get('user_id')
    limit = min(int(request.args.get('limit', 10)), 100)  # Max 100 results
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    # Query search requests for the user
    search_requests = SearchRequest.query.filter_by(user_id=user_id)\
        .order_by(SearchRequest.created_at.desc())\
        .limit(limit)\
        .all()
    
    return jsonify([{
        'id': req.id,
        'search_type': req.search_type,
        'query': req.query,
        'file_path': req.file_path,
        'status': req.status,
        'created_at': req.created_at.isoformat() if req.created_at else None,
        'completed_at': req.completed_at.isoformat() if req.completed_at else None,
        'latitude': req.latitude,
        'longitude': req.longitude,
        'address': req.address
    } for req in search_requests])

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'database': 'ok',
            'yandex_maps': 'ok',
            '2gis': 'ok',
            'gemini': 'ok' if os.getenv('GEMINI_API_KEY') else 'not_configured'
        }
    })
