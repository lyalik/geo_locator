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
    password = db.Column(db.String(255), nullable=False)
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
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    photo_id = db.Column(db.Integer, db.ForeignKey('photos.id'), nullable=True)
    task_type = db.Column(db.String(50), nullable=False)  # 'ocr', 'violation_detection', etc.
    status = db.Column(db.String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    result_data = db.Column(db.JSON)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='processing_tasks')
    photo = db.relationship('Photo', backref='processing_tasks')

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    violation_id = db.Column(db.Integer, db.ForeignKey('violations.id'), nullable=True)
    type = db.Column(db.String(50), nullable=False)  # 'email', 'sms', 'push'
    status = db.Column(db.String(20), default='pending')  # 'pending', 'sent', 'failed', 'read'
    subject = db.Column(db.String(255))
    message = db.Column(db.Text, nullable=False)
    recipient = db.Column(db.String(255), nullable=False)  # email address or phone number
    sent_at = db.Column(db.DateTime)
    read_at = db.Column(db.DateTime)
    meta_data = db.Column(db.JSON)  # additional data like email provider response
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    violation = db.relationship('Violation', backref='notifications')

class UserNotificationPreferences(db.Model):
    __tablename__ = 'user_notification_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    email_notifications = db.Column(db.Boolean, default=True)
    sms_notifications = db.Column(db.Boolean, default=False)
    push_notifications = db.Column(db.Boolean, default=True)
    violation_alerts = db.Column(db.Boolean, default=True)
    weekly_reports = db.Column(db.Boolean, default=True)
    immediate_alerts = db.Column(db.Boolean, default=True)
    notification_frequency = db.Column(db.String(20), default='immediate')  # 'immediate', 'daily', 'weekly'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='notification_preferences', uselist=False)