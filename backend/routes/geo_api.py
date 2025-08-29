#!/usr/bin/env python3
"""
API для комплексной системы геолокации
"""
import os
import logging
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
import uuid
from datetime import datetime

from ..services.geo_aggregator_service import GeoAggregatorService
from ..services.image_database_service import ImageDatabaseService
from ..services.yandex_maps_service import YandexMapsService
from ..services.dgis_service import DGISService

logger = logging.getLogger(__name__)

geo_bp = Blueprint('geo_api', __name__, url_prefix='/api/geo')

# Инициализация сервисов
geo_aggregator = GeoAggregatorService()
image_db = ImageDatabaseService()
yandex_service = YandexMapsService()
dgis_service = DGISService()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads', 'temp')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@geo_bp.route('/health', methods=['GET'])
def health():
    """Проверка состояния геолокационных сервисов"""
    try:
        stats = geo_aggregator.get_location_statistics()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'statistics': stats
        }), 200
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@geo_bp.route('/locate', methods=['POST'])
def locate_image():
    """
    Главный endpoint для определения местоположения изображения
    """
    try:
        # Проверяем наличие файла
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Сохраняем временный файл
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Получаем дополнительные параметры
        location_hint = request.form.get('location_hint', '')
        user_description = request.form.get('description', '')
        
        try:
            # Выполняем геолокацию
            result = geo_aggregator.locate_image(
                file_path, 
                location_hint, 
                user_description
            )
            
            # Добавляем информацию о пользователе (если авторизован)
            try:
                from flask_login import current_user
                if current_user.is_authenticated:
                    result['user_id'] = current_user.id
                else:
                    result['user_id'] = 'anonymous'
            except:
                result['user_id'] = 'anonymous'
            result['processed_at'] = datetime.utcnow().isoformat()
            
            return jsonify(result), 200
            
        finally:
            # Удаляем временный файл
            if os.path.exists(file_path):
                os.remove(file_path)
    
    except Exception as e:
        logger.error(f"Error in locate_image: {e}")
        return jsonify({'error': str(e)}), 500

@geo_bp.route('/search/places', methods=['GET'])
def search_places():
    """
    Поиск мест через Yandex Maps и 2GIS
    """
    try:
        query = request.args.get('q', '')
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', 1000, type=int)
        source = request.args.get('source', 'all')  # 'yandex', 'dgis', 'all'
        
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        results = {'sources': {}}
        
        # Поиск через Yandex Maps
        if source in ['yandex', 'all']:
            yandex_result = yandex_service.search_places(query, lat, lon, radius)
            results['sources']['yandex'] = yandex_result
        
        # Поиск через 2GIS
        if source in ['dgis', 'all']:
            dgis_result = dgis_service.search_places(query, lat, lon, radius)
            results['sources']['dgis'] = dgis_result
        
        # Объединяем результаты
        all_places = []
        for source_name, source_result in results['sources'].items():
            if source_result.get('success'):
                for place in source_result.get('places', []):
                    place['source'] = source_name
                    all_places.append(place)
        
        results['combined_results'] = {
            'total_found': len(all_places),
            'places': all_places[:20]  # Топ 20 результатов
        }
        
        return jsonify(results), 200
    
    except Exception as e:
        logger.error(f"Error in search_places: {e}")
        return jsonify({'error': str(e)}), 500

@geo_bp.route('/geocode', methods=['GET'])
def geocode_address():
    """
    Геокодирование адреса
    """
    try:
        address = request.args.get('address', '')
        source = request.args.get('source', 'yandex')  # 'yandex' или 'dgis'
        
        if not address:
            return jsonify({'error': 'Address parameter is required'}), 400
        
        if source == 'yandex':
            result = yandex_service.geocode(address)
        elif source == 'dgis':
            result = dgis_service.geocode(address)
        else:
            return jsonify({'error': 'Invalid source parameter'}), 400
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error in geocode_address: {e}")
        return jsonify({'error': str(e)}), 500

