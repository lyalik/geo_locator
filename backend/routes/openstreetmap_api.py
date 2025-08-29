from flask import Blueprint, request, jsonify
import logging
try:
    from services.openstreetmap_service import (
        sync_geocode_address,
        sync_reverse_geocode,
        sync_get_buildings_in_area,
        sync_analyze_urban_context,
        sync_search_places
    )
    OSM_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: OpenStreetMap service not available: {e}")
    OSM_SERVICE_AVAILABLE = False
    
    # Mock functions for when service is not available
    def sync_geocode_address(address, country_code='ru'):
        return [{"display_name": f"Mock result for {address}", "lat": "55.7558", "lon": "37.6176"}]
    
    def sync_reverse_geocode(lat, lon, zoom=18):
        return {"display_name": f"Mock address for {lat}, {lon}"}
    
    def sync_get_buildings_in_area(lat, lon, radius):
        return []
    
    def sync_analyze_urban_context(lat, lon):
        return {"area_type": "urban", "building_density": 0.5, "amenity_count": 10}
    
    def sync_search_places(query, lat=None, lon=None, radius=10000):
        return [{"display_name": f"Mock result for {query}", "lat": "55.7558", "lon": "37.6176"}]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('openstreetmap_api', __name__, url_prefix='/api/osm')

