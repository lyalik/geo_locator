import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = (
        os.getenv('DATABASE_URL')
        or f"postgresql+psycopg2://{os.getenv('POSTGRES_USER','postgres')}:{os.getenv('POSTGRES_PASSWORD','postgres')}@{os.getenv('POSTGRES_HOST', 'localhost')}:5432/{os.getenv('POSTGRES_DB','geo_locator')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'uploads'))
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # API Keys
    YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')
    DGIS_API_KEY = os.getenv('DGIS_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    SENTINEL_INSTANCE_ID = os.getenv('SENTINEL_INSTANCE_ID')
    SENTINEL_CLIENT_ID = os.getenv('SENTINEL_CLIENT_ID')
    SENTINEL_CLIENT_SECRET = os.getenv('SENTINEL_CLIENT_SECRET')