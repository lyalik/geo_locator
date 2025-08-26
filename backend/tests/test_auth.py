import unittest
from app import app, db
from models import User

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_register(self):
        response = self.client.post('/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['message'], 'User registered successfully')

    def test_login(self):
        # Register a user first
        self.client.post('/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword'
        })
        response = self.client.post('/login', json={
            'email': 'test@example.com',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Logged in successfully')

    def test_logout(self):
        # Register and login a user first
        self.client.post('/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword'
        })
        self.client.post('/login', json={
            'email': 'test@example.com',
            'password': 'testpassword'
        })
        response = self.client.post('/logout')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Logged out successfully')

if __name__ == '__main__':
    unittest.main()
