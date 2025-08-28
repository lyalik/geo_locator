#!/usr/bin/env python3
import sys
import os
sys.path.append('/home/denis/Documents/Hackathon_2025/geo_locator/backend')

from app import app, db, User

def check_users():
    with app.app_context():
        users = User.query.all()
        print(f"📊 Найдено пользователей: {len(users)}")
        print("-" * 50)
        
        for user in users:
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Password hash: {user.password[:20]}...")
            print("-" * 30)

if __name__ == "__main__":
    check_users()
