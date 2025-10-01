#!/usr/bin/env python3
"""
Скрипт миграции и обновления базы данных Geo Locator
Используется для обновления существующих баз данных до новой схемы.

Запуск:
    python migrate_database.py

Функции:
- Проверка существующих таблиц
- Добавление недостающих колонок
- Создание недостающих таблиц
- Миграция данных между версиями
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine, text, inspect, MetaData, Table, Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.exc import SQLAlchemyError

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

def get_database_url():
    """Получение URL подключения к базе данных"""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    database = os.getenv('POSTGRES_DB', 'geo_locator')
    username = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', 'password')
    
    return f"postgresql://{username}:{password}@{host}:{port}/{database}"

def check_table_exists(engine, table_name):
    """Проверка существования таблицы"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def check_column_exists(engine, table_name, column_name):
    """Проверка существования колонки в таблице"""
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        return any(col['name'] == column_name for col in columns)
    except:
        return False

def add_missing_columns(engine):
    """Добавление недостающих колонок в существующие таблицы"""
    migrations = [
        # Добавляем колонки в таблицу photos если их нет
        {
            'table': 'photos',
            'columns': [
                ('original_filename', 'VARCHAR(255)'),
                ('file_size', 'INTEGER'),
                ('mime_type', 'VARCHAR(100)'),
                ('width', 'INTEGER'),
                ('height', 'INTEGER'),
                ('camera_make', 'VARCHAR(100)'),
                ('camera_model', 'VARCHAR(100)'),
                ('date_taken', 'TIMESTAMP'),
                ('processed', 'BOOLEAN DEFAULT FALSE'),
            ]
        },
        
        # Добавляем колонки в таблицу violations если их нет
        {
            'table': 'violations',
            'columns': [
                ('source', 'VARCHAR(50)'),
                ('bbox_data', 'JSON'),
                ('status', 'VARCHAR(50) DEFAULT \'detected\''),
                ('priority', 'VARCHAR(20) DEFAULT \'medium\''),
                ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ]
        },
        
        # Добавляем колонки в таблицу users если их нет
        {
            'table': 'users',
            'columns': [
                ('full_name', 'VARCHAR(200)'),
                ('role', 'VARCHAR(50) DEFAULT \'user\''),
                ('is_active', 'BOOLEAN DEFAULT TRUE'),
                ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
                ('last_login', 'TIMESTAMP'),
            ]
        }
    ]
    
    for migration in migrations:
        table_name = migration['table']
        
        if not check_table_exists(engine, table_name):
            logger.info(f"⏭️  Table {table_name} doesn't exist, skipping column migration")
            continue
            
        logger.info(f"🔍 Checking table {table_name} for missing columns...")
        
        for column_name, column_def in migration['columns']:
            if not check_column_exists(engine, table_name, column_name):
                try:
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def};"
                    with engine.connect() as conn:
                        conn.execute(text(sql))
                        conn.commit()
                    logger.info(f"✅ Added column {column_name} to {table_name}")
                except Exception as e:
                    logger.warning(f"⚠️  Could not add column {column_name} to {table_name}: {e}")

def create_missing_tables(engine):
    """Создание недостающих таблиц"""
    
    # Определяем SQL для создания таблиц
    table_definitions = {
        'geo_images': '''
            CREATE TABLE geo_images (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_hash VARCHAR(64) UNIQUE NOT NULL,
                file_size INTEGER,
                latitude FLOAT,
                longitude FLOAT,
                altitude FLOAT,
                accuracy FLOAT,
                width INTEGER,
                height INTEGER,
                format VARCHAR(10),
                camera_make VARCHAR(100),
                camera_model VARCHAR(100),
                date_taken TIMESTAMP,
                date_uploaded TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                address TEXT,
                city VARCHAR(100),
                region VARCHAR(100),
                country VARCHAR(100),
                tags TEXT,
                description TEXT,
                user_notes TEXT,
                processed BOOLEAN DEFAULT FALSE,
                has_gps BOOLEAN DEFAULT FALSE,
                geo_source VARCHAR(50),
                yandex_place_id VARCHAR(100),
                dgis_place_id VARCHAR(100),
                satellite_match_score FLOAT
            );
        ''',
        
        'detected_objects': '''
            CREATE TABLE detected_objects (
                id SERIAL PRIMARY KEY,
                class_name VARCHAR(100) NOT NULL,
                confidence FLOAT NOT NULL,
                source VARCHAR(50) DEFAULT 'yolo',
                bbox_x FLOAT,
                bbox_y FLOAT,
                bbox_width FLOAT,
                bbox_height FLOAT,
                bbox_normalized BOOLEAN DEFAULT TRUE,
                violation_id INTEGER REFERENCES violations(id),
                photo_id INTEGER REFERENCES photos(id) NOT NULL,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''',
        
        'analysis_sessions': '''
            CREATE TABLE analysis_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(100) UNIQUE NOT NULL,
                user_id INTEGER REFERENCES users(id) NOT NULL,
                session_type VARCHAR(50),
                total_files INTEGER DEFAULT 0,
                processed_files INTEGER DEFAULT 0,
                successful_files INTEGER DEFAULT 0,
                failed_files INTEGER DEFAULT 0,
                status VARCHAR(50) DEFAULT 'running',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                results_summary JSON,
                error_log TEXT
            );
        ''',
        
        'system_logs': '''
            CREATE TABLE system_logs (
                id SERIAL PRIMARY KEY,
                level VARCHAR(20) NOT NULL,
                message TEXT NOT NULL,
                module VARCHAR(100),
                user_id INTEGER REFERENCES users(id),
                session_id VARCHAR(100),
                request_id VARCHAR(100),
                extra_data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        '''
    }
    
    for table_name, table_sql in table_definitions.items():
        if not check_table_exists(engine, table_name):
            try:
                with engine.connect() as conn:
                    conn.execute(text(table_sql))
                    conn.commit()
                logger.info(f"✅ Created table {table_name}")
            except Exception as e:
                logger.error(f"❌ Error creating table {table_name}: {e}")
        else:
            logger.info(f"✅ Table {table_name} already exists")

