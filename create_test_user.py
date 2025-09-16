#!/usr/bin/env python3
"""
Создание тестового пользователя для тестирования push уведомлений
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.models import db, User
from backend.app import app
from werkzeug.security import generate_password_hash

def create_test_user():
    """Создание тестового пользователя"""
    with app.app_context():
        try:
            # Проверяем, существует ли уже тестовый пользователь
            existing_user = User.query.filter_by(email='test@example.com').first()
            if existing_user:
                print("✅ Тестовый пользователь уже существует")
                print(f"   ID: {existing_user.id}")
                print(f"   Email: {existing_user.email}")
                print(f"   Username: {existing_user.username}")
                return existing_user.id

            # Создаем нового тестового пользователя
            test_user = User(
                username='testuser',
                email='test@example.com',
                password=generate_password_hash('testpass123'),
                is_admin=False
            )
            
            db.session.add(test_user)
            db.session.commit()
            
            print("✅ Тестовый пользователь создан успешно")
            print(f"   ID: {test_user.id}")
            print(f"   Email: {test_user.email}")
            print(f"   Username: {test_user.username}")
            print(f"   Password: testpass123")
            
            return test_user.id
            
        except Exception as e:
            print(f"❌ Ошибка создания тестового пользователя: {e}")
            db.session.rollback()
            return None

if __name__ == "__main__":
    user_id = create_test_user()
    if user_id:
        print(f"\n🎉 Готово! Тестовый пользователь с ID {user_id} готов для тестирования.")
    else:
        print("\n❌ Не удалось создать тестового пользователя.")
