#!/usr/bin/env python3
import requests
import json

# Тест авторизации по username
def test_login_by_username():
    url = "http://localhost:5000/auth/login"
    
    # Тест 1: Авторизация по username
    data = {
        "email": "lyalik1",  # Frontend отправляет в поле email
        "password": "password123"  # Замените на реальный пароль
    }
    
    print("🔐 Тестируем авторизацию по username...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Авторизация по username успешна!")
        else:
            print("❌ Ошибка авторизации")
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")

# Тест 2: Авторизация по email для сравнения
def test_login_by_email():
    url = "http://localhost:5000/auth/login"
    
    data = {
        "email": "lyalik@example.com",  # Замените на реальный email
        "password": "password123"
    }
    
    print("\n📧 Тестируем авторизацию по email...")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Авторизация по email успешна!")
        else:
            print("❌ Ошибка авторизации")
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")

if __name__ == "__main__":
    test_login_by_username()
    test_login_by_email()
