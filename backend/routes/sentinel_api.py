"""
Sentinel Hub API endpoints for satellite imagery
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime, timedelta
from ..services.sentinel_service import SentinelHubService

logger = logging.getLogger(__name__)

sentinel_api = Blueprint('sentinel_api', __name__)
sentinel_service = SentinelHubService()

@sentinel_api.route('/satellite-image', methods=['GET'])
def get_satellite_image():
    """Get satellite image for specified area and time period"""
    try:
        # Get parameters
        bbox_str = request.args.get('bbox')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        resolution = int(request.args.get('resolution', 10))
        max_cloud_coverage = float(request.args.get('max_cloud_coverage', 20.0))
        bands_str = request.args.get('bands', 'B02,B03,B04,B08')
        
        # Validate required parameters
        if not bbox_str:
            return jsonify({'error': 'bbox parameter is required'}), 400
        
        # Parse bbox
        try:
            bbox = [float(x.strip()) for x in bbox_str.split(',')]
            if len(bbox) != 4:
                raise ValueError("bbox must contain 4 coordinates")
        except (ValueError, AttributeError) as e:
            return jsonify({'error': f'Invalid bbox format: {e}'}), 400
        
        # Set default dates if not provided
        if not date_to:
            date_to = datetime.now().strftime('%Y-%m-%d')
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Parse bands
        bands = [band.strip() for band in bands_str.split(',')]
        
        # Get satellite image
        satellite_image = sentinel_service.get_satellite_image_sync(
            bbox=bbox,
            date_from=date_from,
            date_to=date_to,
            resolution=resolution,
            max_cloud_coverage=max_cloud_coverage,
            bands=bands
        )
        
        if satellite_image:
            return jsonify({
                'success': True,
                'data': {
                    'image_url': satellite_image.image_url,
                    'acquisition_date': satellite_image.acquisition_date,
                    'cloud_coverage': satellite_image.cloud_coverage,
                    'bbox': satellite_image.bbox,
                    'resolution': satellite_image.resolution,
                    'bands': satellite_image.bands,
                    'metadata': satellite_image.metadata
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No satellite image found for the specified parameters'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting satellite image: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@sentinel_api.route('/image-analysis', methods=['GET'])
def analyze_satellite_image():
    """Analyze satellite image for vegetation, built-up areas, etc."""
    try:
        # Get parameters
        bbox_str = request.args.get('bbox')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Validate required parameters
        if not bbox_str:
            return jsonify({'error': 'bbox parameter is required'}), 400
        
        # Parse bbox
        try:
            bbox = [float(x.strip()) for x in bbox_str.split(',')]
            if len(bbox) != 4:
                raise ValueError("bbox must contain 4 coordinates")
        except (ValueError, AttributeError) as e:
            return jsonify({'error': f'Invalid bbox format: {e}'}), 400
        
        # Set default dates if not provided
        if not date_to:
            date_to = datetime.now().strftime('%Y-%m-%d')
        if not date_from:
            date_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Analyze satellite image
        analysis = sentinel_service.analyze_satellite_image_sync(
            bbox=bbox,
            date_from=date_from,
            date_to=date_to
        )
        
        if analysis:
            return jsonify({
                'success': True,
                'data': {
                    'vegetation_index': analysis.vegetation_index,
                    'built_up_area': analysis.built_up_area,
                    'water_bodies': analysis.water_bodies,
                    'bare_soil': analysis.bare_soil,
                    'cloud_coverage': analysis.cloud_coverage,
                    'change_detection': analysis.change_detection
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Could not analyze satellite image for the specified parameters'
            }), 404
            
    except Exception as e:
        logger.error(f"Error analyzing satellite image: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@sentinel_api.route('/time-series', methods=['GET'])
def get_time_series_analysis():
    """Get time series analysis for change detection"""
    try:
        # Get parameters
        bbox_str = request.args.get('bbox')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        interval_days = int(request.args.get('interval_days', 30))
        
        # Validate required parameters
        if not bbox_str:
            return jsonify({'error': 'bbox parameter is required'}), 400
        
        # Parse bbox
        try:
            bbox = [float(x.strip()) for x in bbox_str.split(',')]
            if len(bbox) != 4:
                raise ValueError("bbox must contain 4 coordinates")
        except (ValueError, AttributeError) as e:
            return jsonify({'error': f'Invalid bbox format: {e}'}), 400
        
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # Get time series analysis
        analyses = sentinel_service.get_time_series_analysis_sync(
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            interval_days=interval_days
        )
        
        return jsonify({
            'success': True,
            'data': {
                'time_series': [
                    {
                        'vegetation_index': analysis.vegetation_index,
                        'built_up_area': analysis.built_up_area,
                        'water_bodies': analysis.water_bodies,
                        'bare_soil': analysis.bare_soil,
                        'cloud_coverage': analysis.cloud_coverage,
                        'change_detection': analysis.change_detection
                    }
                    for analysis in analyses
                ],
                'summary': {
                    'total_periods': len(analyses),
                    'avg_vegetation': sum(a.vegetation_index for a in analyses) / len(analyses) if analyses else 0,
                    'avg_built_up': sum(a.built_up_area for a in analyses) / len(analyses) if analyses else 0,
                    'avg_cloud_coverage': sum(a.cloud_coverage for a in analyses) / len(analyses) if analyses else 0
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting time series analysis: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@sentinel_api.route('/change-detection', methods=['GET'])
def detect_changes():
    """Detect changes between two time periods"""
    try:
        # Get parameters
        bbox_str = request.args.get('bbox')
        before_date = request.args.get('before_date')
        after_date = request.args.get('after_date')
        
        # Validate required parameters
        if not bbox_str:
            return jsonify({'error': 'bbox parameter is required'}), 400
        
        # Parse bbox
        try:
            bbox = [float(x.strip()) for x in bbox_str.split(',')]
            if len(bbox) != 4:
                raise ValueError("bbox must contain 4 coordinates")
        except (ValueError, AttributeError) as e:
            return jsonify({'error': f'Invalid bbox format: {e}'}), 400
        
        # Set default dates if not provided
        if not after_date:
            after_date = datetime.now().strftime('%Y-%m-%d')
        if not before_date:
            before_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # Get analysis for both periods
        before_analysis = sentinel_service.analyze_satellite_image_sync(
            bbox=bbox,
            date_from=(datetime.strptime(before_date, '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d'),
            date_to=before_date
        )
        
        after_analysis = sentinel_service.analyze_satellite_image_sync(
            bbox=bbox,
            date_from=(datetime.strptime(after_date, '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d'),
            date_to=after_date
        )
        
        if not before_analysis or not after_analysis:
            return jsonify({
                'success': False,
                'error': 'Could not get analysis for one or both time periods'
            }), 404
        
        # Calculate changes
        vegetation_change = after_analysis.vegetation_index - before_analysis.vegetation_index
        built_up_change = after_analysis.built_up_area - before_analysis.built_up_area
        water_change = after_analysis.water_bodies - before_analysis.water_bodies
        
        # Determine change significance
        def get_change_significance(change_value, threshold=0.1):
            if abs(change_value) < threshold:
                return "minimal"
            elif change_value > threshold:
                return "increase"
            else:
                return "decrease"
        
        return jsonify({
            'success': True,
            'data': {
                'before_period': {
                    'date': before_date,
                    'vegetation_index': before_analysis.vegetation_index,
                    'built_up_area': before_analysis.built_up_area,
                    'water_bodies': before_analysis.water_bodies
                },
                'after_period': {
                    'date': after_date,
                    'vegetation_index': after_analysis.vegetation_index,
                    'built_up_area': after_analysis.built_up_area,
                    'water_bodies': after_analysis.water_bodies
                },
                'changes': {
                    'vegetation': {
                        'value': vegetation_change,
                        'percentage': (vegetation_change / before_analysis.vegetation_index * 100) if before_analysis.vegetation_index > 0 else 0,
                        'significance': get_change_significance(vegetation_change)
                    },
                    'built_up': {
                        'value': built_up_change,
                        'percentage': (built_up_change / before_analysis.built_up_area * 100) if before_analysis.built_up_area > 0 else 0,
                        'significance': get_change_significance(built_up_change)
                    },
                    'water': {
                        'value': water_change,
                        'percentage': (water_change / before_analysis.water_bodies * 100) if before_analysis.water_bodies > 0 else 0,
                        'significance': get_change_significance(water_change)
                    }
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error detecting changes: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@sentinel_api.route('/configure', methods=['POST'])
def configure_credentials():
    """Configure Sentinel Hub credentials"""
    try:
        data = request.get_json()
        
        if not data or 'client_id' not in data or 'client_secret' not in data:
            return jsonify({'error': 'client_id and client_secret are required'}), 400
        
        sentinel_service.configure_credentials(
            client_id=data['client_id'],
            client_secret=data['client_secret']
        )
        
        return jsonify({
            'success': True,
            'message': 'Sentinel Hub credentials configured successfully'
        })
        
    except Exception as e:
        logger.error(f"Error configuring credentials: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@sentinel_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check if credentials are configured
        credentials_configured = (
            sentinel_service.client_id is not None and 
            sentinel_service.client_secret is not None
        )
        
        return jsonify({
            'success': True,
            'service': 'Sentinel Hub',
            'status': 'healthy',
            'credentials_configured': credentials_configured,
            'endpoints': [
                '/api/sentinel/satellite-image',
                '/api/sentinel/image-analysis',
                '/api/sentinel/time-series',
                '/api/sentinel/change-detection',
                '/api/sentinel/configure'
            ]
        })
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({'error': 'Internal server error'}), 500
