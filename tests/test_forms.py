import pytest
from toolkit.blueprints.account.forms import (
    LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm,
    ChangePasswordForm, ProfileForm, EmailForm
)
from toolkit.models.user import User
from werkzeug.security import generate_password_hash


class FormTestBase:
    """Base class for form tests that need app context."""

    def create_form_in_context(self, app, form_class, data):
        """Create and validate form within app context."""
        with app.app_context():
            form = form_class(data=data)
            return form, form.validate()


class TestLoginForm(FormTestBase):
    """Test LoginForm."""

    def test_valid_form(self, app):
        """Test valid form data."""
        with app.app_context():
            form = LoginForm(data={
                'username': 'testuser',
                'password': 'password123',
                'remember': True
            })
            assert form.validate() is True

    def test_missing_username(self, app):
        """Test missing username."""
        with app.app_context():
            form = LoginForm(data={
                'password': 'password123',
                'remember': False
            })
            assert form.validate() is False
            assert 'username' in form.errors

    def test_missing_password(self, app):
        """Test missing password."""
        with app.app_context():
            form = LoginForm(data={
                'username': 'testuser',
                'remember': False
            })
            assert form.validate() is False
            assert 'password' in form.errors

    def test_remember_field_optional(self, app):
        """Test remember field is optional."""
        with app.app_context():
            form = LoginForm(data={
                'username': 'testuser',
                'password': 'password123'
            })
            assert form.validate() is True
            # Remember should default to False
            assert form.remember.data is False


class TestRegistrationForm:
    """Test RegistrationForm."""

    def test_valid_form(self, app, db):
        """Test valid form data."""
        with app.app_context():
            form = RegistrationForm(data={
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'password123',
                'password2': 'password123'
            })
            assert form.validate() is True

    def test_missing_username(self, app, db):
        """Test missing username."""
        with app.app_context():
            form = RegistrationForm(data={
                'email': 'test@example.com',
                'password': 'password123',
                'password2': 'password123'
            })
            assert form.validate() is False
            assert 'username' in form.errors

    def test_username_too_short(self, app, db):
        """Test username too short."""
        with app.app_context():
            form = RegistrationForm(data={
                'username': 'ab',
                'email': 'test@example.com',
                'password': 'password123',
                'password2': 'password123'
            })
            assert form.validate() is False
            assert 'username' in form.errors

    def test_username_too_long(self, app, db):
        """Test username too long."""
        with app.app_context():
            form = RegistrationForm(data={
                'username': 'a' * 65,
                'email': 'test@example.com',
                'password': 'password123',
                'password2': 'password123'
            })
            assert form.validate() is False
            assert 'username' in form.errors

    def test_missing_email(self, app, db):
        """Test missing email."""
        with app.app_context():
            form = RegistrationForm(data={
                'username': 'testuser',
                'password': 'password123',
                'password2': 'password123'
            })
            assert form.validate() is False
            assert 'email' in form.errors

    def test_invalid_email(self, app, db):
        """Test invalid email format."""
        with app.app_context():
            form = RegistrationForm(data={
                'username': 'testuser',
                'email': 'invalid-email',
                'password': 'password123',
                'password2': 'password123'
            })
            assert form.validate() is False
            assert 'email' in form.errors

    def test_email_too_long(self, app, db):
        """Test email too long."""
        with app.app_context():
            form = RegistrationForm(data={
                'username': 'testuser',
                'email': 'a' * 121 + '@example.com',
                'password': 'password123',
                'password2': 'password123'
            })
            assert form.validate() is False
            assert 'email' in form.errors

    def test_missing_password(self, app, db):
        """Test missing password."""
        with app.app_context():
            form = RegistrationForm(data={
                'username': 'testuser',
                'email': 'test@example.com',
                'password2': 'password123'
            })
            assert form.validate() is False
            assert 'password' in form.errors

    def test_password_too_short(self, app, db):
        """Test password too short."""
        with app.app_context():
            form = RegistrationForm(data={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'short',
                'password2': 'short'
            })
            assert form.validate() is False
            assert 'password' in form.errors

    def test_password_mismatch(self, app, db):
        """Test password mismatch."""
        with app.app_context():
            form = RegistrationForm(data={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'password123',
                'password2': 'different'
            })
            assert form.validate() is False
            assert 'password2' in form.errors

    def test_duplicate_username(self, app, db):
        """Test duplicate username validation."""
        with app.app_context():
            # Create existing user
            user = User(
                username='existinguser',
                email='existing@example.com',
                password_hash=generate_password_hash('password123')
            )
            db.session.add(user)
            db.session.commit()

            form = RegistrationForm(data={
                'username': 'existinguser',
                'email': 'new@example.com',
                'password': 'password123',
                'password2': 'password123'
            })
            assert form.validate() is False
            assert 'username' in form.errors
            assert 'already exists' in form.username.errors[0]

    def test_duplicate_email(self, app, db):
        """Test duplicate email validation."""
        with app.app_context():
            # Create existing user
            user = User(
                username='existinguser',
                email='existing@example.com',
                password_hash=generate_password_hash('password123')
            )
            db.session.add(user)
            db.session.commit()

            form = RegistrationForm(data={
                'username': 'newuser',
                'email': 'existing@example.com',
                'password': 'password123',
                'password2': 'password123'
            })
            assert form.validate() is False
            assert 'email' in form.errors
            assert 'already registered' in form.email.errors[0]


