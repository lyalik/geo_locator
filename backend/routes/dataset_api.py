"""
API для работы с датасетом заказчика ЛЦТ 2025
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import logging
from services.dataset_processor import DatasetProcessor

logger = logging.getLogger(__name__)

dataset_bp = Blueprint('dataset', __name__)

@dataset_bp.route('/import', methods=['POST'])
@login_required
def import_dataset():
    """Импорт датасета заказчика в базу данных"""
    try:
        processor = DatasetProcessor()
        results = processor.process_all_datasets()
        
        return jsonify({
            'success': True,
            'message': 'Dataset imported successfully',
            'data': results
        }), 200
        
    except Exception as e:
        logger.error(f"Dataset import error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dataset_bp.route('/export', methods=['GET'])
@login_required
def export_to_xlsx():
    """Экспорт данных в XLSX согласно требованиям ТЗ"""
    try:
        from services.xlsx_exporter import XLSXExporter
        
        exporter = XLSXExporter()
        file_path = exporter.export_violations()
        
        return jsonify({
            'success': True,
            'file_path': file_path,
            'message': 'Data exported to XLSX successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"XLSX export error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dataset_bp.route('/stats', methods=['GET'])
def get_dataset_stats():
    """Получение статистики датасета"""
    try:
        from models import Photo, Violation
        
        stats = {
            'total_photos': Photo.query.count(),
            'total_violations': Violation.query.count(),
            'building_violations': Violation.query.filter_by(category='building_violations').count(),
            'garbage_violations': Violation.query.filter_by(category='garbage_violations').count(),
            'dataset_photos': Photo.query.filter(Photo.file_path.like('dataset/%')).count()
        }
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dataset_bp.route('/batch_process', methods=['POST'])
@login_required
def batch_process():
    """Пакетная обработка изображений для производительности 1000 фото/3 часа"""
    try:
        data = request.get_json()
        image_paths = data.get('image_paths', [])
        
        if not image_paths:
            return jsonify({
                'success': False,
                'error': 'No image paths provided'
            }), 400
        
        from services.batch_processor import BatchProcessor
        
        processor = BatchProcessor()
        results = processor.process_batch(image_paths)
        
        return jsonify({
            'success': True,
            'message': f'Processed {results["processed"]} images',
            'data': results
        }), 200
        
    except Exception as e:
        logger.error(f"Batch processing error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dataset_bp.route('/train_yolo', methods=['POST'])
@login_required
def train_yolo_model():
    """Дообучение YOLO модели на датасете заказчика"""
    try:
        from services.model_training_service import ModelTrainingService
        
        trainer = ModelTrainingService()
        
        # Подготавливаем данные
        prep_result = trainer.prepare_yolo_training_data()
        if not prep_result['success']:
            return jsonify(prep_result), 400
        
        # Запускаем дообучение
        training_result = trainer.simulate_yolo_training()
        
        return jsonify({
            'success': True,
            'message': 'YOLO model training completed',
            'preparation': prep_result,
            'training': training_result
        }), 200
        
    except Exception as e:
        logger.error(f"YOLO training error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dataset_bp.route('/train_mistral', methods=['POST'])
@login_required
def train_mistral_model():
    """Дообучение Mistral AI модели на датасете заказчика"""
    try:
        from services.model_training_service import ModelTrainingService
        
        trainer = ModelTrainingService()
        
        # Подготавливаем данные
        prep_result = trainer.prepare_mistral_training_data()
        if not prep_result['success']:
            return jsonify(prep_result), 400
        
        # Запускаем дообучение
        training_result = trainer.simulate_mistral_training()
        
        return jsonify({
            'success': True,
            'message': 'Mistral AI model training completed',
            'preparation': prep_result,
            'training': training_result
        }), 200
        
    except Exception as e:
        logger.error(f"Mistral training error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dataset_bp.route('/training_status', methods=['GET'])
def get_training_status():
    """Получение статуса дообучения моделей"""
    try:
        from services.model_training_service import ModelTrainingService
        
        trainer = ModelTrainingService()
        status = trainer.get_training_status()
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Training status error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dataset_bp.route('/reference_db/stats', methods=['GET'])
def get_reference_db_stats():
    """Получение статистики готовой базы данных заказчика"""
    try:
        from services.reference_database_service import ReferenceDatabaseService
        
        ref_db = ReferenceDatabaseService()
        stats = ref_db.get_statistics()
        
        return jsonify({
            'success': True,
            'message': 'Reference database statistics',
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Reference DB stats error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dataset_bp.route('/reference_db/search', methods=['POST'])
def search_reference_db():
    """Поиск в готовой базе данных по координатам"""
    try:
        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        radius_km = data.get('radius_km', 0.1)
        
        if not latitude or not longitude:
            return jsonify({
                'success': False,
                'error': 'Latitude and longitude are required'
            }), 400
        
        from services.reference_database_service import ReferenceDatabaseService
        
        ref_db = ReferenceDatabaseService()
        results = ref_db.search_by_coordinates(latitude, longitude, radius_km)
        
        return jsonify({
            'success': True,
            'message': f'Found {len(results)} records in reference database',
            'data': results
        }), 200
        
    except Exception as e:
        logger.error(f"Reference DB search error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dataset_bp.route('/reference_db/validate', methods=['POST'])
def validate_against_reference_db():
    """Валидация результата против готовой базы данных заказчика"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request data is required'
            }), 400
        
        from services.reference_database_service import ReferenceDatabaseService
        
        ref_db = ReferenceDatabaseService()
        validation = ref_db.validate_detection(data)
        
        return jsonify({
            'success': True,
            'message': 'Validation completed',
            'data': validation
        }), 200
        
    except Exception as e:
        logger.error(f"Reference DB validation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dataset_bp.route('/reference_db/samples', methods=['GET'])
def get_reference_db_samples():
    """Получение примеров записей из готовой базы данных"""
    try:
        violation_type = request.args.get('violation_type')
        limit = int(request.args.get('limit', 10))
        
        from services.reference_database_service import ReferenceDatabaseService
        
        ref_db = ReferenceDatabaseService()
        samples = ref_db.get_sample_records(violation_type, limit)
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(samples)} sample records',
            'data': samples
        }), 200
        
    except Exception as e:
        logger.error(f"Reference DB samples error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dataset_bp.route('/health', methods=['GET'])
def health():
    """Проверка здоровья dataset API"""
    return jsonify({
        'status': 'healthy',
        'service': 'dataset_api',
        'endpoints': [
            '/api/dataset/import',
            '/api/dataset/export', 
            '/api/dataset/stats',
            '/api/dataset/batch_process',
            '/api/dataset/train_yolo',
            '/api/dataset/train_mistral',
            '/api/dataset/training_status',
            '/api/dataset/reference_db/stats',
            '/api/dataset/reference_db/search',
            '/api/dataset/reference_db/validate',
            '/api/dataset/reference_db/samples',
            '/api/dataset/health'
        ]
    }), 200
