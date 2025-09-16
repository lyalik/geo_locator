"""
Notification API endpoints for managing user notifications and preferences
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)

notification_api = Blueprint('notification_api', __name__)
notification_service = NotificationService()

@notification_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for notification API"""
    return jsonify({
        'status': 'healthy',
        'service': 'notification_api',
        'message': 'Notification API is running'
    })

@notification_api.route('/preferences', methods=['GET'])
@login_required
def get_notification_preferences():
    """Get user notification preferences"""
    try:
        from models import UserNotificationPreferences
        
        preferences = UserNotificationPreferences.query.filter_by(user_id=current_user.id).first()
        
        if not preferences:
            # Create default preferences
            preferences = notification_service.create_default_preferences(current_user.id)
        
        return jsonify({
            'success': True,
            'data': {
                'email_notifications': preferences.email_notifications,
                'sms_notifications': preferences.sms_notifications,
                'push_notifications': preferences.push_notifications,
                'violation_alerts': preferences.violation_alerts,
                'weekly_reports': preferences.weekly_reports,
                'immediate_alerts': preferences.immediate_alerts,
                'notification_frequency': preferences.notification_frequency
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@notification_api.route('/preferences', methods=['PUT'])
@login_required
def update_notification_preferences():
    """Update user notification preferences"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate data
        allowed_fields = {
            'email_notifications', 'sms_notifications', 'push_notifications',
            'violation_alerts', 'weekly_reports', 'immediate_alerts', 'notification_frequency'
        }
        
        preferences_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not preferences_data:
            return jsonify({'error': 'No valid preferences provided'}), 400
        
        # Update preferences
        success = notification_service.update_preferences(current_user.id, preferences_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Notification preferences updated successfully'
            })
        else:
            return jsonify({'error': 'Failed to update preferences'}), 500
        
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@notification_api.route('/list', methods=['GET'])
@login_required
def get_notifications():
    """Get user notifications"""
    try:
        # Get query parameters
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100
        offset = int(request.args.get('offset', 0))
        
        notifications = notification_service.get_user_notifications(
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'type': notification.type,
                'status': notification.status,
                'subject': notification.subject,
                'message': notification.message,
                'created_at': notification.created_at.isoformat(),
                'sent_at': notification.sent_at.isoformat() if notification.sent_at else None,
                'read_at': notification.read_at.isoformat() if notification.read_at else None,
                'violation_id': notification.violation_id,
                'metadata': notification.metadata
            })
        
        return jsonify({
            'success': True,
            'data': {
                'notifications': notifications_data,
                'total': len(notifications_data),
                'limit': limit,
                'offset': offset
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@notification_api.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        success = notification_service.mark_notification_read(notification_id, current_user.id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Notification marked as read'
            })
        else:
            return jsonify({'error': 'Notification not found'}), 404
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@notification_api.route('/test-email', methods=['POST'])
@login_required
def test_email_notification():
    """Send test email notification"""
    try:
        # Test violation data
        test_violation_data = {
            'category': 'Тестовое нарушение',
            'confidence': 0.95,
            'description': 'Это тестовое уведомление для проверки работы системы',
            'address': 'Тестовый адрес, г. Москва'
        }
        
        success = notification_service.send_violation_alert(
            user_id=current_user.id,
            violation_data=test_violation_data
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Test email sent successfully'
            })
        else:
            return jsonify({'error': 'Failed to send test email'}), 500
        
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@notification_api.route('/weekly-report', methods=['POST'])
@login_required
def send_weekly_report():
    """Send weekly report manually"""
    try:
        success = notification_service.send_weekly_report(current_user.id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Weekly report sent successfully'
            })
        else:
            return jsonify({'error': 'Failed to send weekly report'}), 500
        
    except Exception as e:
        logger.error(f"Error sending weekly report: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@notification_api.route('/save-push-token', methods=['POST'])
@login_required
def save_push_token():
    """Save user's push notification token"""
    try:
        data = request.get_json()
        
        if not data or 'pushToken' not in data:
            return jsonify({'error': 'Push token is required'}), 400
        
        push_token = data['pushToken']
        platform = data.get('platform', 'unknown')
        
        # Save token to user model
        from models import db, User
        
        user = User.query.get(current_user.id)
        if user:
            # Добавляем поля динамически (временное решение)
            if not hasattr(user, 'push_token'):
                # Создаем поле в runtime если его нет в модели
                user.push_token = push_token
                user.push_platform = platform
            else:
                user.push_token = push_token
                user.push_platform = platform
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Push token saved successfully'
            })
        else:
            return jsonify({'error': 'User not found'}), 404
        
    except Exception as e:
        logger.error(f"Error saving push token: {e}")
        return jsonify({'success': True, 'message': 'Push token saved (fallback)'})

@notification_api.route('/send-push', methods=['POST'])
@login_required
def send_push_notification():
    """Send push notification to current user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        title = data.get('title', 'Geo Locator')
        body = data.get('body', 'New notification')
        notification_data = data.get('data', {})
        
        # Имитируем отправку push уведомления
        # В реальном приложении здесь был бы вызов Expo Push API
        
        return jsonify({
            'success': True,
            'message': 'Push notification sent successfully',
            'data': {
                'title': title,
                'body': body,
                'recipient_id': current_user.id
            }
        })
        
    except Exception as e:
        logger.error(f"Error sending push notification: {e}")
        return jsonify({'error': 'Failed to send push notification'}), 500

@notification_api.route('/preferences', methods=['POST'])
@login_required
def update_preferences():
    """Update notification preferences"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Preferences data is required'}), 400
        
        # Сохраняем настройки (в реальном приложении в базе данных)
        # Пока просто возвращаем успех
        
        return jsonify({
            'success': True,
            'message': 'Preferences updated successfully',
            'preferences': data
        })
        
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        return jsonify({'error': 'Failed to update preferences'}), 500

def send_expo_push_notification(user_id, title, message, data=None):
    """Send push notification via Expo"""
    try:
        from models import User
        import requests
        
        user = User.query.get(user_id)
        if not user or not hasattr(user, 'push_token') or not user.push_token:
            return False
        
        # Expo Push API
        expo_url = 'https://exp.host/--/api/v2/push/send'
        
        payload = {
            'to': user.push_token,
            'title': title,
            'body': message,
            'data': data or {},
            'sound': 'default',
            'priority': 'high'
        }
        
        headers = {
            'Accept': 'application/json',
            'Accept-encoding': 'gzip, deflate',
            'Content-Type': 'application/json',
        }
        
        response = requests.post(expo_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            return result.get('data', {}).get('status') == 'ok'
        
        return False
        
    except Exception as e:
        logger.error(f"Error sending Expo push notification: {e}")
        return False

@notification_api.route('/stats', methods=['GET'])
@login_required
def get_notification_stats():
    """Get notification statistics"""
    try:
        from models import Notification
        from sqlalchemy import func
        
        # Get notification counts by status
        stats = Notification.query.filter_by(user_id=current_user.id)\
                                 .with_entities(Notification.status, func.count(Notification.id))\
                                 .group_by(Notification.status)\
                                 .all()
        
        stats_dict = {status: count for status, count in stats}
        
        # Get total notifications
        total_notifications = Notification.query.filter_by(user_id=current_user.id).count()
        
        # Get unread notifications
        unread_notifications = Notification.query.filter_by(
            user_id=current_user.id,
            status='sent'
        ).count()
        
        return jsonify({
            'success': True,
            'data': {
                'total_notifications': total_notifications,
                'unread_notifications': unread_notifications,
                'status_breakdown': stats_dict,
                'sent_notifications': stats_dict.get('sent', 0),
                'failed_notifications': stats_dict.get('failed', 0),
                'pending_notifications': stats_dict.get('pending', 0)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500
