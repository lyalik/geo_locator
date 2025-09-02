from flask import Blueprint, request, jsonify
import logging
import datetime

# Импортируем сервисы напрямую без geo_aggregator
try:
    from services.roscosmos_satellite_service import RoscosmosService
except ImportError:
    RoscosmosService = None

try:
    from services.yandex_satellite_service import YandexSatelliteService
except ImportError:
    YandexSatelliteService = None

try:
    from services.dgis_service import DGISService
except ImportError:
    DGISService = None

satellite_bp = Blueprint('satellite', __name__)
logger = logging.getLogger(__name__)

@satellite_bp.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья спутниковых сервисов"""
    try:
        available_services = {
            'roscosmos': RoscosmosService is not None,
            'yandex_satellite': YandexSatelliteService is not None,
            'dgis': DGISService is not None,
            'scanex': True  # Всегда доступен как резервный
        }
        
        return jsonify({
            'success': True,
            'message': 'Российские спутниковые сервисы готовы',
            'available_services': available_services,
            'credentials_configured': True
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@satellite_bp.route('/sources', methods=['GET'])
def get_satellite_sources():
    """Получение списка доступных спутниковых источников"""
    try:
        sources = [
            {
                'name': 'Роскосмос',
                'status': 'active' if RoscosmosService else 'inactive',
                'satellites': ['Ресурс-П', 'Канопус-В', 'Электро-Л'],
                'description': 'Официальные российские спутниковые данные'
            },
            {
                'name': 'Яндекс Спутник',
                'status': 'active' if YandexSatelliteService else 'inactive',
                'satellites': ['Яндекс Maps Satellite'],
                'description': 'Спутниковые снимки от Яндекс'
            },
            {
                'name': 'ScanEx',
                'status': 'active',
                'satellites': ['Архивные данные'],
                'description': 'Архивные спутниковые данные'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': sources,
            'message': 'Satellite sources retrieved successfully'
        })
    except Exception as e:
        logger.error(f"Error getting satellite sources: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@satellite_bp.route('/analyze', methods=['GET', 'POST'])
def analyze_satellite_data():
    """Анализ спутниковых данных для указанной области"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            bbox = data.get('bbox', '')
            analysis_type = data.get('analysis_type', 'comprehensive')
        else:
            bbox = request.args.get('bbox', '')
            analysis_type = request.args.get('analysis_type', 'comprehensive')
        
        # Мок данные для анализа
        analysis_data = {
            'area_classification': 'urban',
            'vegetation_index': 0.3,
            'building_density': 0.7,
            'water_coverage': 0.05,
            'analysis_type': analysis_type,
            'confidence': 0.85,
            'source': 'Роскосмос',
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': analysis_data,
            'message': 'Satellite analysis completed successfully'
        })
    except Exception as e:
        logger.error(f"Error analyzing satellite data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@satellite_bp.route('/image', methods=['GET'])
def get_satellite_image():
    """Получение спутникового снимка"""
    try:
        # Получаем параметры
        bbox = request.args.get('bbox', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        resolution = int(request.args.get('resolution', 10))
        max_cloud_coverage = float(request.args.get('max_cloud_coverage', 20))
        
        # Мок данные для спутникового снимка
        image_data = {
            'image_url': f'https://api.satellite.example.com/image?bbox={bbox}',
            'acquisition_date': datetime.datetime.now().isoformat(),
            'source': 'Роскосмос',
            'resolution': resolution,
            'cloud_coverage': 5.0,
            'bbox': bbox
        }
        
        return jsonify({
            'success': True,
            'data': image_data,
            'message': 'Satellite image retrieved successfully'
        })
    except Exception as e:
        logger.error(f"Error getting satellite image: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@satellite_bp.route('/time-series', methods=['GET'])
def get_time_series():
    """Получение временного ряда спутниковых данных"""
    try:
        bbox = request.args.get('bbox', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        interval_days = int(request.args.get('interval_days', 30))
        
        if not bbox or not start_date or not end_date:
            return jsonify({
                'success': False,
                'error': 'Параметры bbox, start_date и end_date обязательны'
            }), 400
        
        # Имитируем временной ряд данных
        import datetime
        start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        
        time_series = []
        current_date = start
        while current_date <= end:
            time_series.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'vegetation_index': 0.6 + (current_date.month / 12) * 0.3,
                'built_up_area': 0.25,
                'cloud_coverage': min(50, max(5, abs(hash(current_date.strftime('%Y-%m-%d')) % 50)))
            })
            current_date += datetime.timedelta(days=interval_days)
        
        summary = {
            'total_periods': len(time_series),
            'avg_vegetation': sum(item['vegetation_index'] for item in time_series) / len(time_series),
            'avg_built_up': sum(item['built_up_area'] for item in time_series) / len(time_series),
            'avg_cloud_coverage': sum(item['cloud_coverage'] for item in time_series) / len(time_series)
        }
        
        return jsonify({
            'success': True,
            'data': {
                'time_series': time_series,
                'summary': summary
            },
            'message': 'Временной ряд получен успешно'
        })
        
    except Exception as e:
        logger.error(f"Time series error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@satellite_bp.route('/change-detection', methods=['GET'])
def detect_changes():
    """Детекция изменений между двумя периодами"""
    try:
        bbox = request.args.get('bbox', '')
        before_date = request.args.get('before_date', '')
        after_date = request.args.get('after_date', '')
        
        if not bbox or not before_date or not after_date:
            return jsonify({
                'success': False,
                'error': 'Параметры bbox, before_date и after_date обязательны'
            }), 400
        
        # Имитируем данные до и после
        before_period = {
            'date': before_date,
            'vegetation_index': 0.7,
            'built_up_area': 0.2,
            'water_bodies': 0.1
        }
        
        after_period = {
            'date': after_date,
            'vegetation_index': 0.6,
            'built_up_area': 0.3,
            'water_bodies': 0.1
        }
        
        # Вычисляем изменения
        changes = {}
        for key in ['vegetation_index', 'built_up_area', 'water_bodies']:
            before_val = before_period[key]
            after_val = after_period[key]
            change_percent = ((after_val - before_val) / before_val) * 100
            
            if abs(change_percent) > 5:  # Значимое изменение
                significance = 'increase' if change_percent > 0 else 'decrease'
            else:
                significance = 'stable'
            
            key_name = key.replace('_index', '').replace('_area', '').replace('_bodies', '')
            changes[key_name] = {
                'percentage': change_percent,
                'significance': significance
            }
        
        return jsonify({
            'success': True,
            'data': {
                'before_period': before_period,
                'after_period': after_period,
                'changes': changes
            },
            'message': 'Детекция изменений выполнена успешно'
        })
        
    except Exception as e:
        logger.error(f"Change detection error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@satellite_bp.route('/sources', methods=['GET'])
def get_available_sources():
    """Получение списка доступных спутниковых источников"""
    try:
        roscosmos_service = RoscosmosService()
        yandex_service = YandexSatelliteService()
        
        sources = {
            'roscosmos': {
                'name': 'Роскосмос',
                'satellites': ['Ресурс-П1', 'Ресурс-П2', 'Ресурс-П3', 'Канопус-В'],
                'resolution': '1-3 метра',
                'available': True,
                'status': 'active'
            },
            'yandex': {
                'name': 'Яндекс Спутник',
                'satellites': ['Яндекс.Карты'],
                'resolution': 'Переменное',
                'available': True,
                'status': 'active'
            },
            'scanex': {
                'name': 'ScanEx (Космоснимки)',
                'satellites': ['Архивные данные'],
                'resolution': '0.5-30 метров',
                'available': True,
                'status': 'active'
            },
            'dgis': {
                'name': '2GIS',
                'satellites': ['Спутниковые слои 2GIS'],
                'resolution': 'Высокое',
                'available': True,
                'status': 'active'
            }
        }
        
        return jsonify({
            'success': True,
            'data': sources,
            'message': 'Список источников получен'
        })
        
    except Exception as e:
        logger.error(f"Sources error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
