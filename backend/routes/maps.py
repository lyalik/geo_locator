from flask import Blueprint, request, jsonify, Response
from services.maps import map_aggregator
import asyncio
import logging
from io import BytesIO
from PIL import Image

bp = Blueprint('maps', __name__, url_prefix='/api/maps')

@bp.route('/search', methods=['GET'])
def search_places():
    """
    Search for places using multiple map providers
    Query parameters:
    - q: Search query (required)
    - lat: Latitude (required)
    - lon: Longitude (required)
    - radius: Search radius in meters (optional, default=500)
    """
    try:
        query = request.args.get('q')
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        radius = int(request.args.get('radius', 500))
        
        if not query or lat is None or lon is None:
            return jsonify({'error': 'Missing required parameters'}), 400
            
        results = asyncio.run(map_aggregator.search_places(query, lat, lon, radius))
        return jsonify(results)
        
    except ValueError as e:
        return jsonify({'error': 'Invalid parameter values'}), 400
    except Exception as e:
        logging.error(f"Error in search_places: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/reverse-geocode', methods=['GET'])
def reverse_geocode():
    """
    Get address from coordinates using multiple map providers
    Query parameters:
    - lat: Latitude (required)
    - lon: Longitude (required)
    """
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        
        if lat is None or lon is None:
            return jsonify({'error': 'Missing required parameters'}), 400
            
        results = asyncio.run(map_aggregator.reverse_geocode(lat, lon))
        return jsonify(results)
        
    except ValueError as e:
        return jsonify({'error': 'Invalid parameter values'}), 400
    except Exception as e:
        logging.error(f"Error in reverse_geocode: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/satellite', methods=['GET'])
def get_satellite_image():
    """
    Get satellite image for given coordinates
    Query parameters:
    - lat: Latitude (required)
    - lon: Longitude (required)
    - zoom: Zoom level (optional, default=17)
    - width: Image width (optional, default=600)
    - height: Image height (optional, default=400)
    """
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        zoom = int(request.args.get('zoom', 17))
        width = int(request.args.get('width', 600))
        height = int(request.args.get('height', 400))
        
        if lat is None or lon is None:
            return jsonify({'error': 'Missing required parameters'}), 400
            
        # Get the best available satellite image
        result = asyncio.run(map_aggregator.get_satellite_image(lat, lon, zoom, width, height))
        
        if 'error' in result:
            return jsonify(result), 500
            
        # Return the image directly
        return Response(
            result['image'],
            mimetype=result.get('content_type', 'image/jpeg'),
            headers={
                'X-Provider': result.get('provider', 'unknown'),
                'X-Latitude': str(result.get('lat', lat)),
                'X-Longitude': str(result.get('lon', lon)),
                'X-Zoom': str(result.get('zoom', zoom))
            }
        )
        
    except ValueError as e:
        return jsonify({'error': 'Invalid parameter values'}), 400
    except Exception as e:
        logging.error(f"Error in get_satellite_image: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def init_app(app):
    """Register blueprints and initialize services"""
    app.register_blueprint(bp)
    
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Close all connections on app teardown"""
        try:
            from services.maps import yandex_service, dgis_service
            # Note: In a real app, you'd want proper async cleanup
            # For now, we'll handle this synchronously
            pass
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
