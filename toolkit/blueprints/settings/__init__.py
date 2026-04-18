from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import current_user, login_required
from toolkit import db
from toolkit.models.user import UserSettings

bp = Blueprint('settings', __name__)


@bp.route('/')
@login_required
def index():
    """Settings main page."""
    return render_template('settings/index.html')


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Profile settings."""
    if request.method == 'POST':
        display_name = request.form.get('display_name')
        bio = request.form.get('bio')

        current_user.display_name = display_name or current_user.username
        current_user.bio = bio
        db.session.commit()

        flash('Profile updated successfully', 'success')
        return redirect(url_for('settings.profile'))

    return render_template('settings/profile.html')


@bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    """Account settings."""
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'change_email':
            new_email = request.form.get('new_email')
            if User.query.filter_by(email=new_email).first():
                flash('Email already in use', 'error')
            else:
                current_user.email = new_email
                current_user.email_verified = False
                db.session.commit()
                flash('Email updated successfully. Please verify your new email.', 'success')

        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if not current_user.check_password(current_password):
                flash('Current password is incorrect', 'error')
            elif len(new_password) < 8:
                flash('New password must be at least 8 characters', 'error')
            elif new_password != confirm_password:
                flash('New passwords do not match', 'error')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                flash('Password changed successfully', 'success')

        elif action == 'deactivate':
            confirm = request.form.get('confirm_deactivate')
            if confirm == 'DELETE':
                current_user.is_active = False
                db.session.commit()
                flash('Account deactivated successfully', 'success')
                return redirect(url_for('account.logout'))

        return redirect(url_for('settings.account'))

    return render_template('settings/account.html')


@bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """User preferences."""
    settings = current_user.settings
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()

    if request.method == 'POST':
        theme = request.form.get('theme')
        language = request.form.get('language')
        timezone = request.form.get('timezone')
        email_notifications = bool(request.form.get('email_notifications'))
        push_notifications = bool(request.form.get('push_notifications'))

        settings.theme = theme
        settings.language = language
        settings.timezone = timezone
        settings.email_notifications = email_notifications
        settings.push_notifications = push_notifications

        db.session.commit()
        flash('Preferences updated successfully', 'success')
        return redirect(url_for('settings.preferences'))

    return render_template('settings/preferences.html', settings=settings)


@bp.route('/security', methods=['GET', 'POST'])
@login_required
def security():
    """Security settings."""
    settings = current_user.settings
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'enable_2fa':
            # In production, generate and display QR code for 2FA setup
            flash('Two-factor authentication setup is not yet implemented', 'info')

        elif action == 'disable_2fa':
            settings.two_factor_enabled = False
            settings.two_factor_secret = None
            db.session.commit()
            flash('Two-factor authentication disabled', 'success')

        elif action == 'regenerate_api_key':
            # In production, generate new API key
            flash('API key regeneration is not yet implemented', 'info')

        return redirect(url_for('settings.security'))

    return render_template('settings/security.html', settings=settings)


@bp.route('/notifications', methods=['GET', 'POST'])
@login_required
def notifications():
    """Notification settings."""
    settings = current_user.settings
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()

    if request.method == 'POST':
        # Update notification preferences
        for key in request.form:
            if key.startswith('notify_'):
                # Process notification preferences
                pass

        db.session.commit()
        flash('Notification settings updated', 'success')
        return redirect(url_for('settings.notifications'))

    return render_template('settings/notifications.html')


@bp.route('/api')
@login_required
def api():
    """API settings."""
    return render_template('settings/api.html')