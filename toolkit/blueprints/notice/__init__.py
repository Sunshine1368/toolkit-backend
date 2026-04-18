from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import current_user, login_required
from sqlalchemy import desc
from toolkit import db
from toolkit.models.notification import Notification

bp = Blueprint('notice', __name__)


@bp.route('/')
@login_required
def index():
    """Notifications page."""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(desc(Notification.created_at))\
        .paginate(page=page, per_page=per_page, error_out=False)

    return render_template('notice/index.html', notifications=notifications)


@bp.route('/api/notifications', methods=['GET'])
@login_required
def api_notifications():
    """Get notifications API."""
    limit = request.args.get('limit', 20, type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'

    query = Notification.query.filter_by(user_id=current_user.id)

    if unread_only:
        query = query.filter_by(is_read=False)

    notifications = query.order_by(desc(Notification.created_at))\
        .limit(limit)\
        .all()

    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    })


@bp.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """Mark notification as read."""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()

    notification.mark_as_read()
    db.session.commit()

    return jsonify({'success': True})


@bp.route('/api/notifications/read-all', methods=['POST'])
@login_required
def mark_all_as_read():
    """Mark all notifications as read."""
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).all()

    for notification in notifications:
        notification.mark_as_read()

    db.session.commit()

    return jsonify({
        'success': True,
        'marked_count': len(notifications)
    })


@bp.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    """Delete notification."""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(notification)
    db.session.commit()

    return jsonify({'success': True})


@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Notification settings."""
    if request.method == 'POST':
        # Update notification preferences
        # This would typically update user settings
        flash('Notification settings updated', 'success')
        return redirect(url_for('notice.settings'))

    return render_template('notice/settings.html')