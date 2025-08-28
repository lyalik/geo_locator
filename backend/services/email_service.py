"""
Email notification service for sending violation alerts and reports
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
from jinja2 import Template

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending email notifications"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
        self.from_name = os.getenv('FROM_NAME', 'Geo Locator')
        
    def send_email(self, 
                   to_email: str, 
                   subject: str, 
                   html_content: str, 
                   text_content: Optional[str] = None,
                   attachments: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        Send an email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (optional)
            attachments: List of attachments with 'filename' and 'content' keys
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_violation_alert(self, 
                           user_email: str, 
                           user_name: str,
                           violation_data: Dict[str, Any]) -> bool:
        """
        Send violation alert email
        
        Args:
            user_email: User's email address
            user_name: User's name
            violation_data: Violation details
            
        Returns:
            bool: True if email sent successfully
        """
        subject = f"🚨 Нарушение обнаружено - {violation_data.get('category', 'Неизвестно')}"
        
        # HTML template for violation alert
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 30px; }
                .alert-badge { background-color: #ff4444; color: white; padding: 10px 20px; border-radius: 20px; display: inline-block; font-weight: bold; }
                .violation-details { background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .detail-row { margin: 10px 0; }
                .label { font-weight: bold; color: #333; }
                .value { color: #666; }
                .footer { text-align: center; margin-top: 30px; color: #888; font-size: 12px; }
                .button { background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 Обнаружено нарушение</h1>
                    <div class="alert-badge">{{ violation_category }}</div>
                </div>
                
                <p>Здравствуйте, {{ user_name }}!</p>
                <p>Система Geo Locator обнаружила нарушение в загруженном вами изображении.</p>
                
                <div class="violation-details">
                    <h3>Детали нарушения:</h3>
                    <div class="detail-row">
                        <span class="label">Категория:</span>
                        <span class="value">{{ violation_category }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Уровень достоверности:</span>
                        <span class="value">{{ confidence }}%</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Дата обнаружения:</span>
                        <span class="value">{{ detection_date }}</span>
                    </div>
                    {% if address %}
                    <div class="detail-row">
                        <span class="label">Адрес:</span>
                        <span class="value">{{ address }}</span>
                    </div>
                    {% endif %}
                    {% if description %}
                    <div class="detail-row">
                        <span class="label">Описание:</span>
                        <span class="value">{{ description }}</span>
                    </div>
                    {% endif %}
                </div>
                
                <p>Рекомендуем принять соответствующие меры для устранения нарушения.</p>
                
                <a href="{{ dashboard_url }}" class="button">Перейти в Dashboard</a>
                
                <div class="footer">
                    <p>Это автоматическое уведомление от системы Geo Locator.</p>
                    <p>Если у вас есть вопросы, обратитесь в службу поддержки.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Render template
        template = Template(html_template)
        html_content = template.render(
            user_name=user_name,
            violation_category=violation_data.get('category', 'Неизвестно'),
            confidence=round(violation_data.get('confidence', 0) * 100, 1),
            detection_date=datetime.now().strftime('%d.%m.%Y %H:%M'),
            address=violation_data.get('address', ''),
            description=violation_data.get('description', ''),
            dashboard_url=os.getenv('FRONTEND_URL', 'http://localhost:3000')
        )
        
        # Plain text version
        text_content = f"""
        Обнаружено нарушение - {violation_data.get('category', 'Неизвестно')}
        
        Здравствуйте, {user_name}!
        
        Система Geo Locator обнаружила нарушение в загруженном вами изображении.
        
        Детали нарушения:
        - Категория: {violation_data.get('category', 'Неизвестно')}
        - Уровень достоверности: {round(violation_data.get('confidence', 0) * 100, 1)}%
        - Дата обнаружения: {datetime.now().strftime('%d.%m.%Y %H:%M')}
        
        Рекомендуем принять соответствующие меры для устранения нарушения.
        
        Перейти в Dashboard: {os.getenv('FRONTEND_URL', 'http://localhost:3000')}
        """
        
        return self.send_email(user_email, subject, html_content, text_content)
    
    def send_weekly_report(self, 
                          user_email: str, 
                          user_name: str,
                          report_data: Dict[str, Any]) -> bool:
        """
        Send weekly violation report
        
        Args:
            user_email: User's email address
            user_name: User's name
            report_data: Report data with violations summary
            
        Returns:
            bool: True if email sent successfully
        """
        subject = f"📊 Еженедельный отчет по нарушениям - {datetime.now().strftime('%d.%m.%Y')}"
        
        # HTML template for weekly report
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 30px; }
                .stats { display: flex; justify-content: space-around; margin: 20px 0; }
                .stat-item { text-align: center; padding: 15px; background-color: #f8f9fa; border-radius: 8px; }
                .stat-number { font-size: 24px; font-weight: bold; color: #007bff; }
                .stat-label { color: #666; font-size: 12px; }
                .violations-list { margin: 20px 0; }
                .violation-item { padding: 10px; border-left: 4px solid #ff4444; margin: 10px 0; background-color: #fff5f5; }
                .footer { text-align: center; margin-top: 30px; color: #888; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Еженедельный отчет</h1>
                    <p>{{ week_period }}</p>
                </div>
                
                <p>Здравствуйте, {{ user_name }}!</p>
                <p>Ваш еженедельный отчет по обнаруженным нарушениям готов.</p>
                
                <div class="stats">
                    <div class="stat-item">
                        <div class="stat-number">{{ total_violations }}</div>
                        <div class="stat-label">Всего нарушений</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{{ new_violations }}</div>
                        <div class="stat-label">Новых за неделю</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{{ resolved_violations }}</div>
                        <div class="stat-label">Устранено</div>
                    </div>
                </div>
                
                {% if recent_violations %}
                <div class="violations-list">
                    <h3>Последние нарушения:</h3>
                    {% for violation in recent_violations %}
                    <div class="violation-item">
                        <strong>{{ violation.category }}</strong> - {{ violation.date }}
                        <br><small>{{ violation.address }}</small>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
                
                <div class="footer">
                    <p>Это автоматический отчет от системы Geo Locator.</p>
                    <p>Для получения подробной информации перейдите в Dashboard.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Render template
        template = Template(html_template)
        html_content = template.render(
            user_name=user_name,
            week_period=report_data.get('week_period', ''),
            total_violations=report_data.get('total_violations', 0),
            new_violations=report_data.get('new_violations', 0),
            resolved_violations=report_data.get('resolved_violations', 0),
            recent_violations=report_data.get('recent_violations', [])
        )
        
        return self.send_email(user_email, subject, html_content)
    
    def test_connection(self) -> bool:
        """
        Test SMTP connection
        
        Returns:
            bool: True if connection successful
        """
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
            logger.info("SMTP connection test successful")
            return True
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False
