#!/usr/bin/env python3
"""
Тест для проверки функции удаления пользователя в админ-панели
"""
import requests
import json

def test_admin_delete():
    base_url = "http://localhost:5001"
    
    # Сначала получим список пользователей
    try:
        response = requests.get(f"{base_url}/admin/users")
        print(f"GET /admin/users: {response.status_code}")
        
        if response.status_code == 200:
            users = response.json().get('data', [])
            print(f"Found {len(users)} users")
            
            # Найдем пользователя для удаления (не админа)
            target_user = None
            for user in users:
                if user.get('role') != 'admin' and user.get('id') != 1:
                    target_user = user
                    break
            
            if target_user:
                print(f"Testing delete for user: {target_user['id']} ({target_user['username']})")
                
                # Попробуем удалить пользователя
                delete_response = requests.delete(f"{base_url}/admin/users/{target_user['id']}")
                print(f"DELETE /admin/users/{target_user['id']}: {delete_response.status_code}")
                print(f"Response: {delete_response.text}")
                
            else:
                print("No suitable user found for deletion test")
        else:
            print(f"Failed to get users: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_admin_delete()
