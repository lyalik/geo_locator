from flask import Blueprint, request, jsonify
import logging
from services.rosreestr_service import (
    sync_search_by_address,
    sync_get_property_by_cadastral_number,
    sync_validate_property_usage,
    sync_get_properties_by_coordinates
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('rosreestr_api', __name__, url_prefix='/api/rosreestr')

@bp.route('/search/address', methods=['GET'])
def search_by_address():
    """
    Search properties by address.
    
    Query Parameters:
        address (str): Property address to search
        
    Returns:
        JSON response with property list
    """
    try:
        address = request.args.get('address')
        if not address:
            return jsonify({'error': 'Address parameter is required'}), 400
        
        logger.info(f"Searching properties by address: {address}")
        properties = sync_search_by_address(address)
        
        return jsonify({
            'success': True,
            'count': len(properties),
            'properties': properties
        })
        
    except Exception as e:
        logger.error(f"Error in address search: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/property/<cadastral_number>', methods=['GET'])
def get_property_info(cadastral_number):
    """
    Get property information by cadastral number.
    
    Path Parameters:
        cadastral_number (str): Property cadastral number
        
    Returns:
        JSON response with property details
    """
    try:
        logger.info(f"Getting property info for: {cadastral_number}")
        property_info = sync_get_property_by_cadastral_number(cadastral_number)
        
        if not property_info:
            return jsonify({'error': 'Property not found'}), 404
        
        return jsonify({
            'success': True,
            'property': property_info.__dict__
        })
        
    except Exception as e:
        logger.error(f"Error getting property info: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/search/coordinates', methods=['GET'])
def search_by_coordinates():
    """
    Search properties by coordinates.
    
    Query Parameters:
        lat (float): Latitude
        lon (float): Longitude
        radius (int, optional): Search radius in meters (default: 100)
        
    Returns:
        JSON response with properties in area
    """
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', type=int, default=100)
        
        if lat is None or lon is None:
            return jsonify({'error': 'Latitude and longitude parameters are required'}), 400
        
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return jsonify({'error': 'Invalid coordinates'}), 400
        
        logger.info(f"Searching properties by coordinates: {lat}, {lon} (radius: {radius}m)")
        properties = sync_get_properties_by_coordinates(lat, lon, radius)
        
        # Convert PropertyInfo objects to dictionaries
        properties_data = [prop.__dict__ for prop in properties]
        
        return jsonify({
            'success': True,
            'count': len(properties_data),
            'coordinates': {'lat': lat, 'lon': lon, 'radius': radius},
            'properties': properties_data
        })
        
    except Exception as e:
        logger.error(f"Error in coordinate search: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/validate/usage', methods=['POST'])
def validate_property_usage():
    """
    Validate property usage compliance.
    
    JSON Body:
        cadastral_number (str): Property cadastral number
        current_usage (str): Current observed usage
        
    Returns:
        JSON response with validation result
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body is required'}), 400
        
        cadastral_number = data.get('cadastral_number')
        current_usage = data.get('current_usage')
        
        if not cadastral_number or not current_usage:
            return jsonify({'error': 'cadastral_number and current_usage are required'}), 400
        
        logger.info(f"Validating usage for property: {cadastral_number}")
        validation_result = sync_validate_property_usage(cadastral_number, current_usage)
        
        return jsonify({
            'success': True,
            'validation': validation_result
        })
        
    except Exception as e:
        logger.error(f"Error validating property usage: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/analyze/location', methods=['POST'])
def analyze_location():
    """
    Comprehensive location analysis combining property data with violation detection.
    
    JSON Body:
        lat (float): Latitude
        lon (float): Longitude
        image_path (str, optional): Path to violation image
        violation_types (list, optional): Types of violations to check
        
    Returns:
        JSON response with comprehensive analysis
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body is required'}), 400
        
        lat = data.get('lat', type=float)
        lon = data.get('lon', type=float)
        image_path = data.get('image_path')
        violation_types = data.get('violation_types', ['unauthorized_construction', 'usage_violation'])
        
        if lat is None or lon is None:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        logger.info(f"Analyzing location: {lat}, {lon}")
        
        # Get properties in the area
        properties = sync_get_properties_by_coordinates(lat, lon, radius=50)
        properties_data = [prop.__dict__ for prop in properties]
        
        # Analyze each property for potential violations
        analysis_results = []
        for prop in properties:
            # Basic property analysis
            property_analysis = {
                'property': prop.__dict__,
                'risk_factors': [],
                'compliance_status': 'unknown'
            }
            
            # Check for risk factors
            if not prop.building_year and prop.category == 'building':
                property_analysis['risk_factors'].append('missing_construction_date')
            
            if prop.area > 5000:
                property_analysis['risk_factors'].append('large_area')
            
            if 'жилая' in prop.permitted_use.lower() and any(word in prop.address.lower() 
                for word in ['магазин', 'офис', 'салон', 'кафе']):
                property_analysis['risk_factors'].append('potential_usage_violation')
            
            # Determine compliance status
            if len(property_analysis['risk_factors']) == 0:
                property_analysis['compliance_status'] = 'compliant'
            elif len(property_analysis['risk_factors']) <= 2:
                property_analysis['compliance_status'] = 'needs_review'
            else:
                property_analysis['compliance_status'] = 'high_risk'
            
            analysis_results.append(property_analysis)
        
        # Summary statistics
        total_properties = len(analysis_results)
        compliant_count = sum(1 for r in analysis_results if r['compliance_status'] == 'compliant')
        high_risk_count = sum(1 for r in analysis_results if r['compliance_status'] == 'high_risk')
        
        return jsonify({
            'success': True,
            'location': {'lat': lat, 'lon': lon},
            'summary': {
                'total_properties': total_properties,
                'compliant': compliant_count,
                'needs_review': total_properties - compliant_count - high_risk_count,
                'high_risk': high_risk_count
            },
            'properties': properties_data,
            'analysis': analysis_results,
            'timestamp': request.headers.get('X-Request-Time', 'unknown')
        })
        
    except Exception as e:
        logger.error(f"Error analyzing location: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Rosreestr service."""
    return jsonify({
        'service': 'rosreestr_api',
        'status': 'healthy',
        'endpoints': [
            '/search/address',
            '/property/<cadastral_number>',
            '/search/coordinates',
            '/validate/usage',
            '/analyze/location'
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
