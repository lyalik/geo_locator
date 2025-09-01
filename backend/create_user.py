#!/usr/bin/env python3
"""
Script to create a user with proper password hashing
"""
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Load environment variables
load_dotenv('.env')

from app import app, db
from models import User

def create_user(username, email, password):
    """Create a user with properly hashed password"""
    with app.app_context():
        try:
            # Check if user already exists
            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                print(f"❌ User with username '{username}' or email '{email}' already exists")
                return False
            
            # Create new user with hashed password
            hashed_password = generate_password_hash(password)
            new_user = User(
                username=username,
                email=email,
                password=hashed_password
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            print(f"✅ User '{username}' created successfully!")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create user: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("👤 Creating user 'lyalik1'...")
    success = create_user('lyalik1', 'lyalik1@example.com', 'lyalik1')
    
    if success:
        print("\n🎉 User created! You can now login with:")
        print("Username: lyalik1")
        print("Password: lyalik1")
    else:
        print("\n❌ Failed to create user")
