#!/usr/bin/env python3
"""
Тестирование системы push уведомлений для мобильного приложения Geo Locator
"""

import requests
import json
import time
from datetime import datetime

# Конфигурация
API_BASE_URL = "http://localhost:5001"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpass123"

# Тестовый Expo push token (для демонстрации)
TEST_PUSH_TOKEN = "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]"

class PushNotificationTester:
    def __init__(self):
        self.session = requests.Session()
        self.user_id = None
        
    def login(self):
        """Авторизация тестового пользователя"""
        try:
            print("🔐 Авторизация пользователя...")
            response = self.session.post(f"{API_BASE_URL}/auth/login", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            
            if response.status_code == 200:
                user_data = response.json()
                self.user_id = user_data.get('user', {}).get('id')
                print(f"✅ Авторизация успешна, user_id: {self.user_id}")
                return True
            else:
                print(f"❌ Ошибка авторизации: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при авторизации: {e}")
            return False
    
    def save_push_token(self):
        """Сохранение push токена"""
        try:
            print("💾 Сохранение push токена...")
            response = self.session.post(f"{API_BASE_URL}/api/notifications/save-push-token", json={
                "pushToken": TEST_PUSH_TOKEN
            })
            
            if response.status_code == 200:
                print("✅ Push токен сохранен успешно")
                return True
            else:
                print(f"❌ Ошибка сохранения токена: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при сохранении токена: {e}")
            return False
    
    def send_test_notification(self):
        """Отправка тестового уведомления"""
        try:
            print("📱 Отправка тестового push уведомления...")
            response = self.session.post(f"{API_BASE_URL}/api/notifications/send-push", json={
                "title": "Тестовое уведомление",
                "body": "Это тестовое push уведомление от Geo Locator",
                "data": {
                    "type": "test",
                    "timestamp": datetime.now().isoformat(),
                    "test_id": "push_test_001"
                }
            })
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Тестовое уведомление отправлено:")
                print(f"   Статус: {result.get('success')}")
                print(f"   Сообщение: {result.get('message')}")
                return True
            else:
                print(f"❌ Ошибка отправки уведомления: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при отправке уведомления: {e}")
            return False
    
    def simulate_violation_detection(self):
        """Симуляция обнаружения нарушения для тестирования автоматических уведомлений"""
        try:
            print("🚨 Симуляция обнаружения нарушения...")
            
            # Создаем тестовый файл изображения
            test_image_data = b"fake_image_data_for_testing"
            files = {
                'file': ('test_violation.jpg', test_image_data, 'image/jpeg')
            }
            
            data = {
                'latitude': '55.7558',
                'longitude': '37.6176'
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/api/violations/detect",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Симуляция обнаружения нарушения завершена:")
                print(f"   Успех: {result.get('success')}")
                print(f"   Нарушений найдено: {len(result.get('violations', []))}")
                return True
            else:
                print(f"❌ Ошибка симуляции: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при симуляции: {e}")
            return False
    
    def check_notification_stats(self):
        """Проверка статистики уведомлений"""
        try:
            print("📊 Получение статистики уведомлений...")
            response = self.session.get(f"{API_BASE_URL}/api/notifications/stats")
            
            if response.status_code == 200:
                stats = response.json()
                print("✅ Статистика уведомлений:")
                print(f"   Всего отправлено: {stats.get('total_sent', 0)}")
                print(f"   Успешно доставлено: {stats.get('delivered', 0)}")
                print(f"   Ошибок доставки: {stats.get('failed', 0)}")
                print(f"   Активных токенов: {stats.get('active_tokens', 0)}")
                return True
            else:
                print(f"❌ Ошибка получения статистики: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при получении статистики: {e}")
            return False
    
    def test_notification_preferences(self):
        """Тестирование настроек уведомлений"""
        try:
            print("⚙️ Тестирование настроек уведомлений...")
            
            # Получаем текущие настройки
            response = self.session.get(f"{API_BASE_URL}/api/notifications/preferences")
            if response.status_code == 200:
                prefs = response.json()
                print(f"   Текущие настройки: {prefs}")
            
            # Обновляем настройки
            new_prefs = {
                "email_notifications": True,
                "push_notifications": True,
                "violation_alerts": True,
                "system_updates": False
            }
            
            response = self.session.post(f"{API_BASE_URL}/api/notifications/preferences", json=new_prefs)
            if response.status_code == 200:
                print("✅ Настройки уведомлений обновлены")
                return True
            else:
                print(f"❌ Ошибка обновления настроек: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при тестировании настроек: {e}")
            return False
    
    def run_full_test(self):
        """Запуск полного тестирования системы push уведомлений"""
        print("🚀 Начинаем полное тестирование системы push уведомлений")
        print("=" * 60)
        
        tests = [
            ("Авторизация", self.login),
            ("Сохранение push токена", self.save_push_token),
            ("Тестирование настроек", self.test_notification_preferences),
            ("Отправка тестового уведомления", self.send_test_notification),
            ("Симуляция обнаружения нарушения", self.simulate_violation_detection),
            ("Проверка статистики", self.check_notification_stats)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Тест: {test_name}")
            print("-" * 40)
            
            try:
                if test_func():
                    passed += 1
                    print(f"✅ {test_name} - ПРОЙДЕН")
                else:
                    print(f"❌ {test_name} - ПРОВАЛЕН")
            except Exception as e:
                print(f"❌ {test_name} - ОШИБКА: {e}")
            
            time.sleep(1)  # Небольшая пауза между тестами
        
        print("\n" + "=" * 60)
        print(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print(f"   Пройдено: {passed}/{total}")
        print(f"   Процент успеха: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print("⚠️  Некоторые тесты провалены. Проверьте логи выше.")
        
        return passed == total

def main():
    """Главная функция"""
    print("🔔 Тестирование системы Push уведомлений Geo Locator")
    print("=" * 60)
    
    tester = PushNotificationTester()
    success = tester.run_full_test()
    
    if success:
        print("\n✅ Система push уведомлений работает корректно!")
    else:
        print("\n❌ Обнаружены проблемы в системе push уведомлений.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
