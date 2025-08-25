from datetime import datetime
from . import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    search_requests = db.relationship('SearchRequest', backref='user', lazy=True)

class SearchRequest(db.Model):
    __tablename__ = 'search_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    search_type = db.Column(db.String(50), nullable=False)  # 'text', 'image', 'video', 'panorama'
    query = db.Column(db.Text, nullable=True)  # For text search
    file_path = db.Column(db.String(255), nullable=True)  # For media uploads
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Results
    yandex_result = db.Column(db.JSON, nullable=True)
    dgis_result = db.Column(db.JSON, nullable=True)
    sentinel_result = db.Column(db.JSON, nullable=True)
    gemini_analysis = db.Column(db.Text, nullable=True)
    
    # Location data
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    address = db.Column(db.String(255), nullable=True)
    
    # Relationships
    comparisons = db.relationship('Comparison', backref='search_request', lazy=True)

class Comparison(db.Model):
    __tablename__ = 'comparisons'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('search_requests.id'), nullable=False)
    source = db.Column(db.String(50), nullable=False)  # 'yandex', '2gis', 'sentinel', 'composite'
    confidence = db.Column(db.Float, nullable=True)
    result_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Location data
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    address = db.Column(db.String(255), nullable=True)
