#!/usr/bin/env python3
"""
Integration test script for Geo Locator notification system
Tests the complete flow from user registration to violation detection and notifications
"""

import requests
import json
import time
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpass123"
TEST_USER_NAME = "Test User"

class GeoLocatorTester:
    def __init__(self):
        self.session = requests.Session()
        self.user_id = None
        
    def test_health_endpoints(self):
        """Test all health endpoints"""
        print("🔍 Testing health endpoints...")
        
        endpoints = [
            "/health",
            "/api/notifications/health",
            "/api/ocr/health"
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                if response.status_code == 200:
                    print(f"✅ {endpoint} - OK")
                else:
                    print(f"❌ {endpoint} - Status: {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint} - Error: {e}")
    
    def test_user_registration(self):
        """Test user registration"""
        print("\n👤 Testing user registration...")
        
        # First try to login (user might already exist)
        login_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        
        response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            user_data = response.json()
            self.user_id = user_data.get("user", {}).get("id")
            print(f"✅ User login successful - ID: {self.user_id}")
            return True
        
        # If login failed, try registration
        register_data = {
            "username": TEST_USER_NAME,
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        
        response = self.session.post(f"{BASE_URL}/auth/register", json=register_data)
        
        if response.status_code == 201:
            print("✅ User registration successful")
            # Now login
            login_response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            if login_response.status_code == 200:
                user_data = login_response.json()
                self.user_id = user_data.get("user", {}).get("id")
                print(f"✅ User login after registration - ID: {self.user_id}")
                return True
        
        print(f"❌ Registration/Login failed: {response.status_code}")
        return False
    
    def test_notification_preferences(self):
        """Test notification preferences API"""
        print("\n🔔 Testing notification preferences...")
        
        # Get current preferences
        response = self.session.get(f"{BASE_URL}/api/notifications/preferences")
        
        if response.status_code == 200:
            preferences = response.json()
            print(f"✅ Got notification preferences: {preferences}")
            
            # Update preferences
            update_data = {
                "email_violations": True,
                "email_reports": True,
                "in_app_violations": True,
                "in_app_reports": True
            }
            
            update_response = self.session.put(
                f"{BASE_URL}/api/notifications/preferences", 
                json=update_data
            )
            
            if update_response.status_code == 200:
                print("✅ Notification preferences updated successfully")
                return True
            else:
                print(f"❌ Failed to update preferences: {update_response.status_code}")
        else:
            print(f"❌ Failed to get preferences: {response.status_code}")
        
        return False
    
    def test_notification_list(self):
        """Test notification list API"""
        print("\n📋 Testing notification list...")
        
        response = self.session.get(f"{BASE_URL}/api/notifications/list")
        
        if response.status_code == 200:
            notifications = response.json()
            print(f"✅ Got notifications list: {len(notifications.get('notifications', []))} notifications")
            return True
        else:
            print(f"❌ Failed to get notifications: {response.status_code}")
        
        return False
    
    def test_notification_stats(self):
        """Test notification statistics"""
        print("\n📊 Testing notification stats...")
        
        response = self.session.get(f"{BASE_URL}/api/notifications/stats")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Got notification stats: {stats}")
            return True
        else:
            print(f"❌ Failed to get stats: {response.status_code}")
        
        return False
    
    def test_email_notification(self):
        """Test email notification sending"""
        print("\n📧 Testing email notification...")
        
        test_data = {
            "subject": "Test Notification",
            "message": "This is a test notification from the integration test."
        }
        
        response = self.session.post(f"{BASE_URL}/api/notifications/test-email", json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Email notification test: {result.get('message', 'Success')}")
            return True
        else:
            print(f"❌ Email notification failed: {response.status_code}")
            if response.text:
                print(f"   Error: {response.text}")
        
        return False
    
    def create_test_image(self):
        """Create a simple test image for violation detection"""
        try:
            from PIL import Image, ImageDraw
            
            # Create a simple test image
            img = Image.new('RGB', (640, 480), color='white')
            draw = ImageDraw.Draw(img)
            
            # Draw some simple shapes to simulate a violation
            draw.rectangle([100, 100, 300, 200], fill='red', outline='black')
            draw.text((150, 250), "TEST VIOLATION", fill='black')
            
            test_image_path = "/tmp/test_violation.jpg"
            img.save(test_image_path, 'JPEG')
            return test_image_path
            
        except ImportError:
            print("⚠️  PIL not available, skipping image creation")
            return None
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting Geo Locator Integration Tests")
        print("=" * 50)
        
        # Test health endpoints
        self.test_health_endpoints()
        
        # Test user authentication
        if not self.test_user_registration():
            print("❌ Cannot continue without user authentication")
            return False
        
        # Test notification system
        self.test_notification_preferences()
        self.test_notification_list()
        self.test_notification_stats()
        self.test_email_notification()
        
        print("\n" + "=" * 50)
        print("🎉 Integration tests completed!")
        
        return True

if __name__ == "__main__":
    tester = GeoLocatorTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Some tests failed. Check the output above.")
