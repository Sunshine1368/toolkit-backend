from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import requests
from urllib.parse import urlencode
from toolkit import db
from toolkit.models.user import User, UserSettings
from toolkit.models.oauth import OAuth
from .forms import (
    LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm,
    ChangePasswordForm, ProfileForm, EmailForm, OAuthBindForm, OAuthUnbindForm
)

bp = Blueprint('account', __name__)


def send_email(to, subject, body):
    """Simulate sending email (prints to console in development)."""
    # In production, integrate with Flask-Mail or external service
    print(f"\n=== EMAIL TO: {to} ===")
    print(f"Subject: {subject}")
    print(f"Body:\n{body}")
    print("=== END EMAIL ===\n")
    return True


# GitHub OAuth Configuration
GITHUB_CLIENT_ID = current_app.config.get('GITHUB_CLIENT_ID', '')
GITHUB_CLIENT_SECRET = current_app.config.get('GITHUB_CLIENT_SECRET', '')
GITHUB_AUTHORIZE_URL = 'https://github.com/login/oauth/authorize'
GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'
GITHUB_USER_API = 'https://api.github.com/user'


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with WTForms."""
    if current_user.is_authenticated:
        return redirect(url_for('www.index'))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember.data

        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User.query.filter_by(email=username).first()

        if user is None or not user.check_password(password):
            flash('Invalid username or password', 'error')
            return redirect(url_for('account.login'))

        if not user.is_active:
            flash('Account is disabled', 'error')
            return redirect(url_for('account.login'))

        login_user(user, remember=remember)
        user.ping()
        db.session.commit()

        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('www.index')

        flash('Logged in successfully', 'success')
        return redirect(next_page)

    return render_template('account/login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page with WTForms."""
    if current_user.is_authenticated:
        return redirect(url_for('www.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            display_name=form.username.data
        )
        user.set_password(form.password.data)

        # Create default settings
        settings = UserSettings(user=user)

        db.session.add(user)
        db.session.add(settings)
        db.session.commit()

        # Simulate welcome email
        send_email(
            user.email,
            'Welcome to Toolkit.uno',
            f'Hello {user.username},\n\nThank you for registering at Toolkit.uno!\n\n'
            f'Your account has been created successfully.\n\n'
            f'Best regards,\nToolkit.uno Team'
        )

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('account.login'))

    return render_template('account/register.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    """Logout user."""
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('www.index'))


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page."""
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.display_name = form.display_name.data or current_user.username
        current_user.bio = form.bio.data
        current_user.avatar_url = form.avatar_url.data
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('account.profile'))

    # Populate form with current data
    form.display_name.data = current_user.display_name
    form.bio.data = current_user.bio
    form.avatar_url.data = current_user.avatar_url

    return render_template('account/profile.html', form=form)


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password for logged-in users."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('account.change_password'))

        current_user.set_password(form.new_password.data)
        db.session.commit()

        # Simulate password change notification email
        send_email(
            current_user.email,
            'Password Changed',
            f'Hello {current_user.username},\n\n'
            f'Your password has been changed successfully.\n\n'
            f'If you did not make this change, please contact support immediately.\n\n'
            f'Best regards,\nToolkit.uno Team'
        )

        flash('Password changed successfully', 'success')
        return redirect(url_for('account.profile'))

    return render_template('account/change_password.html', form=form)


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page."""
    if current_user.is_authenticated:
        return redirect(url_for('www.index'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            # Generate reset token
            token = user.get_reset_password_token()
            reset_url = url_for('account.reset_password', token=token, _external=True)

            # Simulate sending reset email
            send_email(
                user.email,
                'Password Reset Request',
                f'Hello {user.username},\n\n'
                f'You requested a password reset. Click the link below to reset your password:\n\n'
                f'{reset_url}\n\n'
                f'This link will expire in 1 hour.\n\n'
                f'If you did not request this, please ignore this email.\n\n'
                f'Best regards,\nToolkit.uno Team'
            )

            flash('Password reset instructions have been sent to your email', 'info')
        else:
            # Still show success message to prevent email enumeration
            flash('If an account exists with that email, reset instructions will be sent', 'info')

        return redirect(url_for('account.login'))

    return render_template('account/forgot_password.html', form=form)


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password page."""
    if current_user.is_authenticated:
        return redirect(url_for('www.index'))

    user = User.verify_reset_password_token(token)
    if not user:
        flash('Invalid or expired reset token', 'error')
        return redirect(url_for('account.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()

        # Simulate password reset confirmation email
        send_email(
            user.email,
            'Password Reset Successful',
            f'Hello {user.username},\n\n'
            f'Your password has been reset successfully.\n\n'
            f'If you did not make this change, please contact support immediately.\n\n'
            f'Best regards,\nToolkit.uno Team'
        )

        flash('Password has been reset successfully', 'success')
        return redirect(url_for('account.login'))

    return render_template('account/reset_password.html', form=form, token=token)


@bp.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email():
    """Change email address."""
    form = EmailForm()
    if form.validate_on_submit():
        # Check if email already in use
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user and existing_user.id != current_user.id:
            flash('Email already registered', 'error')
            return redirect(url_for('account.change_email'))

        old_email = current_user.email
        current_user.email = form.email.data
        current_user.email_verified = False
        db.session.commit()

        # Simulate email change notification
        send_email(
            old_email,
            'Email Address Changed',
            f'Hello {current_user.username},\n\n'
            f'Your email address has been changed from {old_email} to {current_user.email}.\n\n'
            f'If you did not make this change, please contact support immediately.\n\n'
            f'Best regards,\nToolkit.uno Team'
        )

        send_email(
            current_user.email,
            'Verify Your New Email Address',
            f'Hello {current_user.username},\n\n'
            f'Please verify your new email address by clicking the link below:\n\n'
            f'{url_for("account.verify_email", _external=True)}?token=VERIFICATION_TOKEN_HERE\n\n'
            f'Best regards,\nToolkit.uno Team'
        )

        flash('Email address updated. Please verify your new email.', 'success')
        return redirect(url_for('account.profile'))

    return render_template('account/change_email.html', form=form)


@bp.route('/oauth')
@login_required
def oauth_connections():
    """View OAuth connections."""
    connections = OAuth.query.filter_by(user_id=current_user.id).all()
    return render_template('account/oauth.html', connections=connections)


@bp.route('/oauth/github')
def oauth_github():
    """Start GitHub OAuth flow."""
    if current_user.is_authenticated:
        # Binding existing account
        state = f'bind:{current_user.id}'
    else:
        # Login or registration
        state = 'login'

    params = {
        'client_id': GITHUB_CLIENT_ID,
        'redirect_uri': url_for('account.oauth_github_callback', _external=True),
        'scope': 'user:email',
        'state': state,
        'allow_signup': 'true'
    }

    auth_url = f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"
    return redirect(auth_url)


@bp.route('/oauth/github/callback')
def oauth_github_callback():
    """GitHub OAuth callback."""
    code = request.args.get('code')
    state = request.args.get('state')

    if not code:
        flash('Authorization failed: No code provided', 'error')
        return redirect(url_for('account.login'))

    # Exchange code for access token
    token_response = requests.post(
        GITHUB_TOKEN_URL,
        headers={'Accept': 'application/json'},
        data={
            'client_id': GITHUB_CLIENT_ID,
            'client_secret': GITHUB_CLIENT_SECRET,
            'code': code,
            'redirect_uri': url_for('account.oauth_github_callback', _external=True)
        }
    )

    if token_response.status_code != 200:
        flash('Failed to obtain access token from GitHub', 'error')
        return redirect(url_for('account.login'))

    token_data = token_response.json()
    access_token = token_data.get('access_token')

    if not access_token:
        flash('Failed to obtain access token from GitHub', 'error')
        return redirect(url_for('account.login'))

    # Get user info from GitHub
    user_response = requests.get(
        GITHUB_USER_API,
        headers={
            'Authorization': f'token {access_token}',
            'Accept': 'application/json'
        }
    )

    if user_response.status_code != 200:
        flash('Failed to fetch user info from GitHub', 'error')
        return redirect(url_for('account.login'))

    github_user = user_response.json()
    github_id = str(github_user['id'])
    username = github_user.get('login')
    email = github_user.get('email')
    avatar_url = github_user.get('avatar_url')
    profile_data = {
        'github_username': username,
        'github_profile': github_user.get('html_url'),
        'name': github_user.get('name'),
        'company': github_user.get('company'),
        'blog': github_user.get('blog'),
        'location': github_user.get('location'),
        'bio': github_user.get('bio')
    }

    # Check if this GitHub account is already connected
    existing_oauth = OAuth.find_by_provider_user_id('github', github_id)

    if state.startswith('bind:'):
        # Binding to existing account
        if not current_user.is_authenticated:
            flash('Authentication required for binding', 'error')
            return redirect(url_for('account.login'))

        if existing_oauth:
            if existing_oauth.user_id == current_user.id:
                flash('This GitHub account is already connected to your account', 'info')
            else:
                flash('This GitHub account is already connected to another account', 'error')
            return redirect(url_for('account.oauth_connections'))

        # Create OAuth connection
        OAuth.create_or_update(
            user_id=current_user.id,
            provider='github',
            provider_user_id=github_id,
            access_token=access_token,
            profile_data=profile_data
        )

        # Update user avatar if not set
        if not current_user.avatar_url and avatar_url:
            current_user.avatar_url = avatar_url
            db.session.commit()

        flash('GitHub account connected successfully', 'success')
        return redirect(url_for('account.oauth_connections'))

    else:
        # Login or registration
        if existing_oauth:
            # Existing user - log them in
            user = User.query.get(existing_oauth.user_id)
            if user and user.is_active:
                login_user(user)
                user.ping()
                db.session.commit()

                # Update OAuth token
                existing_oauth.access_token = access_token
                existing_oauth.profile_data = profile_data
                existing_oauth.updated_at = datetime.datetime.utcnow()
                db.session.commit()

                flash('Logged in with GitHub successfully', 'success')
                return redirect(url_for('www.index'))
            else:
                flash('Account is disabled', 'error')
                return redirect(url_for('account.login'))

        # New user - need to create account
        # Check if email already exists
        user = None
        if email:
            user = User.query.filter_by(email=email).first()

        if not user:
            # Create new user
            username_base = username or f'github_{github_id}'
            # Ensure username is unique
            counter = 1
            original_username = username_base
            while User.query.filter_by(username=username_base).first():
                username_base = f'{original_username}_{counter}'
                counter += 1

            user = User(
                username=username_base,
                email=email or f'{github_id}@github.toolkit.uno',  # Placeholder if no email
                display_name=github_user.get('name') or username_base,
                avatar_url=avatar_url
            )
            # Generate random password (user can set later)
            user.set_password(jwt.encode({'github_id': github_id}, current_app.config['SECRET_KEY']))

            settings = UserSettings(user=user)

            db.session.add(user)
            db.session.add(settings)
            db.session.commit()

        # Create OAuth connection
        OAuth.create_or_update(
            user_id=user.id,
            provider='github',
            provider_user_id=github_id,
            access_token=access_token,
            profile_data=profile_data
        )

        # Log in the user
        login_user(user)
        user.ping()
        db.session.commit()

        flash('Account created with GitHub successfully', 'success')
        return redirect(url_for('www.index'))


@bp.route('/oauth/<provider>/unbind', methods=['POST'])
@login_required
def oauth_unbind(provider):
    """Unbind OAuth connection."""
    oauth = OAuth.query.filter_by(
        user_id=current_user.id,
        provider=provider
    ).first()

    if not oauth:
        flash(f'No {provider} connection found', 'error')
        return redirect(url_for('account.oauth_connections'))

    # Check if user has a password set (need at least one auth method)
    if not current_user.password_hash:
        # Check if there are other OAuth connections
        other_connections = OAuth.query.filter(
            OAuth.user_id == current_user.id,
            OAuth.provider != provider
        ).count()

        if other_connections == 0:
            flash('Cannot remove last authentication method. Please set a password first.', 'error')
            return redirect(url_for('account.oauth_connections'))

    db.session.delete(oauth)
    db.session.commit()

    flash(f'{provider.title()} account disconnected successfully', 'success')
    return redirect(url_for('account.oauth_connections'))


@bp.route('/verify-email')
@login_required
def verify_email():
    """Email verification endpoint (placeholder)."""
    # In production, implement email verification with token
    flash('Email verification is not yet implemented', 'info')
    return redirect(url_for('account.profile'))


@bp.route('/api/user')
@login_required
def api_user():
    """Get current user info (API)."""
    return jsonify(current_user.to_dict())