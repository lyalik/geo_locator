#!/usr/bin/env python3
"""
Скрипт создания всех необходимых таблиц в базе данных PostgreSQL для Geo Locator
Используется при развертывании на новых серверах и для инициализации базы данных.

Запуск:
    python create_database_tables.py

Переменные окружения:
    DATABASE_URL - URL подключения к PostgreSQL
    POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD - альтернативные параметры
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine, text, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Загрузка переменных окружения из .env файла
try:
    from dotenv import load_dotenv
    # Ищем .env файл в текущей директории и родительских
    env_path = None
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Проверяем текущую директорию
    if os.path.exists(os.path.join(current_dir, '.env')):
        env_path = os.path.join(current_dir, '.env')
    # Проверяем родительскую директорию (корень проекта)
    elif os.path.exists(os.path.join(os.path.dirname(current_dir), '.env')):
        env_path = os.path.join(os.path.dirname(current_dir), '.env')
    
    if env_path:
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from: {env_path}")
    else:
        print("⚠️  .env file not found, using system environment variables")
        
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables")
    print("   Install with: pip install python-dotenv")

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Базовый класс для моделей
Base = declarative_base()

# ================================
# МОДЕЛИ ТАБЛИЦ
# ================================

class User(Base):
    """Пользователи системы"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200))
    role = Column(String(50), default='user')  # user, admin, moderator
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Связи
    photos = relationship("Photo", back_populates="user")
    violations = relationship("Violation", back_populates="user")

class Photo(Base):
    """Загруженные фотографии"""
    __tablename__ = 'photos'
    
    id = Column(Integer, primary_key=True)
    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # Координаты
    lat = Column(Float)
    lon = Column(Float)
    altitude = Column(Float)
    accuracy = Column(Float)
    
    # Метаданные изображения
    width = Column(Integer)
    height = Column(Integer)
    camera_make = Column(String(100))
    camera_model = Column(String(100))
    date_taken = Column(DateTime)
    
    # Адресная информация
    address_data = Column(JSON)  # Хранит адрес, источник координат, confidence
    
    # Системные поля
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    
    # Связи
    user = relationship("User", back_populates="photos")
    violations = relationship("Violation", back_populates="photo")

class Violation(Base):
    """Обнаруженные нарушения"""
    __tablename__ = 'violations'
    
    id = Column(Integer, primary_key=True)
    
    # Основная информация
    category = Column(String(100), nullable=False)  # Тип нарушения
    description = Column(Text)
    confidence = Column(Float)  # Уверенность детекции (0.0 - 1.0)
    source = Column(String(50))  # yolo, mistral_ai, manual
    
    # Координаты нарушения
    lat = Column(Float)
    lon = Column(Float)
    
    # Bounding box для объекта на изображении
    bbox_data = Column(JSON)  # {x, y, width, height, normalized}
    
    # Связанные данные
    photo_id = Column(Integer, ForeignKey('photos.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Статус обработки
    status = Column(String(50), default='detected')  # detected, verified, false_positive, resolved
    priority = Column(String(20), default='medium')  # low, medium, high, critical
    
    # Временные метки
    detected_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    photo = relationship("Photo", back_populates="violations")
    user = relationship("User", back_populates="violations")
    detected_objects = relationship("DetectedObject", back_populates="violation")

class DetectedObject(Base):
    """Обнаруженные объекты на изображениях"""
    __tablename__ = 'detected_objects'
    
    id = Column(Integer, primary_key=True)
    
    # Информация об объекте
    class_name = Column(String(100), nullable=False)  # Класс объекта (car, person, building, etc.)
    confidence = Column(Float, nullable=False)  # Уверенность детекции
    source = Column(String(50), default='yolo')  # Источник детекции
    
    # Bounding box
    bbox_x = Column(Float)
    bbox_y = Column(Float)
    bbox_width = Column(Float)
    bbox_height = Column(Float)
    bbox_normalized = Column(Boolean, default=True)
    
    # Связи
    violation_id = Column(Integer, ForeignKey('violations.id'))
    photo_id = Column(Integer, ForeignKey('photos.id'), nullable=False)
    
    # Временная метка
    detected_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    violation = relationship("Violation", back_populates="detected_objects")

class GeoImage(Base):
    """Геопривязанные изображения для архивного поиска"""
    __tablename__ = 'geo_images'
    
    id = Column(Integer, primary_key=True)
    
    # Файловая информация
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), unique=True, nullable=False)  # SHA-256
    file_size = Column(Integer)
    
    # Координаты
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    accuracy = Column(Float)
    
    # Метаданные изображения
    width = Column(Integer)
    height = Column(Integer)
    format = Column(String(10))  # JPEG, PNG, etc.
    camera_make = Column(String(100))
    camera_model = Column(String(100))
    
    # Временные метки
    date_taken = Column(DateTime)
    date_uploaded = Column(DateTime, default=datetime.utcnow)
    date_modified = Column(DateTime, default=datetime.utcnow)
    
    # Адресная информация
    address = Column(Text)
    city = Column(String(100))
    region = Column(String(100))
    country = Column(String(100))
    
    # Теги и описание
    tags = Column(Text)  # JSON array
    description = Column(Text)
    user_notes = Column(Text)
    
    # Статус обработки
    processed = Column(Boolean, default=False)
    has_gps = Column(Boolean, default=False)
    geo_source = Column(String(50))  # 'exif', 'manual', 'api_match'
    
    # Связанные данные
    yandex_place_id = Column(String(100))
    dgis_place_id = Column(String(100))
    satellite_match_score = Column(Float)

