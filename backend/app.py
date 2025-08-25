from flask import Flask, request, jsonify
from celery import Celery
from config import Config
from models import SessionLocal, init_db
from routes.maps import init_app as init_maps_routes
import os
import asyncio
import aiohttp

app = Flask(__name__)
app.config.from_object(Config)

# Celery
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    return celery

celery = make_celery(app)

# Initialize database and routes
init_db()
init_maps_routes(app)

# Эндпоинты
@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files')  # 1-5 файлов
    text = request.form.get('text', '')  # Текстовый контекст
    mode = request.form.get('mode', 'normal')  # normal, panorama, video
    
    if not files or len(files) > 5:
        return jsonify({'error': 'Invalid files'}), 400
    
    # Сохраняем файлы временно
    upload_dir = 'uploads'
    os.makedirs(upload_dir, exist_ok=True)
    file_paths = []
    for file in files:
        if file.filename.split('.')[-1].lower() not in ['jpeg', 'jpg', 'png', 'mp4', 'mov']:
            return jsonify({'error': 'Unsupported format'}), 400
        path = os.path.join(upload_dir, file.filename)
        file.save(path)
        file_paths.append(path)
    
    # Запускаем Celery таску
    task = process_media.delay(file_paths, text, mode)
    
    return jsonify({'task_id': task.id}), 202

@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    task = celery.AsyncResult(task_id)
    return jsonify({'status': task.status})

@app.route('/result/<task_id>', methods=['GET'])
def get_result(task_id):
    task = celery.AsyncResult(task_id)
    if task.status == 'SUCCESS':
        return jsonify(task.result)
    return jsonify({'status': task.status}), 202

# Для внешней интеграции (e.g., от ИНС системы)
@app.route('/api/coords', methods=['POST'])
def api_coords():
    # Аналогично upload, но для интеграции
    data = request.json
    file_paths = data.get('file_paths')  # Или URL к фото от внешней системы
    text = data.get('text')
    mode = data.get('mode', 'normal')
    # ... (обработка)
    task = process_media.delay(file_paths, text, mode)
    return jsonify({'task_id': task.id})

@app.teardown_appcontext
def shutdown_session(exception=None):
    """Close database session on app teardown"""
    db_session = SessionLocal()
    db_session.close()

if __name__ == '__main__':
    # Create uploads directory if it doesn't exist
    os.makedirs('uploads', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)