from flask import Blueprint, request, jsonify, current_app
from services.cache_service import CacheManager, cache

# Create blueprint
bp = Blueprint('cache_api', __name__, url_prefix='/api/cache')

@bp.route('/info', methods=['GET'])
def get_cache_info():
    """Get comprehensive cache information and statistics."""
    try:
        cache_info = CacheManager.get_cache_info()
        return jsonify({
            'success': True,
            'data': cache_info,
            'error': None
        })
    except Exception as e:
        current_app.logger.error(f"Cache info error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': None
        }), 500

@bp.route('/clear', methods=['POST'])
def clear_cache():
    """Clear cache entries by type or all cache."""
    try:
        data = request.get_json() or {}
        cache_type = data.get('type', 'all')
        
        if cache_type == 'all':
            success = CacheManager.clear_all_cache()
            message = "All cache cleared" if success else "Failed to clear cache"
        else:
            cleared_count = CacheManager.clear_cache_by_type(cache_type)
            message = f"Cleared {cleared_count} entries for type {cache_type}"
            success = True
        
        return jsonify({
            'success': success,
            'message': message,
            'error': None
        })
        
    except Exception as e:
        current_app.logger.error(f"Cache clear error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': None
        }), 500

@bp.route('/warm-up', methods=['POST'])
def warm_up_cache():
    """Warm up cache with common data."""
    try:
        CacheManager.warm_up_cache()
        return jsonify({
            'success': True,
            'message': 'Cache warm-up completed',
            'error': None
        })
    except Exception as e:
        current_app.logger.error(f"Cache warm-up error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': None
        }), 500

@bp.route('/cleanup', methods=['POST'])
def cleanup_cache():
    """Clean up expired cache entries."""
    try:
        CacheManager.cleanup_expired()
        return jsonify({
            'success': True,
            'message': 'Cache cleanup completed',
            'error': None
        })
    except Exception as e:
        current_app.logger.error(f"Cache cleanup error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': None
        }), 500
