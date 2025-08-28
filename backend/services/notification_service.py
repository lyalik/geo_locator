"""
Notification service for managing violation alerts and user notifications
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import and_
from models import db, Notification, UserNotificationPreferences, User, Violation
from .email_service import EmailService

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for managing notifications and alerts"""
    
    def __init__(self):
        self.email_service = EmailService()
    
    def create_notification(self, 
                          user_id: int,
                          notification_type: str,
                          message: str,
                          recipient: str,
                          subject: Optional[str] = None,
                          violation_id: Optional[int] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> Notification:
        """
        Create a new notification record
        
        Args:
            user_id: User ID
            notification_type: Type of notification ('email', 'sms', 'push')
            message: Notification message
            recipient: Recipient address (email/phone)
            subject: Notification subject (for emails)
            violation_id: Related violation ID (optional)
            metadata: Additional metadata
            
        Returns:
            Notification: Created notification object
        """
        notification = Notification(
            user_id=user_id,
            violation_id=violation_id,
            type=notification_type,
            subject=subject,
            message=message,
            recipient=recipient,
            meta_data=metadata or {}
        )
        
        db.session.add(notification)
        db.session.commit()
        
        logger.info(f"Created notification {notification.id} for user {user_id}")
        return notification
    
    def send_violation_alert(self, 
                           user_id: int, 
                           violation_data: Dict[str, Any]) -> bool:
        """
        Send violation alert to user based on their preferences
        
        Args:
            user_id: User ID
            violation_data: Violation details
            
        Returns:
            bool: True if notification sent successfully
        """
        try:
            # Get user and preferences
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            
            preferences = UserNotificationPreferences.query.filter_by(user_id=user_id).first()
            if not preferences:
                # Create default preferences
                preferences = self.create_default_preferences(user_id)
            
            # Check if user wants violation alerts
            if not preferences.violation_alerts:
                logger.info(f"User {user_id} has violation alerts disabled")
                return True
            
            success = True
            
            # Send email notification
            if preferences.email_notifications:
                message = f"Обнаружено нарушение: {violation_data.get('category', 'Неизвестно')}"
                notification = self.create_notification(
                    user_id=user.id,
                    notification_type='email',
                    message=message,
                    recipient=user.email,
                    subject=f"🚨 Нарушение обнаружено - {violation_data.get('category', 'Неизвестно')}",
                    violation_id=violation_data.get('violation_id'),
                    metadata={'violation_data': violation_data}
                )
                
                email_sent = self.email_service.send_violation_alert(
                    user_email=user.email,
                    user_name=user.username,
                    violation_data=violation_data
                )
                
                if email_sent:
                    notification.status = 'sent'
                    notification.sent_at = datetime.utcnow()
                else:
                    notification.status = 'failed'
                    success = False
                
                db.session.commit()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send violation alert to user {user_id}: {e}")
            return False
    
    def send_weekly_report(self, user_id: int) -> bool:
        """
        Send weekly violation report to user
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if report sent successfully
        """
        try:
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            
            preferences = UserNotificationPreferences.query.filter_by(user_id=user_id).first()
            if not preferences or not preferences.weekly_reports:
                logger.info(f"User {user_id} has weekly reports disabled")
                return True
            
            # Get violations from last week
            week_ago = datetime.utcnow() - timedelta(days=7)
            violations = Violation.query.filter(
                and_(
                    Violation.user_id == user_id,
                    Violation.created_at >= week_ago
                )
            ).all()
            
            # Prepare report data
            report_data = {
                'week_period': f"{week_ago.strftime('%d.%m.%Y')} - {datetime.utcnow().strftime('%d.%m.%Y')}",
                'total_violations': len(violations),
                'new_violations': len(violations),
                'resolved_violations': 0,  # TODO: Add resolution tracking
                'recent_violations': [
                    {
                        'category': v.category,
                        'date': v.created_at.strftime('%d.%m.%Y'),
                        'address': 'Адрес не указан'  # TODO: Add address from photo metadata
                    }
                    for v in violations[:5]  # Show last 5
                ]
            }
            
            # Create notification
            notification = self.create_notification(
                user_id=user.id,
                notification_type='email',
                message=f"Еженедельный отчет: {report_data['new_violations']} новых нарушений",
                recipient=user.email,
                subject=f"📊 Еженедельный отчет по нарушениям - {datetime.utcnow().strftime('%d.%m.%Y')}",
                metadata={'report_data': report_data}
            )
            
            # Send email
            email_sent = self.email_service.send_weekly_report(
                user_email=user.email,
                user_name=user.username,
                report_data=report_data
            )
            
            if email_sent:
                notification.status = 'sent'
                notification.sent_at = datetime.utcnow()
            else:
                notification.status = 'failed'
            
            db.session.commit()
            return email_sent
            
        except Exception as e:
            logger.error(f"Failed to send weekly report to user {user_id}: {e}")
            return False
    
    def create_default_preferences(self, user_id: int) -> UserNotificationPreferences:
        """
        Create default notification preferences for user
        
        Args:
            user_id: User ID
            
        Returns:
            UserNotificationPreferences: Created preferences object
        """
        preferences = UserNotificationPreferences(
            user_id=user_id,
            email_notifications=True,
            sms_notifications=False,
            push_notifications=True,
            violation_alerts=True,
            weekly_reports=True,
            immediate_alerts=True,
            notification_frequency='immediate'
        )
        
        db.session.add(preferences)
        db.session.commit()
        
        logger.info(f"Created default notification preferences for user {user_id}")
        return preferences
    
    def update_preferences(self, 
                         user_id: int, 
                         preferences_data: Dict[str, Any]) -> bool:
        """
        Update user notification preferences
        
        Args:
            user_id: User ID
            preferences_data: New preferences data
            
        Returns:
            bool: True if updated successfully
        """
        try:
            preferences = UserNotificationPreferences.query.filter_by(user_id=user_id).first()
            if not preferences:
                preferences = self.create_default_preferences(user_id)
            
            # Update preferences
            for key, value in preferences_data.items():
                if hasattr(preferences, key):
                    setattr(preferences, key, value)
            
            preferences.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Updated notification preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update preferences for user {user_id}: {e}")
            return False
    
    def get_user_notifications(self, 
                             user_id: int, 
                             limit: int = 50,
                             offset: int = 0) -> List[Notification]:
        """
        Get user notifications
        
        Args:
            user_id: User ID
            limit: Maximum number of notifications to return
            offset: Offset for pagination
            
        Returns:
            List[Notification]: User notifications
        """
        return Notification.query.filter_by(user_id=user_id)\
                                .order_by(Notification.created_at.desc())\
                                .limit(limit)\
                                .offset(offset)\
                                .all()
    
    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """
        Mark notification as read
        
        Args:
            notification_id: Notification ID
            user_id: User ID (for security)
            
        Returns:
            bool: True if marked successfully
        """
        try:
            notification = Notification.query.filter_by(
                id=notification_id, 
                user_id=user_id
            ).first()
            
            if not notification:
                logger.error(f"Notification {notification_id} not found for user {user_id}")
                return False
            
            notification.status = 'read'
            notification.read_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Marked notification {notification_id} as read")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark notification {notification_id} as read: {e}")
            return False
    
    def process_pending_notifications(self) -> int:
        """
        Process all pending notifications (for background tasks)
        
        Returns:
            int: Number of notifications processed
        """
        try:
            pending_notifications = Notification.query.filter_by(status='pending').all()
            processed_count = 0
            
            for notification in pending_notifications:
                if notification.type == 'email':
                    # Retry sending email
                    user = User.query.get(notification.user_id)
                    if user and notification.violation_id:
                        violation = Violation.query.get(notification.violation_id)
                        if violation:
                            violation_data = {
                                'category': violation.category,
                                'confidence': violation.confidence,
                                'violation_id': violation.id
                            }
                            
                            email_sent = self.email_service.send_violation_alert(
                                user_email=user.email,
                                user_name=user.username,
                                violation_data=violation_data
                            )
                            
                            if email_sent:
                                notification.status = 'sent'
                                notification.sent_at = datetime.utcnow()
                                processed_count += 1
                            else:
                                notification.status = 'failed'
            
            db.session.commit()
            logger.info(f"Processed {processed_count} pending notifications")
            return processed_count
            
        except Exception as e:
            logger.error(f"Failed to process pending notifications: {e}")
            return 0
