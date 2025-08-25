from flask import Blueprint, request, jsonify
from ..services.maps import map_aggregator
import asyncio
import logging

bp = Blueprint('maps', __name__, url_prefix='/api/maps')

@bp.route('/search', methods=['GET'])
async def search_places():
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
            
        results = await map_aggregator.search_places(query, lat, lon, radius)
        return jsonify(results)
        
    except ValueError as e:
        return jsonify({'error': 'Invalid parameter values'}), 400
    except Exception as e:
        logging.error(f"Error in search_places: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/reverse-geocode', methods=['GET'])
async def reverse_geocode():
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
            
        results = await map_aggregator.reverse_geocode(lat, lon)
        return jsonify(results)
        
    except ValueError as e:
        return jsonify({'error': 'Invalid parameter values'}), 400
    except Exception as e:
        logging.error(f"Error in reverse_geocode: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def init_app(app):
    """Register blueprints and initialize services"""
    app.register_blueprint(bp)
    
    @app.teardown_appcontext
    async def shutdown_session(exception=None):
        """Close all connections on app teardown"""
        from ..services.maps import yandex_service, dgis_service
        await yandex_service.close()
        await dgis_service.close()