class AnalysisSession(Base):
    """Сессии анализа для отслеживания пакетной обработки"""
    __tablename__ = 'analysis_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), unique=True, nullable=False)
    
    # Информация о сессии
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_type = Column(String(50))  # batch_upload, coordinate_analysis, violation_detection
    
    # Статистика
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    successful_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    
    # Статус
    status = Column(String(50), default='running')  # running, completed, failed, cancelled
    
    # Временные метки
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Результаты
    results_summary = Column(JSON)
    error_log = Column(Text)

class SystemLog(Base):
    """Системные логи для мониторинга"""
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True)
    
    # Информация о событии
    level = Column(String(20), nullable=False)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    module = Column(String(100))  # Модуль/сервис, который создал лог
    
    # Контекст
    user_id = Column(Integer, ForeignKey('users.id'))
    session_id = Column(String(100))
    request_id = Column(String(100))
    
    # Дополнительные данные
    extra_data = Column(JSON)
    
    # Временная метка
    created_at = Column(DateTime, default=datetime.utcnow)

# ================================
# ФУНКЦИИ СОЗДАНИЯ БАЗЫ ДАННЫХ
# ================================

def get_database_url():
    """Получение URL подключения к базе данных"""
    # Проверяем DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    
    # Собираем из отдельных параметров
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    database = os.getenv('POSTGRES_DB', 'geo_locator')
    username = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', 'password')
    
    return f"postgresql://{username}:{password}@{host}:{port}/{database}"

def create_database_if_not_exists(database_url):
    """Создание базы данных если она не существует"""
    try:
        # Подключаемся к postgres для создания БД
        from urllib.parse import urlparse
        parsed = urlparse(database_url)
        
        # URL для подключения к postgres
        postgres_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/postgres"
        
        engine = create_engine(postgres_url)
        conn = engine.connect()
        conn.execute(text("COMMIT"))  # Завершаем текущую транзакцию
        
        # Проверяем существование БД
        db_name = parsed.path[1:]  # Убираем ведущий слеш
        result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
        
        if not result.fetchone():
            logger.info(f"Creating database: {db_name}")
            conn.execute(text(f"CREATE DATABASE {db_name}"))
            logger.info(f"✅ Database {db_name} created successfully")
        else:
            logger.info(f"✅ Database {db_name} already exists")
        
        conn.close()
        
    except Exception as e:
        logger.warning(f"Could not create database: {e}")
        logger.info("Assuming database already exists or will be created manually")

