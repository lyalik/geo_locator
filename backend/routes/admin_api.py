from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Violation, Photo, Notification, UserNotificationPreferences, ProcessingTask
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from pathlib import Path
import os

bp = Blueprint('admin_api', __name__)

def admin_required(f):
    """Декоратор для проверки прав администратора"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Проверяем роль пользователя (если поле role существует)
        user_role = getattr(current_user, 'role', 'user')
        if user_role not in ['admin', 'moderator']:
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
            
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/users', methods=['GET'])
@login_required
@admin_required
def get_all_users():
    """Получение списка всех пользователей"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        users_query = User.query.order_by(desc(User.created_at))
        total = users_query.count()
        users = users_query.offset((page - 1) * per_page).limit(per_page).all()
        
        users_data = []
        for user in users:
            # Подсчитываем статистику пользователя
            photos_count = Photo.query.filter_by(user_id=user.id).count()
            violations_count = db.session.query(Violation).join(Photo).filter(Photo.user_id == user.id).count()
            
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': getattr(user, 'role', 'user'),
                'is_active': getattr(user, 'is_active', True),
                'created_at': user.created_at.isoformat() + 'Z' if user.created_at else None,
                'photos_count': photos_count,
                'violations_count': violations_count
            })
        
        return jsonify({
            'success': True,
            'users': users_data,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting users: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    """Обновление данных пользователя"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'role' in data:
            # Добавляем поле role если его нет
            if not hasattr(user, 'role'):
                # Можно добавить поле в модель или использовать JSON поле
                pass
            else:
                user.role = data['role']
        if 'is_active' in data:
            # Аналогично для is_active
            if not hasattr(user, 'is_active'):
                pass
            else:
                user.is_active = data['is_active']
        
        db.session.commit()
        current_app.logger.info(f"Admin {current_user.id} updated user {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': getattr(user, 'role', 'user'),
                'is_active': getattr(user, 'is_active', True)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error updating user {user_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """Удаление пользователя (только для суперадмина)"""
    try:
        current_app.logger.info(f"Delete user request for user_id: {user_id} by user: {current_user.id}")
        
        # Проверяем, что текущий пользователь - суперадмин
        if getattr(current_user, 'role', 'user') != 'admin':
            current_app.logger.warning(f"Non-admin user {current_user.id} tried to delete user {user_id}")
            return jsonify({
                'success': False,
                'error': 'Superadmin access required'
            }), 403
        
        user = User.query.get_or_404(user_id)
        
        # Нельзя удалить самого себя
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'error': 'Cannot delete yourself'
            }), 400
        
        # Удаляем связанные данные вручную для избежания ошибок
        try:
            # Удаляем уведомления пользователя
            Notification.query.filter_by(user_id=user_id).delete()
            
            # Удаляем предпочтения уведомлений
            UserNotificationPreferences.query.filter_by(user_id=user_id).delete()
            
            # Удаляем задачи обработки
            ProcessingTask.query.filter_by(user_id=user_id).delete()
            
            # Удаляем фотографии пользователя (это также удалит связанные нарушения)
            photos = Photo.query.filter_by(user_id=user_id).all()
            for photo in photos:
                # Удаляем связанные нарушения
                Violation.query.filter_by(photo_id=photo.id).delete()
                # Удаляем саму фотографию
                db.session.delete(photo)
            
            # Теперь удаляем пользователя
            db.session.delete(user)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting user {user_id}: {str(e)}")
            current_app.logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            raise e
        
        current_app.logger.info(f"Admin {current_user.id} deleted user {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error deleting user {user_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/violations', methods=['GET'])
@login_required
@admin_required
def get_all_violations():
    """Получение всех нарушений для админ-панели"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status_filter = request.args.get('status')
        category_filter = request.args.get('category')
        user_id_filter = request.args.get('user_id')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        violations_query = db.session.query(Violation).join(Photo).order_by(desc(Photo.created_at))
        
        if status_filter:
            violations_query = violations_query.filter(Violation.status == status_filter)
        
        if category_filter:
            violations_query = violations_query.filter(Violation.category == category_filter)
        
        if user_id_filter:
            violations_query = violations_query.filter(Photo.user_id == int(user_id_filter))
        
        if date_from:
            violations_query = violations_query.filter(Photo.created_at >= date_from)
        
        if date_to:
            violations_query = violations_query.filter(Photo.created_at <= date_to + ' 23:59:59')
        
        total = violations_query.count()
        violations = violations_query.offset((page - 1) * per_page).limit(per_page).all()
        
        violations_data = []
        for violation in violations:
            photo = violation.photo
            user = photo.user if photo else None
            
            violations_data.append({
                'violation_id': str(violation.id),
                'category': violation.category,
                'confidence': violation.confidence,
                'status': getattr(violation, 'status', 'pending'),
                'notes': getattr(violation, 'notes', ''),
                'source': getattr(violation, 'source', 'unknown'),
                'created_at': photo.created_at.isoformat() + 'Z' if photo else None,
                'user_id': str(photo.user_id) if photo else None,
                'username': user.username if user else 'Unknown',
                'image_path': f"http://192.168.1.67:5001/uploads/violations/{Path(photo.file_path).name}" if photo and photo.file_path else None,
                'location': {
                    'latitude': photo.lat if photo else None,
                    'longitude': photo.lon if photo else None,
                    'address': photo.address_data if photo else None
                }
            })
        
        return jsonify({
            'success': True,
            'violations': violations_data,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting violations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/violations/<int:violation_id>/moderate', methods=['PUT'])
@login_required
@admin_required
def moderate_violation(violation_id):
    """Модерация нарушения"""
    try:
        violation = Violation.query.get_or_404(violation_id)
        data = request.get_json()
        
        action = data.get('action')  # 'approve', 'reject', 'pending'
        notes = data.get('notes', '')
        
        if action == 'approve':
            # Если у модели нет поля status, используем заметки для отслеживания
            if hasattr(violation, 'status'):
                violation.status = 'approved'
            if hasattr(violation, 'notes'):
                violation.notes = f"Одобрено модератором: {notes}"
        elif action == 'reject':
            if hasattr(violation, 'status'):
                violation.status = 'rejected'
            if hasattr(violation, 'notes'):
                violation.notes = f"Отклонено модератором: {notes}"
        elif action == 'pending':
            if hasattr(violation, 'status'):
                violation.status = 'pending'
        
        db.session.commit()
        current_app.logger.info(f"Moderator {current_user.id} {action} violation {violation_id}")
        
        return jsonify({
            'success': True,
            'message': f'Violation {action}d successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error moderating violation {violation_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/violations/<int:violation_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_violation_admin(violation_id):
    """Удаление нарушения через админ панель"""
    try:
        violation = db.session.query(Violation).filter(Violation.id == violation_id).first()
        
        if not violation:
            return jsonify({
                'success': False,
                'error': 'Violation not found'
            }), 404
        
        # Проверяем, является ли это единственным нарушением для фото
        photo = violation.photo
        if photo and len(photo.violations) == 1:
            # Удаляем фото и файл, если это последнее нарушение
            if photo.file_path and os.path.exists(photo.file_path):
                os.remove(photo.file_path)
            db.session.delete(photo)
        
        db.session.delete(violation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Violation deleted successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error deleting violation {violation_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to delete violation: {str(e)}'
        }), 500

@bp.route('/analytics/detailed', methods=['GET'])
@login_required
@admin_required
def get_detailed_analytics():
    """Расширенная аналитика для админ-панели"""
    try:
        # Базовая статистика
        total_users = User.query.count()
        total_photos = Photo.query.count()
        total_violations = Violation.query.count()
        
        # Статистика по дням (последние 30 дней)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_stats = db.session.query(
            func.date(Photo.created_at).label('date'),
            func.count(Photo.id).label('photos'),
            func.count(Violation.id).label('violations')
        ).outerjoin(Violation, Photo.id == Violation.photo_id)\
         .filter(Photo.created_at >= thirty_days_ago)\
         .group_by(func.date(Photo.created_at))\
         .order_by(func.date(Photo.created_at)).all()
        
        # Статистика по категориям
        category_stats = db.session.query(
            Violation.category,
            func.count(Violation.id).label('count')
        ).group_by(Violation.category)\
         .order_by(desc(func.count(Violation.id))).all()
        
        # Статистика по пользователям (топ 10)
        user_stats = db.session.query(
            User.username,
            func.count(Photo.id).label('photos_count'),
            func.count(Violation.id).label('violations_count')
        ).outerjoin(Photo, User.id == Photo.user_id)\
         .outerjoin(Violation, Photo.id == Violation.photo_id)\
         .group_by(User.id, User.username)\
         .order_by(desc(func.count(Photo.id)))\
         .limit(10).all()
        
        # Статистика по статусам (если поле существует)
        status_stats = []
        try:
            status_stats = db.session.query(
                Violation.status,
                func.count(Violation.id).label('count')
            ).group_by(Violation.status).all()
        except:
            # Поле status может не существовать в старых записях
            pass
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total_users': total_users,
                    'total_photos': total_photos,
                    'total_violations': total_violations,
                    'avg_violations_per_photo': round(total_violations / max(total_photos, 1), 2)
                },
                'daily_stats': [
                    {
                        'date': stat.date.isoformat(),
                        'photos': stat.photos,
                        'violations': stat.violations or 0
                    } for stat in daily_stats
                ],
                'category_stats': [
                    {
                        'category': stat.category,
                        'count': stat.count
                    } for stat in category_stats
                ],
                'user_stats': [
                    {
                        'username': stat.username,
                        'photos_count': stat.photos_count,
                        'violations_count': stat.violations_count or 0
                    } for stat in user_stats
                ],
                'status_stats': [
                    {
                        'status': stat.status or 'unknown',
                        'count': stat.count
                    } for stat in status_stats
                ]
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting detailed analytics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/export/violations', methods=['GET'])
@login_required
@admin_required
def export_violations():
    """Экспорт нарушений в CSV"""
    try:
        import csv
        import io
        
        violations = db.session.query(Violation).join(Photo).join(User).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow([
            'ID', 'Категория', 'Уверенность', 'Статус', 'Источник',
            'Пользователь', 'Email', 'Дата создания', 'Координаты',
            'Адрес', 'Заметки'
        ])
        
        # Данные
        for violation in violations:
            photo = violation.photo
            user = photo.user if photo else None
            
            writer.writerow([
                violation.id,
                violation.category,
                violation.confidence,
                getattr(violation, 'status', 'unknown'),
                getattr(violation, 'source', 'unknown'),
                user.username if user else 'Unknown',
                user.email if user else 'Unknown',
                photo.created_at.isoformat() if photo else '',
                f"{photo.lat},{photo.lon}" if photo and photo.lat and photo.lon else '',
                str(photo.address_data) if photo and photo.address_data else '',
                getattr(violation, 'notes', '')
            ])
        
        output.seek(0)
        
        return jsonify({
            'success': True,
            'data': output.getvalue(),
            'filename': f'violations_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error exporting violations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
