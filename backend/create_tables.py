#!/usr/bin/env python3
"""
Script to create database tables for Geo Locator
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

from app import app, db
from models import User, Photo, Violation, ProcessingTask, Notification, UserNotificationPreferences

def create_tables():
    """Create all database tables"""
    with app.app_context():
        try:
            # Drop all tables first (for clean setup)
            print("🗑️ Dropping existing tables...")
            db.drop_all()
            
            # Create all tables
            print("🏗️ Creating database tables...")
            db.create_all()
            
            # Verify tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"✅ Created {len(tables)} tables:")
            for table in sorted(tables):
                print(f"   - {table}")
            
            # Create a default user for testing
            existing_user = User.query.filter_by(username='admin').first()
            if not existing_user:
                default_user = User(
                    username='admin',
                    email='admin@geolocator.com',
                    password='admin123'  # In production, this should be hashed
                )
                db.session.add(default_user)
                db.session.commit()
                print("👤 Created default admin user (username: admin, password: admin123)")
            else:
                print("👤 Default admin user already exists")
            
            print("\n🎉 Database setup completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("🚀 Geo Locator Database Setup")
    print("=" * 40)
    
    success = create_tables()
    
    if success:
        print("\n✅ Ready to start the application!")
        print("Run: python3 run_local.py")
    else:
        print("\n❌ Database setup failed. Check the errors above.")