def create_tables(database_url):
    """Создание всех таблиц"""
    try:
        logger.info("Connecting to database...")
        engine = create_engine(database_url)
        
        logger.info("Creating all tables...")
        Base.metadata.create_all(engine)
        
        logger.info("✅ All tables created successfully!")
        
        # Проверяем созданные таблицы
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            logger.info(f"📊 Created tables: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        return False

def create_admin_user(database_url):
    """Создание администратора по умолчанию"""
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Проверяем, есть ли уже пользователи
        existing_user = session.query(User).filter_by(username='admin').first()
        
        if not existing_user:
            from werkzeug.security import generate_password_hash
            
            admin_user = User(
                username='admin',
                email='admin@geolocator.local',
                password_hash=generate_password_hash('admin123'),
                full_name='System Administrator',
                role='admin',
                is_active=True
            )
            
            session.add(admin_user)
            session.commit()
            
            logger.info("✅ Default admin user created:")
            logger.info("   Username: admin")
            logger.info("   Password: admin123")
            logger.info("   Email: admin@geolocator.local")
        else:
            logger.info("✅ Admin user already exists")
        
        session.close()
        
    except Exception as e:
        logger.error(f"❌ Error creating admin user: {e}")

def create_indexes(database_url):
    """Создание индексов для оптимизации производительности"""
    try:
        engine = create_engine(database_url)
        
        indexes = [
            # Индексы для быстрого поиска по координатам
            "CREATE INDEX IF NOT EXISTS idx_photos_coordinates ON photos (lat, lon);",
            "CREATE INDEX IF NOT EXISTS idx_violations_coordinates ON violations (lat, lon);",
            "CREATE INDEX IF NOT EXISTS idx_geo_images_coordinates ON geo_images (latitude, longitude);",
            
            # Индексы для поиска по времени
            "CREATE INDEX IF NOT EXISTS idx_photos_uploaded_at ON photos (uploaded_at);",
            "CREATE INDEX IF NOT EXISTS idx_violations_detected_at ON violations (detected_at);",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs (created_at);",
            
            # Индексы для поиска по пользователям
            "CREATE INDEX IF NOT EXISTS idx_photos_user_id ON photos (user_id);",
            "CREATE INDEX IF NOT EXISTS idx_violations_user_id ON violations (user_id);",
            
            # Индексы для поиска по статусам
            "CREATE INDEX IF NOT EXISTS idx_violations_status ON violations (status);",
            "CREATE INDEX IF NOT EXISTS idx_violations_category ON violations (category);",
            
            # Индекс для хешей файлов
            "CREATE INDEX IF NOT EXISTS idx_geo_images_file_hash ON geo_images (file_hash);",
        ]
        
        with engine.connect() as conn:
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    conn.commit()
                except Exception as e:
                    logger.warning(f"Index creation warning: {e}")
        
        logger.info("✅ Database indexes created successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error creating indexes: {e}")

def main():
    """Основная функция"""
    logger.info("🚀 Starting Geo Locator database initialization...")
    
    # Получаем URL базы данных
    database_url = get_database_url()
    logger.info(f"Database URL: {database_url.replace(database_url.split('@')[0].split('//')[1], '***')}")
    
    try:
        # 1. Создаем базу данных если нужно
        create_database_if_not_exists(database_url)
        
        # 2. Создаем таблицы
        if not create_tables(database_url):
            sys.exit(1)
        
        # 3. Создаем индексы
        create_indexes(database_url)
        
        # 4. Создаем администратора
        create_admin_user(database_url)
        
        logger.info("🎉 Database initialization completed successfully!")
        logger.info("")
        logger.info("📋 Summary:")
        logger.info("   ✅ Database created/verified")
        logger.info("   ✅ All tables created")
        logger.info("   ✅ Indexes created")
        logger.info("   ✅ Admin user created")
        logger.info("")
        logger.info("🔐 Default credentials:")
        logger.info("   Username: admin")
        logger.info("   Password: admin123")
        logger.info("")
        logger.info("🚀 Your Geo Locator database is ready!")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
