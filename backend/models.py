from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# This will be initialized in app.py
db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Photo(db.Model):
    __tablename__ = 'photos'
    
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    has_gps = db.Column(db.Boolean, default=False)
    location_method = db.Column(db.String(50))  # 'gps', 'hint_matching', 'manual'
    location_hint = db.Column(db.String(500))
    address_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('photos', lazy=True))
    violations = db.relationship('Violation', backref='photo', lazy=True, cascade='all, delete-orphan')

class Violation(db.Model):
    __tablename__ = 'violations'
    
    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey('photos.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer)
    confidence = db.Column(db.Float, nullable=False)
    bbox_data = db.Column(db.JSON)  # Bounding box coordinates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProcessingTask(db.Model):
    __tablename__ = 'processing_tasks'
    
    id = db.Column(db.String(100), primary_key=True)  # Celery task_id
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='PENDING')  # PENDING, STARTED, SUCCESS, FAILURE
    task_type = db.Column(db.String(50))  # 'violation_detection', 'location_matching'
    result_data = db.Column(db.JSON)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('tasks', lazy=True))