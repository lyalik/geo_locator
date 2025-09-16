#!/usr/bin/env python3
"""
API для OpenStreetMap urban context анализа
"""
import logging
from flask import Blueprint, request, jsonify
from services.osm_overpass_service import OSMOverpassService

logger = logging.getLogger(__name__)

osm_bp = Blueprint('osm_api', __name__, url_prefix='/api/osm')

# Инициализация OSM сервиса
try:
    osm_service = OSMOverpassService()
    logger.info("OSM service initialized successfully")
except Exception as e:
    logger.error(f"Error initializing OSM service: {e}")
    osm_service = None

@osm_bp.route('/urban-context', methods=['GET'])
def get_urban_context():
    """
    Получение городского контекста через OSM Overpass API
    """
    try:
        if osm_service is None:
            return jsonify({'error': 'OSM service not available'}), 503
        
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', 1000, type=int)
        
        if lat is None or lon is None:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        # Получаем здания
        buildings_query = f"""
        [out:json][timeout:25];
        (
          way["building"](around:{radius},{lat},{lon});
          relation["building"](around:{radius},{lat},{lon});
        );
        out geom;
        """
        
        buildings_result = osm_service._execute_query(buildings_query)
        buildings = []
        
        if buildings_result.get('success'):
            for element in buildings_result.get('data', {}).get('elements', []):
                building = {
                    'id': element.get('id'),
                    'name': element.get('tags', {}).get('name'),
                    'building_type': element.get('tags', {}).get('building', 'yes'),
                    'address': osm_service._format_address(element.get('tags', {})),
                    'levels': element.get('tags', {}).get('building:levels'),
                    'height': element.get('tags', {}).get('height'),
                    'amenity': element.get('tags', {}).get('amenity'),
                    'coordinates': osm_service._extract_center_coordinates(element)
                }
                buildings.append(building)
        
        # Получаем удобства и инфраструктуру
        amenities_query = f"""
        [out:json][timeout:25];
        (
          node["amenity"](around:{radius},{lat},{lon});
          way["amenity"](around:{radius},{lat},{lon});
          node["shop"](around:{radius},{lat},{lon});
          way["shop"](around:{radius},{lat},{lon});
          node["leisure"](around:{radius},{lat},{lon});
          way["leisure"](around:{radius},{lat},{lon});
          node["tourism"](around:{radius},{lat},{lon});
          way["tourism"](around:{radius},{lat},{lon});
        );
        out geom;
        """
        
        amenities_result = osm_service._execute_query(amenities_query)
        amenities = []
        
        if amenities_result.get('success'):
            for element in amenities_result.get('data', {}).get('elements', []):
                tags = element.get('tags', {})
                amenity = {
                    'id': element.get('id'),
                    'name': tags.get('name'),
                    'amenity': tags.get('amenity') or tags.get('shop') or tags.get('leisure') or tags.get('tourism'),
                    'category': osm_service._categorize_amenity(tags),
                    'address': osm_service._format_address(tags),
                    'coordinates': osm_service._extract_center_coordinates(element)
                }
                amenities.append(amenity)
        
        return jsonify({
            'success': True,
            'context': {
                'buildings': buildings,
                'amenities': amenities,
                'center_coordinates': {'lat': lat, 'lon': lon},
                'radius': radius,
                'building_count': len(buildings),
                'amenity_count': len(amenities)
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error in get_urban_context: {e}")
        return jsonify({'error': str(e)}), 500

@osm_bp.route('/health', methods=['GET'])
def health():
    """Проверка состояния OSM сервиса"""
    try:
        if osm_service is None:
            return jsonify({'status': 'error', 'error': 'OSM service not initialized'}), 500
        
        # Простой тестовый запрос
        test_result = osm_service.search_by_name("test", limit=1)
        
        return jsonify({
            'status': 'healthy',
            'service': 'OSM Overpass API',
            'available': test_result.get('success', False)
        }), 200
    
    except Exception as e:
        logger.error(f"OSM health check error: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500
