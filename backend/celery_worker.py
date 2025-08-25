#!/usr/bin/env python3
"""
Celery worker for processing background tasks.
"""
import os
from app import create_app
from celery import Celery
from celery.signals import worker_ready, worker_shutdown

# Create Flask app and configure Celery
app = create_app()
app.app_context().push()

# Initialize Celery
celery = Celery(
    'geo_locator',
    broker=app.config['CELERY_BROKER_URL'],
    backend=app.config['CELERY_RESULT_BACKEND']
)

# Configure Celery
celery.conf.update(app.config)

# Import tasks after Celery is configured to avoid circular imports
from tasks import process_search_request, search_yandex_maps, search_2gis

@worker_ready.connect
def on_worker_ready(**_):
    """Handler for when the worker is ready."""
    app.logger.info('Celery worker is ready')

@worker_shutdown.connect
def on_worker_shutdown(**_):
    """Handler for when the worker shuts down."""
    app.logger.info('Celery worker is shutting down')

if __name__ == '__main__':
    # Start the Celery worker
    celery.worker_main(['worker', '--loglevel=info'])