class TestForgotPasswordForm:
    """Test ForgotPasswordForm."""

    def test_valid_form(self, app):
        """Test valid form data."""
        with app.app_context():
            form = ForgotPasswordForm(data={
                'email': 'user@example.com'
            })
            assert form.validate() is True

    def test_missing_email(self, app):
        """Test missing email."""
        with app.app_context():
            form = ForgotPasswordForm(data={})
            assert form.validate() is False
            assert 'email' in form.errors

    def test_invalid_email(self, app):
        """Test invalid email format."""
        with app.app_context():
            form = ForgotPasswordForm(data={
                'email': 'invalid-email'
            })
            assert form.validate() is False
            assert 'email' in form.errors


class TestResetPasswordForm:
    """Test ResetPasswordForm."""

    def test_valid_form(self, app):
        """Test valid form data."""
        with app.app_context():
            form = ResetPasswordForm(data={
                'password': 'newpassword123',
                'password2': 'newpassword123'
            })
            assert form.validate() is True

    def test_missing_password(self, app):
        """Test missing password."""
        with app.app_context():
            form = ResetPasswordForm(data={
                'password2': 'newpassword123'
            })
            assert form.validate() is False
            assert 'password' in form.errors

    def test_password_too_short(self, app):
        """Test password too short."""
        with app.app_context():
            form = ResetPasswordForm(data={
                'password': 'short',
                'password2': 'short'
            })
            assert form.validate() is False
            assert 'password' in form.errors

    def test_password_mismatch(self, app):
        """Test password mismatch."""
        with app.app_context():
            form = ResetPasswordForm(data={
                'password': 'newpassword123',
                'password2': 'different'
            })
            assert form.validate() is False
            assert 'password2' in form.errors


class TestChangePasswordForm:
    """Test ChangePasswordForm."""

    def test_valid_form(self, app):
        """Test valid form data."""
        with app.app_context():
            form = ChangePasswordForm(data={
                'current_password': 'oldpassword',
                'new_password': 'newpassword123',
                'new_password2': 'newpassword123'
            })
            assert form.validate() is True

    def test_missing_current_password(self, app):
        """Test missing current password."""
        with app.app_context():
            form = ChangePasswordForm(data={
                'new_password': 'newpassword123',
                'new_password2': 'newpassword123'
            })
            assert form.validate() is False
            assert 'current_password' in form.errors

    def test_missing_new_password(self, app):
        """Test missing new password."""
        with app.app_context():
            form = ChangePasswordForm(data={
                'current_password': 'oldpassword',
                'new_password2': 'newpassword123'
            })
            assert form.validate() is False
            assert 'new_password' in form.errors

    def test_new_password_too_short(self, app):
        """Test new password too short."""
        with app.app_context():
            form = ChangePasswordForm(data={
                'current_password': 'oldpassword',
                'new_password': 'short',
                'new_password2': 'short'
            })
            assert form.validate() is False
            assert 'new_password' in form.errors

    def test_new_password_mismatch(self, app):
        """Test new password mismatch."""
        with app.app_context():
            form = ChangePasswordForm(data={
                'current_password': 'oldpassword',
                'new_password': 'newpassword123',
                'new_password2': 'different'
            })
            assert form.validate() is False
            assert 'new_password2' in form.errors


class TestProfileForm:
    """Test ProfileForm."""

    def test_valid_form(self, app):
        """Test valid form data."""
        with app.app_context():
            form = ProfileForm(data={
                'display_name': 'Test User',
                'bio': 'This is a test bio.',
                'avatar_url': 'http://example.com/avatar.jpg'
            })
            assert form.validate() is True

    def test_empty_form_valid(self, app):
        """Test empty form is valid (all fields optional)."""
        with app.app_context():
            form = ProfileForm(data={})
            assert form.validate() is True

    def test_display_name_too_long(self, app):
        """Test display name too long."""
        with app.app_context():
            form = ProfileForm(data={
                'display_name': 'a' * 65,
                'bio': 'Test bio',
                'avatar_url': 'http://example.com/avatar.jpg'
            })
            assert form.validate() is False
            assert 'display_name' in form.errors

    def test_bio_too_long(self, app):
        """Test bio too long."""
        with app.app_context():
            form = ProfileForm(data={
                'display_name': 'Test User',
                'bio': 'a' * 501,
                'avatar_url': 'http://example.com/avatar.jpg'
            })
            assert form.validate() is False
            assert 'bio' in form.errors

    def test_avatar_url_too_long(self, app):
        """Test avatar URL too long."""
        with app.app_context():
            form = ProfileForm(data={
                'display_name': 'Test User',
                'bio': 'Test bio',
                'avatar_url': 'http://example.com/' + 'a' * 240
            })
            assert form.validate() is False
            assert 'avatar_url' in form.errors


class TestEmailForm:
    """Test EmailForm."""

    def test_valid_form(self, app, db):
        """Test valid form data."""
        with app.app_context():
            form = EmailForm(data={
                'email': 'newemail@example.com'
            })
            assert form.validate() is True

    def test_missing_email(self, app, db):
        """Test missing email."""
        with app.app_context():
            form = EmailForm(data={})
            assert form.validate() is False
            assert 'email' in form.errors

    def test_invalid_email(self, app, db):
        """Test invalid email format."""
        with app.app_context():
            form = EmailForm(data={
                'email': 'invalid-email'
            })
            assert form.validate() is False
            assert 'email' in form.errors

    def test_duplicate_email(self, app, db):
        """Test duplicate email validation."""
        with app.app_context():
            # Create existing user
            user = User(
                username='existinguser',
                email='existing@example.com',
                password_hash=generate_password_hash('password123')
            )
            db.session.add(user)
            db.session.commit()

            form = EmailForm(data={
                'email': 'existing@example.com'
            })
            assert form.validate() is False
            assert 'email' in form.errors
            assert 'already registered' in form.email.errors[0]