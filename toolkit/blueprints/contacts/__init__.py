from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import current_user, login_required
from sqlalchemy import or_, and_
from toolkit import db
from toolkit.models.contact import Contact
from toolkit.models.user import User

bp = Blueprint('contacts', __name__)


@bp.route('/')
@login_required
def index():
    """Contacts page."""
    return render_template('contacts/index.html')


@bp.route('/api/contacts', methods=['GET'])
@login_required
def api_contacts():
    """Get contacts API."""
    search = request.args.get('search', '')
    favorites_only = request.args.get('favorites_only', 'false').lower() == 'true'

    query = Contact.query.filter_by(user_id=current_user.id)

    if favorites_only:
        query = query.filter_by(is_favorite=True)

    if search:
        # Search in contacts by username or nickname
        query = query.join(User, Contact.contact_id == User.id)\
            .filter(or_(
                User.username.ilike(f'%{search}%'),
                User.display_name.ilike(f'%{search}%'),
                Contact.nickname.ilike(f'%{search}%')
            ))

    contacts = query.order_by(Contact.is_favorite.desc(), Contact.created_at.desc()).all()

    result = []
    for contact in contacts:
        contact_user = User.query.get(contact.contact_id)
        if contact_user:
            result.append({
                'contact': contact.to_dict(),
                'user': contact_user.to_dict()
            })

    return jsonify({'contacts': result})


@bp.route('/api/contacts', methods=['POST'])
@login_required
def add_contact():
    """Add a new contact."""
    data = request.get_json()
    username = data.get('username')

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    # Find user by username or email
    contact_user = User.query.filter(
        or_(User.username == username, User.email == username)
    ).first()

    if not contact_user:
        return jsonify({'error': 'User not found'}), 404

    if contact_user.id == current_user.id:
        return jsonify({'error': 'Cannot add yourself as a contact'}), 400

    # Check if contact already exists
    existing_contact = Contact.query.filter_by(
        user_id=current_user.id,
        contact_id=contact_user.id
    ).first()

    if existing_contact:
        return jsonify({'error': 'Contact already exists'}), 400

    # Create contact
    contact = Contact(
        user_id=current_user.id,
        contact_id=contact_user.id,
        nickname=data.get('nickname')
    )

    db.session.add(contact)
    db.session.commit()

    return jsonify({
        'success': True,
        'contact': contact.to_dict(),
        'user': contact_user.to_dict()
    })


@bp.route('/api/contacts/<int:contact_id>', methods=['PUT'])
@login_required
def update_contact(contact_id):
    """Update contact."""
    contact = Contact.query.filter_by(
        id=contact_id,
        user_id=current_user.id
    ).first_or_404()

    data = request.get_json()

    if 'nickname' in data:
        contact.nickname = data['nickname']
    if 'notes' in data:
        contact.notes = data['notes']
    if 'is_favorite' in data:
        contact.is_favorite = bool(data['is_favorite'])
    if 'is_blocked' in data:
        contact.is_blocked = bool(data['is_blocked'])

    db.session.commit()

    return jsonify({'success': True, 'contact': contact.to_dict()})


@bp.route('/api/contacts/<int:contact_id>', methods=['DELETE'])
@login_required
def delete_contact(contact_id):
    """Delete contact."""
    contact = Contact.query.filter_by(
        id=contact_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(contact)
    db.session.commit()

    return jsonify({'success': True})


@bp.route('/api/search/users', methods=['GET'])
@login_required
def search_users():
    """Search for users to add as contacts."""
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify({'users': []})

    users = User.query.filter(
        and_(
            User.id != current_user.id,
            or_(
                User.username.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%'),
                User.display_name.ilike(f'%{query}%')
            )
        )
    ).limit(10).all()

    # Filter out users already in contacts
    contact_ids = {c.contact_id for c in Contact.query.filter_by(user_id=current_user.id).all()}
    filtered_users = [u for u in users if u.id not in contact_ids]

    return jsonify({
        'users': [{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'display_name': u.display_name,
            'avatar_url': u.avatar_url
        } for u in filtered_users]
    })


@bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_contacts():
    """Import contacts page."""
    if request.method == 'POST':
        # Handle contact import (CSV, vCard, etc.)
        flash('Contact import is not yet implemented', 'info')
        return redirect(url_for('contacts.import_contacts'))

    return render_template('contacts/import.html')


@bp.route('/export')
@login_required
def export_contacts():
    """Export contacts."""
    # In production, generate CSV or vCard export
    flash('Contact export is not yet implemented', 'info')
    return redirect(url_for('contacts.index'))