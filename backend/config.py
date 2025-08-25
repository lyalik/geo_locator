import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST', 'localhost')}:5432/{os.getenv('POSTGRES_DB')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')
    
    # API Keys
    YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')
    DGIS_API_KEY = os.getenv('DGIS_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    SENTINEL_INSTANCE_ID = os.getenv('SENTINEL_INSTANCE_ID')
    SENTINEL_CLIENT_ID = os.getenv('SENTINEL_CLIENT_ID')
    SENTINEL_CLIENT_SECRET = os.getenv('SENTINEL_CLIENT_SECRET')