@geo_bp.route('/reverse-geocode', methods=['GET'])
def reverse_geocode():
    """
    Обратное геокодирование - получение адреса по координатам
    """
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        source = request.args.get('source', 'yandex')
        
        if lat is None or lon is None:
            return jsonify({'error': 'Latitude and longitude parameters are required'}), 400
        
        if source == 'yandex':
            result = yandex_service.reverse_geocode(lat, lon)
        elif source == 'dgis':
            result = dgis_service.reverse_geocode(lat, lon)
        else:
            return jsonify({'error': 'Invalid source parameter'}), 400
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error in reverse_geocode: {e}")
        return jsonify({'error': str(e)}), 500

@geo_bp.route('/images/search', methods=['GET'])
def search_images():
    """
    Поиск изображений в базе данных
    """
    try:
        query = request.args.get('q', '')
        has_gps = request.args.get('has_gps', type=bool)
        city = request.args.get('city', '')
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', 1000, type=int)
        
        if lat and lon:
            # Поиск по координатам
            results = image_db.find_similar_images(lat, lon, radius)
        else:
            # Поиск по текстовому запросу
            results = image_db.search_images(
                query=query if query else None,
                has_gps=has_gps,
                city=city if city else None
            )
        
        return jsonify({
            'success': True,
            'total_found': len(results),
            'images': results
        }), 200
    
    except Exception as e:
        logger.error(f"Error in search_images: {e}")
        return jsonify({'error': str(e)}), 500

@geo_bp.route('/images/<image_id>', methods=['GET'])
def get_image_info(image_id):
    """
    Получение информации об изображении
    """
    try:
        image_info = image_db.get_image_info(image_id)
        if not image_info:
            return jsonify({'error': 'Image not found'}), 404
        
        return jsonify(image_info), 200
    
    except Exception as e:
        logger.error(f"Error in get_image_info: {e}")
        return jsonify({'error': str(e)}), 500

@geo_bp.route('/images/<image_id>/thumbnail', methods=['GET'])
def get_image_thumbnail(image_id):
    """
    Получение миниатюры изображения
    """
    try:
        thumbnail_path = os.path.join(image_db.thumbnail_dir, f"{image_id}.jpg")
        
        if not os.path.exists(thumbnail_path):
            return jsonify({'error': 'Thumbnail not found'}), 404
        
        return send_file(thumbnail_path, mimetype='image/jpeg')
    
    except Exception as e:
        logger.error(f"Error in get_image_thumbnail: {e}")
        return jsonify({'error': str(e)}), 500

@geo_bp.route('/images/<image_id>/location', methods=['PUT'])
def update_image_location(image_id):
    """
    Обновление геолокации изображения
    """
    try:
        data = request.get_json()
        lat = data.get('latitude')
        lon = data.get('longitude')
        source = data.get('source', 'manual')
        
        if lat is None or lon is None:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        result = image_db.update_location(image_id, lat, lon, source)
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        logger.error(f"Error in update_image_location: {e}")
        return jsonify({'error': str(e)}), 500

@geo_bp.route('/nearby', methods=['GET'])
def find_nearby_places():
    """
    Поиск ближайших мест определенной категории
    """
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        category = request.args.get('category', '')
        radius = request.args.get('radius', 1000, type=int)
        source = request.args.get('source', 'dgis')
        
        if lat is None or lon is None:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        if source == 'dgis':
            result = dgis_service.find_nearby_places(lat, lon, category, radius)
        else:
            return jsonify({'error': 'Only 2GIS source is supported for nearby search'}), 400
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error in find_nearby_places: {e}")
        return jsonify({'error': str(e)}), 500

@geo_bp.route('/static-map', methods=['GET'])
def get_static_map():
    """
    Получение статической карты
    """
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        zoom = request.args.get('zoom', 15, type=int)
        width = request.args.get('width', 600, type=int)
        height = request.args.get('height', 400, type=int)
        
        if lat is None or lon is None:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        result = yandex_service.get_static_map(lat, lon, zoom, width, height)
        
        if result.get('success'):
            return result['image_data'], 200, {
                'Content-Type': result['content_type']
            }
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error in get_static_map: {e}")
        return jsonify({'error': str(e)}), 500

@geo_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """
    Получение статистики системы геолокации
    """
    try:
        stats = geo_aggregator.get_location_statistics()
        return jsonify(stats), 200
    
    except Exception as e:
        logger.error(f"Error in get_statistics: {e}")
        return jsonify({'error': str(e)}), 500
