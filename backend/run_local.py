#!/usr/bin/env python3
"""
Local development server startup script
"""
import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv('.env')

from app import app, db

def setup_database():
    """Initialize database tables"""
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created successfully")
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            return False
    return True

def check_dependencies():
    """Check if required services are running"""
    import psycopg2
    from redis import Redis
    
    # Check PostgreSQL
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            database=os.getenv('POSTGRES_DB', 'geo_locator'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'postgres')
        )
        conn.close()
        print("✅ PostgreSQL connection successful")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("Make sure PostgreSQL is running and database exists")
        return False
    
    # Check Redis
    try:
        redis_client = Redis(host='localhost', port=6379, db=0)
        redis_client.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("Make sure Redis is running on localhost:6379")
        return False
    
    return True

if __name__ == '__main__':
    print("🚀 Starting Geo Locator Backend (Local Development)")
    print("=" * 50)
    
    # Check environment
    if not os.path.exists('.env'):
        print("⚠️  .env file not found. Creating template...")
        with open('.env', 'w') as f:
            f.write("""# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=geo_locator

# Redis Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API Keys (replace with your actual keys)
YANDEX_API_KEY=your_yandex_api_key_here
DGIS_API_KEY=your_dgis_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Security
SECRET_KEY=your-secret-key-for-development
""")
        print("📝 Template .env file created. Please update with your API keys.")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("\n❌ Database setup failed.")
        sys.exit(1)
    
    print("\n🎉 All checks passed! Starting Flask development server...")
    print(f"📍 Backend will be available at: http://localhost:5001")
    print(f"📍 API endpoints at: http://localhost:5001/api/")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start the Flask development server
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        use_reloader=True
    )
