from celery import Celery
from .app import app as flask_app, db
import os
from datetime import datetime
import requests
import json

# Initialize Celery
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# Use the existing Flask app
app = flask_app
celery = make_celery(app)

@celery.task(bind=True)
def process_search_request(self, request_id):
    """Process a search request asynchronously (placeholder)."""
    with app.app_context():
        try:
            # Placeholder implementation while SearchRequest model is not defined
            # Implement actual logic once model and routes are ready
            return {'status': 'success', 'request_id': request_id}
        except Exception as e:
            raise self.retry(exc=e, countdown=60, max_retries=3)

# Example task for Yandex Maps API
@celery.task(bind=True)
def search_yandex_maps(self, query, api_key):
    """Search location using Yandex Maps API."""
    try:
        base_url = "https://search-maps.yandex.ru/v1/"
        params = {
            'apikey': api_key,
            'text': query,
            'lang': 'ru_RU',
            'type': 'geo',
            'results': 5
        }
        
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise self.retry(exc=e, countdown=60, max_retries=3)

# Example task for 2GIS API
@celery.task(bind=True)
def search_2gis(self, query, api_key):
    """Search location using 2GIS API."""
    try:
        base_url = "https://catalog.api.2gis.com/3.0/items/geocode"
        headers = {
            'Authorization': f'Key {api_key}'
        }
        params = {
            'q': query,
            'fields': 'items.point'
        }
        
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise self.retry(exc=e, countdown=60, max_retries=3)
