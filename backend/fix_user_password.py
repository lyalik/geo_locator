#!/usr/bin/env python3
"""
Script to fix user password with proper hashing
"""
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Load environment variables
load_dotenv('.env')

from app import app, db
from models import User

def fix_user_password():
    """Fix lyalik1 user password"""
    with app.app_context():
        try:
            # Find the user
            user = User.query.filter_by(username='lyalik1').first()
            
            if not user:
                print("❌ User 'lyalik1' not found")
                return False
            
            # Update password with proper hash
            hashed_password = generate_password_hash('lyalik1')
            user.password = hashed_password
            
            db.session.commit()
            
            print("✅ Password updated successfully!")
            print("Username: lyalik1")
            print("Password: lyalik1")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update password: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("🔑 Fixing password for user 'lyalik1'...")
    fix_user_password()
