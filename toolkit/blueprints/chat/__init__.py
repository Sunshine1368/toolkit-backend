from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import current_user, login_required
from flask_socketio import emit, join_room, leave_room
from sqlalchemy import desc
import datetime
from toolkit import db, socketio
from toolkit.models.message import Message
from toolkit.models.user import User
from toolkit.models.contact import Contact

bp = Blueprint('chat', __name__)


@bp.route('/')
@login_required
def index():
    """Chat main page."""
    return render_template('chat/index.html')


@bp.route('/api/conversations', methods=['GET'])
@login_required
def api_conversations():
    """Get conversations list."""
    # Get users with recent messages
    subquery = db.session.query(
        Message.recipient_id,
        db.func.max(Message.created_at).label('last_message_time')
    ).filter(Message.sender_id == current_user.id)\
     .group_by(Message.recipient_id)\
     .subquery()

    conversations = db.session.query(User, subquery.c.last_message_time)\
        .join(subquery, User.id == subquery.c.recipient_id)\
        .order_by(desc(subquery.c.last_message_time))\
        .limit(50)\
        .all()

    # Also include contacts
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    contact_ids = {c.contact_id for c in contacts}

    # Get contact users not already in conversations
    for contact in contacts:
        if contact.contact_id not in {c[0].id for c in conversations}:
            contact_user = User.query.get(contact.contact_id)
            if contact_user:
                conversations.append((contact_user, None))

    result = []
    for user, last_message_time in conversations:
        # Get unread count
        unread_count = Message.query.filter_by(
            sender_id=user.id,
            recipient_id=current_user.id,
            is_read=False
        ).count()

        # Get last message
        last_message = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.recipient_id == user.id)) |
            ((Message.sender_id == user.id) & (Message.recipient_id == current_user.id))
        ).order_by(desc(Message.created_at)).first()

        result.append({
            'user': user.to_dict(),
            'last_message_time': last_message_time.isoformat() if last_message_time else None,
            'last_message': last_message.to_dict() if last_message else None,
            'unread_count': unread_count
        })

    return jsonify({'conversations': result})


@bp.route('/api/conversations/<int:user_id>/messages', methods=['GET'])
@login_required
def api_messages(user_id):
    """Get messages with a specific user."""
    page = request.args.get('page', 1, type=int)
    per_page = 50

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.recipient_id == current_user.id))
    ).order_by(desc(Message.created_at))\
     .paginate(page=page, per_page=per_page, error_out=False)

    # Mark messages as read
    unread_messages = Message.query.filter_by(
        sender_id=user_id,
        recipient_id=current_user.id,
        is_read=False
    ).all()

    for message in unread_messages:
        message.mark_as_read()

    if unread_messages:
        db.session.commit()

    return jsonify({
        'messages': [m.to_dict() for m in messages.items][::-1],  # Reverse to get chronological order
        'has_next': messages.has_next,
        'has_prev': messages.has_prev,
        'page': messages.page,
        'pages': messages.pages
    })


@bp.route('/api/conversations/<int:user_id>/messages', methods=['POST'])
@login_required
def send_message(user_id):
    """Send a message to a user."""
    data = request.get_json()
    content = data.get('content')
    message_type = data.get('message_type', 'text')

    if not content:
        return jsonify({'error': 'Message content is required'}), 400

    # Check if recipient exists
    recipient = User.query.get(user_id)
    if not recipient:
        return jsonify({'error': 'Recipient not found'}), 404

    # Create message
    message = Message(
        sender_id=current_user.id,
        recipient_id=user_id,
        content=content,
        message_type=message_type,
        media_url=data.get('media_url')
    )

    db.session.add(message)
    db.session.commit()

    # Emit SocketIO event
    socketio.emit('new_message', {
        'message': message.to_dict(),
        'sender': current_user.to_dict()
    }, room=f'user_{user_id}')

    return jsonify({'success': True, 'message': message.to_dict()})


@bp.route('/api/messages/<int:message_id>', methods=['DELETE'])
@login_required
def delete_message(message_id):
    """Delete a message (soft delete for sender only)."""
    message = Message.query.filter_by(
        id=message_id,
        sender_id=current_user.id
    ).first_or_404()

    # In production, implement soft delete
    db.session.delete(message)
    db.session.commit()

    return jsonify({'success': True})


@bp.route('/api/unread-count', methods=['GET'])
@login_required
def unread_count():
    """Get total unread messages count."""
    count = Message.query.filter_by(
        recipient_id=current_user.id,
        is_read=False
    ).count()

    return jsonify({'unread_count': count})


# SocketIO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    if current_user.is_authenticated:
        join_room(f'user_{current_user.id}')
        emit('connected', {'user_id': current_user.id})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    if current_user.is_authenticated:
        leave_room(f'user_{current_user.id}')


@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicator."""
    recipient_id = data.get('recipient_id')
    if recipient_id and current_user.is_authenticated:
        emit('user_typing', {
            'user_id': current_user.id,
            'username': current_user.username
        }, room=f'user_{recipient_id}')


@socketio.on('read_receipt')
def handle_read_receipt(data):
    """Handle read receipt."""
    message_id = data.get('message_id')
    if message_id:
        message = Message.query.get(message_id)
        if message and message.recipient_id == current_user.id:
            message.mark_as_read()
            db.session.commit()
            emit('message_read', {
                'message_id': message_id
            }, room=f'user_{message.sender_id}')