@bp.route('/geocode', methods=['GET'])
def geocode_address():
    """
    Geocode address using OpenStreetMap Nominatim.
    
    Query Parameters:
        address (str): Address to geocode
        country_code (str, optional): Country code (default: 'ru')
        
    Returns:
        JSON response with geocoding results
    """
    try:
        address = request.args.get('address')
        country_code = request.args.get('country_code', 'ru')
        
        if not address:
            return jsonify({'error': 'Address parameter is required'}), 400
        
        logger.info(f"Geocoding address: {address}")
        results = sync_geocode_address(address, country_code)
        
        return jsonify({
            'success': True,
            'count': len(results),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in geocoding: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/reverse-geocode', methods=['GET'])
@bp.route('/reverse_geocode', methods=['GET'])
def reverse_geocode():
    """
    Reverse geocode coordinates using OpenStreetMap Nominatim.
    
    Query Parameters:
        lat (float): Latitude
        lon (float): Longitude
        zoom (int, optional): Detail level 1-18 (default: 18)
        
    Returns:
        JSON response with reverse geocoding result
    """
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        zoom = request.args.get('zoom', type=int, default=18)
        
        if lat is None or lon is None:
            return jsonify({'error': 'Latitude and longitude parameters are required'}), 400
        
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return jsonify({'error': 'Invalid coordinates'}), 400
        
        if not (1 <= zoom <= 18):
            return jsonify({'error': 'Zoom level must be between 1 and 18'}), 400
        
        logger.info(f"Reverse geocoding: {lat}, {lon}")
        result = sync_reverse_geocode(lat, lon, zoom)
        
        if result:
            return jsonify({
                'success': True,
                'result': result
            })
        else:
            return jsonify({'error': 'No results found'}), 404
        
    except Exception as e:
        logger.error(f"Error in reverse geocoding: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/buildings', methods=['GET'])
def get_buildings():
    """
    Get buildings in area using OpenStreetMap Overpass API.
    
    Query Parameters:
        lat (float): Center latitude
        lon (float): Center longitude
        radius (int, optional): Search radius in meters (default: 100)
        
    Returns:
        JSON response with buildings in area
    """
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', type=int, default=100)
        
        if lat is None or lon is None:
            return jsonify({'error': 'Latitude and longitude parameters are required'}), 400
        
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return jsonify({'error': 'Invalid coordinates'}), 400
        
        if not (10 <= radius <= 2000):
            return jsonify({'error': 'Radius must be between 10 and 2000 meters'}), 400
        
        logger.info(f"Getting buildings around: {lat}, {lon} (radius: {radius}m)")
        buildings = sync_get_buildings_in_area(lat, lon, radius)
        
        # Convert OSMBuilding objects to dictionaries
        buildings_data = [building.__dict__ for building in buildings]
        
        return jsonify({
            'success': True,
            'count': len(buildings_data),
            'center': {'lat': lat, 'lon': lon, 'radius': radius},
            'buildings': buildings_data
        })
        
    except Exception as e:
        logger.error(f"Error getting buildings: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/search', methods=['GET'])
def search_places():
    """
    Search for places using OpenStreetMap Nominatim.
    
    Query Parameters:
        query (str): Search query
        lat (float, optional): Center latitude for bounded search
        lon (float, optional): Center longitude for bounded search
        radius (int, optional): Search radius in meters (default: 10000)
        
    Returns:
        JSON response with search results
    """
    try:
        query = request.args.get('query')
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', type=int, default=10000)
        
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        if lat is not None and lon is not None:
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                return jsonify({'error': 'Invalid coordinates'}), 400
        
        logger.info(f"Searching places: {query}")
        results = sync_search_places(query, lat, lon, radius)
        
        # Convert OSMFeature objects to dictionaries
        results_data = [result.__dict__ for result in results]
        
        return jsonify({
            'success': True,
            'count': len(results_data),
            'query': query,
            'center': {'lat': lat, 'lon': lon} if lat and lon else None,
            'results': results_data
        })
        
    except Exception as e:
        logger.error(f"Error searching places: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/analyze', methods=['POST'])
@bp.route('/urban-context', methods=['GET'])
def analyze_urban_context():
    """
    Analyze urban context around coordinates.
    
    For GET requests - Query Parameters:
        lat (float): Latitude
        lon (float): Longitude
        radius (int): Search radius in meters
        
    For POST requests - JSON Body:
        lat (float): Latitude
        lon (float): Longitude
        
    Returns:
        JSON response with comprehensive urban analysis
    """
    try:
        # Handle both GET and POST requests
        if request.method == 'GET':
            lat = request.args.get('lat', type=float)
            lon = request.args.get('lon', type=float)
            radius = request.args.get('radius', type=int, default=1000)
        else:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'JSON body is required'}), 400
            lat = data.get('lat', type=float)
            lon = data.get('lon', type=float)
            radius = data.get('radius', 1000)
        
        if lat is None or lon is None:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return jsonify({'error': 'Invalid coordinates'}), 400
        
        logger.info(f"Analyzing urban context: {lat}, {lon}")
        
        # Get buildings and urban context
        buildings = sync_get_buildings_in_area(lat, lon, radius)
        analysis = sync_analyze_urban_context(lat, lon)
        
        # Format response for urban-context endpoint
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'context': {
                    'buildings': buildings[:50] if buildings else [],  # Limit to 50 buildings
                    'amenities': analysis.get('amenities', []) if isinstance(analysis, dict) else [],
                    'area_type': analysis.get('area_type', 'unknown') if isinstance(analysis, dict) else 'urban',
                    'building_density': analysis.get('building_density', 0.5) if isinstance(analysis, dict) else 0.5,
                    'coordinates': {'lat': lat, 'lon': lon, 'radius': radius}
                }
            })
        else:
            return jsonify({
                'success': True,
                'analysis': analysis
            })
        
    except Exception as e:
        logger.error(f"Error analyzing urban context: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/compare_locations', methods=['POST'])
def compare_locations():
    """
    Compare urban context between multiple locations.
    
    JSON Body:
        locations (list): List of {lat, lon, name} objects
        
    Returns:
        JSON response with comparative analysis
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body is required'}), 400
        
        locations = data.get('locations', [])
        
        if not locations or len(locations) < 2:
            return jsonify({'error': 'At least 2 locations are required for comparison'}), 400
        
        if len(locations) > 5:
            return jsonify({'error': 'Maximum 5 locations allowed for comparison'}), 400
        
        logger.info(f"Comparing {len(locations)} locations")
        
        # Analyze each location
        analyses = []
        for location in locations:
            lat = location.get('lat')
            lon = location.get('lon')
            name = location.get('name', f"Location {len(analyses) + 1}")
            
            if lat is None or lon is None:
                continue
            
            analysis = sync_analyze_urban_context(lat, lon)
            analysis['location_name'] = name
            analyses.append(analysis)
        
        # Generate comparison summary
        comparison = {
            'total_locations': len(analyses),
            'locations': analyses,
            'comparison_summary': {
                'building_density_range': {
                    'min': min(a.get('building_density', 0) for a in analyses),
                    'max': max(a.get('building_density', 0) for a in analyses),
                    'avg': sum(a.get('building_density', 0) for a in analyses) / len(analyses)
                },
                'area_types': list(set(a.get('area_type', 'unknown') for a in analyses)),
                'total_amenities': sum(a.get('amenity_count', 0) for a in analyses),
                'most_urban': max(analyses, key=lambda x: x.get('building_density', 0))['location_name'],
                'least_urban': min(analyses, key=lambda x: x.get('building_density', 0))['location_name']
            }
        }
        
        return jsonify({
            'success': True,
            'comparison': comparison
        })
        
    except Exception as e:
        logger.error(f"Error comparing locations: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/building_analysis', methods=['POST'])
def analyze_building_compliance():
    """
    Analyze building compliance based on OSM data and detected violations.
    
    JSON Body:
        lat (float): Latitude
        lon (float): Longitude
        violation_types (list, optional): Types of violations detected
        
    Returns:
        JSON response with building compliance analysis
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body is required'}), 400
        
        lat = data.get('lat', type=float)
        lon = data.get('lon', type=float)
        violation_types = data.get('violation_types', [])
        
        if lat is None or lon is None:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        logger.info(f"Analyzing building compliance: {lat}, {lon}")
        
        # Get buildings and urban context
        buildings = sync_get_buildings_in_area(lat, lon, 100)
        urban_context = sync_analyze_urban_context(lat, lon)
        
        # Analyze each building for compliance issues
        compliance_analysis = []
        for building in buildings:
            building_analysis = {
                'building': building.__dict__,
                'compliance_issues': [],
                'risk_level': 'low'
            }
            
            # Check for missing required data
            if not building.name and building.building_type not in ['house', 'residential']:
                building_analysis['compliance_issues'].append('missing_name')
            
            if not building.address:
                building_analysis['compliance_issues'].append('missing_address')
            
            # Check building type consistency
            if building.amenity and building.building_type == 'residential':
                building_analysis['compliance_issues'].append('mixed_use_in_residential')
            
            # Check for unusual building characteristics
            if building.levels and building.levels > 20:
                building_analysis['compliance_issues'].append('high_rise_building')
            
            # Determine risk level
            issue_count = len(building_analysis['compliance_issues'])
            if issue_count == 0:
                building_analysis['risk_level'] = 'low'
            elif issue_count <= 2:
                building_analysis['risk_level'] = 'medium'
            else:
                building_analysis['risk_level'] = 'high'
            
            compliance_analysis.append(building_analysis)
        
        # Generate summary
        total_buildings = len(compliance_analysis)
        high_risk_count = sum(1 for b in compliance_analysis if b['risk_level'] == 'high')
        medium_risk_count = sum(1 for b in compliance_analysis if b['risk_level'] == 'medium')
        low_risk_count = total_buildings - high_risk_count - medium_risk_count
        
        return jsonify({
            'success': True,
            'location': {'lat': lat, 'lon': lon},
            'urban_context': urban_context,
            'summary': {
                'total_buildings': total_buildings,
                'high_risk': high_risk_count,
                'medium_risk': medium_risk_count,
                'low_risk': low_risk_count,
                'compliance_rate': (low_risk_count / total_buildings * 100) if total_buildings > 0 else 0
            },
            'building_analysis': compliance_analysis,
            'violation_types': violation_types
        })
        
    except Exception as e:
        logger.error(f"Error analyzing building compliance: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for OpenStreetMap service."""
    return jsonify({
        'service': 'openstreetmap_api',
        'status': 'healthy',
        'endpoints': [
            '/geocode',
            '/reverse_geocode',
            '/buildings',
            '/search',
            '/analyze',
            '/compare_locations',
            '/building_analysis'
        ]
    })

@bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404

@bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500