def update_data_types(engine):
    """Обновление типов данных для совместимости"""
    
    updates = [
        # Обновляем address_data в photos для поддержки JSON
        {
            'condition': lambda: check_table_exists(engine, 'photos') and not check_column_exists(engine, 'photos', 'address_data'),
            'sql': 'ALTER TABLE photos ADD COLUMN address_data JSON;',
            'description': 'Add address_data JSON column to photos'
        },
        
        # Обновляем bbox_data в violations для поддержки JSON
        {
            'condition': lambda: check_table_exists(engine, 'violations') and not check_column_exists(engine, 'violations', 'bbox_data'),
            'sql': 'ALTER TABLE violations ADD COLUMN bbox_data JSON;',
            'description': 'Add bbox_data JSON column to violations'
        }
    ]
    
    for update in updates:
        if update['condition']():
            try:
                with engine.connect() as conn:
                    conn.execute(text(update['sql']))
                    conn.commit()
                logger.info(f"✅ {update['description']}")
            except Exception as e:
                logger.warning(f"⚠️  {update['description']} failed: {e}")

def create_views(engine):
    """Создание полезных представлений (views)"""
    
    views = [
        {
            'name': 'violation_summary',
            'sql': '''
                CREATE OR REPLACE VIEW violation_summary AS
                SELECT 
                    v.category,
                    v.status,
                    v.priority,
                    COUNT(*) as count,
                    AVG(v.confidence) as avg_confidence,
                    MIN(v.detected_at) as first_detected,
                    MAX(v.detected_at) as last_detected
                FROM violations v
                GROUP BY v.category, v.status, v.priority
                ORDER BY count DESC;
            '''
        },
        
        {
            'name': 'user_activity',
            'sql': '''
                CREATE OR REPLACE VIEW user_activity AS
                SELECT 
                    u.username,
                    u.full_name,
                    COUNT(DISTINCT p.id) as photos_uploaded,
                    COUNT(DISTINCT v.id) as violations_detected,
                    MAX(p.uploaded_at) as last_upload,
                    u.last_login
                FROM users u
                LEFT JOIN photos p ON u.id = p.user_id
                LEFT JOIN violations v ON u.id = v.user_id
                GROUP BY u.id, u.username, u.full_name, u.last_login
                ORDER BY photos_uploaded DESC;
            '''
        },
        
        {
            'name': 'coordinate_coverage',
            'sql': '''
                CREATE OR REPLACE VIEW coordinate_coverage AS
                SELECT 
                    'photos' as source_table,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN lat IS NOT NULL AND lon IS NOT NULL THEN 1 END) as with_coordinates,
                    ROUND(
                        COUNT(CASE WHEN lat IS NOT NULL AND lon IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 
                        2
                    ) as coverage_percentage
                FROM photos
                UNION ALL
                SELECT 
                    'violations' as source_table,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN lat IS NOT NULL AND lon IS NOT NULL THEN 1 END) as with_coordinates,
                    ROUND(
                        COUNT(CASE WHEN lat IS NOT NULL AND lon IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 
                        2
                    ) as coverage_percentage
                FROM violations;
            '''
        }
    ]
    
    for view in views:
        try:
            with engine.connect() as conn:
                conn.execute(text(view['sql']))
                conn.commit()
            logger.info(f"✅ Created/updated view {view['name']}")
        except Exception as e:
            logger.warning(f"⚠️  Could not create view {view['name']}: {e}")

def analyze_database(engine):
    """Анализ текущего состояния базы данных"""
    
    logger.info("📊 Analyzing database structure...")
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    logger.info(f"📋 Found {len(tables)} tables:")
    
    for table in sorted(tables):
        try:
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
            
            columns = inspector.get_columns(table)
            logger.info(f"   📄 {table}: {count} records, {len(columns)} columns")
            
        except Exception as e:
            logger.warning(f"   ⚠️  Could not analyze table {table}: {e}")

def main():
    """Основная функция миграции"""
    logger.info("🔄 Starting Geo Locator database migration...")
    
    database_url = get_database_url()
    logger.info(f"Database URL: {database_url.replace(database_url.split('@')[0].split('//')[1], '***')}")
    
    try:
        engine = create_engine(database_url)
        
        # Проверяем подключение
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")
        
        # 1. Анализируем текущее состояние
        analyze_database(engine)
        
        # 2. Создаем недостающие таблицы
        logger.info("🏗️  Creating missing tables...")
        create_missing_tables(engine)
        
        # 3. Добавляем недостающие колонки
        logger.info("🔧 Adding missing columns...")
        add_missing_columns(engine)
        
        # 4. Обновляем типы данных
        logger.info("🔄 Updating data types...")
        update_data_types(engine)
        
        # 5. Создаем представления
        logger.info("👁️  Creating database views...")
        create_views(engine)
        
        # 6. Финальный анализ
        logger.info("📊 Final database analysis:")
        analyze_database(engine)
        
        logger.info("🎉 Database migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
