import pytest
from flask import url_for, get_flashed_messages
from unittest.mock import patch, MagicMock


class TestLogin:
    """Test login functionality."""

    def test_login_page_get(self, client):
        """Test GET request to login page."""
        response = client.get(url_for('account.login'))
        assert response.status_code == 200
        assert b'Login' in response.data or b'Sign In' in response.data

    def test_login_success(self, account_client, user_factory):
        """Test successful login."""
        user = user_factory(password='password123')

        response = account_client.post(url_for('account.login'), data={
            'username': user.username,
            'password': 'password123',
            'remember': False
        }, follow_redirects=False)

        assert response.status_code == 302  # Redirect
        # Should redirect to index
        assert url_for('www.index') in response.location

        # Verify user is logged in by checking cookies
        cookies = response.headers.getlist('Set-Cookie')
        assert any('remember_token' in cookie for cookie in cookies)

    def test_login_with_email(self, client, user_factory):
        """Test login with email instead of username."""
        user = user_factory(password='password123')

        response = client.post(url_for('account.login'), data={
            'username': user.email,
            'password': 'password123',
            'remember': False
        }, follow_redirects=False)

        assert response.status_code == 302
        assert url_for('www.index') in response.location

    def test_login_invalid_username(self, client):
        """Test login with invalid username."""
        response = client.post(url_for('account.login'), data={
            'username': 'nonexistent',
            'password': 'password',
            'remember': False
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should show error message
        assert b'Invalid username or password' in response.data

    def test_login_invalid_password(self, client, user_factory):
        """Test login with invalid password."""
        user = user_factory(password='correctpassword')

        response = client.post(url_for('account.login'), data={
            'username': user.username,
            'password': 'wrongpassword',
            'remember': False
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Invalid username or password' in response.data

    def test_login_inactive_account(self, client, user_factory):
        """Test login with inactive account."""
        user = user_factory(password='password123', is_active=False)

        response = client.post(url_for('account.login'), data={
            'username': user.username,
            'password': 'password123',
            'remember': False
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Account is disabled' in response.data

    def test_login_remember_me(self, client, user_factory):
        """Test login with remember me checked."""
        user = user_factory(password='password123')

        response = client.post(url_for('account.login'), data={
            'username': user.username,
            'password': 'password123',
            'remember': True
        }, follow_redirects=False)

        assert response.status_code == 302
        # Check if remember cookie is set
        cookies = response.headers.get_all('Set-Cookie')
        remember_cookies = [c for c in cookies if 'remember_token' in c]
        assert len(remember_cookies) > 0

    def test_login_already_authenticated(self, client, user_factory):
        """Test login when already authenticated."""
        user = user_factory(password='password123')

        # First login
        client.post(url_for('account.login'), data={
            'username': user.username,
            'password': 'password123'
        })

        # Try to access login page again
        response = client.get(url_for('account.login'), follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to index
        assert b'index' in response.data.lower() or b'home' in response.data.lower()

    def test_login_next_parameter(self, client, user_factory):
        """Test login with next parameter."""
        user = user_factory(password='password123')

        response = client.post(
            url_for('account.login', next='/profile'),
            data={
                'username': user.username,
                'password': 'password123',
                'remember': False
            },
            follow_redirects=False
        )

        assert response.status_code == 302
        # Should redirect to /profile
        assert '/profile' in response.location


class TestLogout:
    """Test logout functionality."""

    def test_logout_requires_login(self, client):
        """Test logout requires authentication."""
        response = client.get(url_for('account.logout'), follow_redirects=True)
        # Should redirect to login
        assert response.status_code == 200
        assert b'Login' in response.data or b'Sign In' in response.data

    def test_logout_success(self, client, user_factory):
        """Test successful logout."""
        user = user_factory(password='password123')

        # Login first
        client.post(url_for('account.login'), data={
            'username': user.username,
            'password': 'password123'
        })

        # Then logout
        response = client.get(url_for('account.logout'), follow_redirects=True)
        assert response.status_code == 200
        assert b'Logged out successfully' in response.data

        # Verify user is logged out
        with client.session_transaction() as session:
            assert 'user_id' not in session


class TestRegistration:
    """Test registration functionality."""

    def test_register_page_get(self, client):
        """Test GET request to registration page."""
        response = client.get(url_for('account.register'))
        assert response.status_code == 200
        assert b'Register' in response.data

    def test_register_success(self, client, db):
        """Test successful registration."""
        response = client.post(url_for('account.register'), data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'password2': 'password123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Registration successful' in response.data

        # Verify user was created
        from toolkit.models.user import User
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'newuser@example.com'

        # Verify settings were created
        assert user.settings is not None

    def test_register_duplicate_username(self, client, user_factory):
        """Test registration with duplicate username."""
        user = user_factory(username='existinguser')

        response = client.post(url_for('account.register'), data={
            'username': 'existinguser',
            'email': 'new@example.com',
            'password': 'password123',
            'password2': 'password123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Username already exists' in response.data

    def test_register_duplicate_email(self, client, user_factory):
        """Test registration with duplicate email."""
        user = user_factory(email='existing@example.com')

        response = client.post(url_for('account.register'), data={
            'username': 'newuser',
            'email': 'existing@example.com',
            'password': 'password123',
            'password2': 'password123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Email already registered' in response.data

    def test_register_password_mismatch(self, client):
        """Test registration with password mismatch."""
        response = client.post(url_for('account.register'), data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'password123',
            'password2': 'different'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Passwords must match' in response.data

    def test_register_short_password(self, client):
        """Test registration with short password."""
        response = client.post(url_for('account.register'), data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'short',
            'password2': 'short'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Password must be at least 8 characters' in response.data

    def test_register_already_authenticated(self, client, user_factory):
        """Test registration when already authenticated."""
        user = user_factory(password='password123')

        # Login first
        client.post(url_for('account.login'), data={
            'username': user.username,
            'password': 'password123'
        })

        # Try to access registration page
        response = client.get(url_for('account.register'), follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to index
        assert b'index' in response.data.lower()


class TestProfile:
    """Test profile functionality."""

    def test_profile_requires_login(self, client):
        """Test profile page requires authentication."""
        response = client.get(url_for('account.profile'), follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data or b'Sign In' in response.data

    def test_profile_page_get(self, client, user_factory):
        """Test GET request to profile page."""
        user = user_factory(password='password123')

        # Login first
        client.post(url_for('account.login'), data={
            'username': user.username,
            'password': 'password123'
        })

        response = client.get(url_for('account.profile'))
        assert response.status_code == 200
        assert b'Profile' in response.data or b'Update Profile' in response.data

    def test_profile_update(self, client, user_factory, db):
        """Test updating profile."""
        user = user_factory(password='password123', display_name='Old Name', bio='Old bio')

        # Login
        client.post(url_for('account.login'), data={
            'username': user.username,
            'password': 'password123'
        })

        response = client.post(url_for('account.profile'), data={
            'display_name': 'New Name',
            'bio': 'New bio',
            'avatar_url': 'http://example.com/new-avatar.jpg'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Profile updated successfully' in response.data

        # Refresh user from database
        db.session.refresh(user)
        assert user.display_name == 'New Name'
        assert user.bio == 'New bio'
        assert user.avatar_url == 'http://example.com/new-avatar.jpg'


class TestChangePassword:
    """Test change password functionality."""

    def test_change_password_requires_login(self, client):
        """Test change password page requires authentication."""
        response = client.get(url_for('account.change_password'), follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_change_password_page_get(self, client, user_factory):
        """Test GET request to change password page."""
        user = user_factory(password='password123')

        # Login
        client.post(url_for('account.login'), data={
            'username': user.username,
            'password': 'password123'
        })

        response = client.get(url_for('account.change_password'))
        assert response.status_code == 200
        assert b'Change Password' in response.data

    def test_change_password_success(self, client, user_factory, db):
        """Test successful password change."""
        user = user_factory(password='oldpassword')

        # Login
        client.post(url_for('account.login'), data={
            'username': user.username,
            'password': 'oldpassword'
        })

        response = client.post(url_for('account.change_password'), data={
            'current_password': 'oldpassword',
            'new_password': 'newpassword123',
            'new_password2': 'newpassword123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Password changed successfully' in response.data

        # Verify password was changed
        db.session.refresh(user)
        assert user.check_password('newpassword123') is True
        assert user.check_password('oldpassword') is False

    def test_change_password_wrong_current(self, client, user_factory):
        """Test password change with wrong current password."""
        user = user_factory(password='correctpassword')

        # Login
        client.post(url_for('account.login'), data={
            'username': user.username,
            'password': 'correctpassword'
        })

        response = client.post(url_for('account.change_password'), data={
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'new_password2': 'newpassword123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Current password is incorrect' in response.data

    def test_change_password_mismatch(self, client, user_factory):
        """Test password change with mismatched new passwords."""
        user = user_factory(password='oldpassword')

        # Login
        client.post(url_for('account.login'), data={
            'username': user.username,
            'password': 'oldpassword'
        })

        response = client.post(url_for('account.change_password'), data={
            'current_password': 'oldpassword',
            'new_password': 'newpassword123',
            'new_password2': 'different'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Passwords must match' in response.data

    def test_change_password_short(self, client, user_factory):
        """Test password change with short new password."""
        user = user_factory(password='oldpassword')

        # Login
        client.post(url_for('account.login'), data={
            'username': user.username,
            'password': 'oldpassword'
        })

        response = client.post(url_for('account.change_password'), data={
            'current_password': 'oldpassword',
            'new_password': 'short',
            'new_password2': 'short'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Password must be at least 8 characters' in response.data


class TestForgotPassword:
    """Test forgot password functionality."""

    def test_forgot_password_page_get(self, client):
        """Test GET request to forgot password page."""
        response = client.get(url_for('account.forgot_password'))
        assert response.status_code == 200
        assert b'Forgot Password' in response.data or b'Reset Password' in response.data

    def test_forgot_password_success(self, client, user_factory):
        """Test successful forgot password request."""
        user = user_factory()

        response = client.post(url_for('account.forgot_password'), data={
            'email': user.email
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should show success message (even if email doesn't exist, for security)
        assert b'reset instructions' in response.data.lower()

    def test_forgot_password_invalid_email(self, client):
        """Test forgot password with invalid email format."""
        response = client.post(url_for('account.forgot_password'), data={
            'email': 'invalid-email'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should show validation error
        assert b'Invalid email address' in response.data

    def test_forgot_password_already_authenticated(self, client, user_factory):
        """Test forgot password when already authenticated."""
        user = user_factory(password='password123')

        # Login first
        client.post(url_for('account.login'), data={
            'username': user.username,
            'password': 'password123'
        })

        # Try to access forgot password page
        response = client.get(url_for('account.forgot_password'), follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to index
        assert b'index' in response.data.lower()


class TestResetPassword:
    """Test reset password functionality."""

    def test_reset_password_invalid_token(self, client):
        """Test reset password with invalid token."""
        response = client.get(url_for('account.reset_password', token='invalid-token'))
        assert response.status_code == 302  # Redirect to forgot password
        # Should redirect to forgot password page

    def test_reset_password_valid_token_get(self, app, client, user_factory):
        """Test GET request to reset password page with valid token."""
        with app.app_context():
            user = user_factory()
            token = user.get_reset_password_token()

            response = client.get(url_for('account.reset_password', token=token))
            assert response.status_code == 200
            assert b'Reset Password' in response.data

    def test_reset_password_success(self, app, client, user_factory, db):
        """Test successful password reset."""
        with app.app_context():
            user = user_factory(password='oldpassword')
            token = user.get_reset_password_token()

            response = client.post(url_for('account.reset_password', token=token), data={
                'password': 'newpassword123',
                'password2': 'newpassword123'
            }, follow_redirects=True)

            assert response.status_code == 200
            assert b'Password has been reset successfully' in response.data

            # Verify password was changed
            db.session.refresh(user)
            assert user.check_password('newpassword123') is True
            assert user.check_password('oldpassword') is False

    def test_reset_password_mismatch(self, app, client, user_factory):
        """Test password reset with mismatched passwords."""
        with app.app_context():
            user = user_factory()
            token = user.get_reset_password_token()

            response = client.post(url_for('account.reset_password', token=token), data={
                'password': 'newpassword123',
                'password2': 'different'
            }, follow_redirects=True)

            assert response.status_code == 200
            assert b'Passwords must match' in response.data

    def test_reset_password_short(self, app, client, user_factory):
        """Test password reset with short password."""
        with app.app_context():
            user = user_factory()
            token = user.get_reset_password_token()

            response = client.post(url_for('account.reset_password', token=token), data={
                'password': 'short',
                'password2': 'short'
            }, follow_redirects=True)

            assert response.status_code == 200
            assert b'Password must be at least 8 characters' in response.data


class TestOAuth:
    """Test OAuth functionality."""

    def test_oauth_connections_requires_login(self, client):
        """Test OAuth connections page requires authentication."""
        response = client.get(url_for('account.oauth_connections'), follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_oauth_connections_page(self, client, user_factory):
        """Test OAuth connections page."""
        user = user_factory(password='password123')

        # Login
        client.post(url_for('account.login'), data={
            'username': user.username,
            'password': 'password123'
        })

        response = client.get(url_for('account.oauth_connections'))
        assert response.status_code == 200
        assert b'OAuth' in response.data or b'Connections' in response.data

    def test_oauth_github_start(self, client):
        """Test starting GitHub OAuth flow."""
        response = client.get(url_for('account.oauth_github'), follow_redirects=False)
        assert response.status_code == 302
        # Should redirect to GitHub
        assert 'github.com' in response.location

    @patch('requests.post')
    @patch('requests.get')
    def test_oauth_github_callback_new_user(self, mock_get, mock_post, app, client, db):
        """Test GitHub OAuth callback for new user."""
        # Mock token response
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {'access_token': 'test_token'}
        mock_post.return_value = mock_token_response

        # Mock user info response
        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {
            'id': 12345,
            'login': 'githubuser',
            'email': 'github@example.com',
            'avatar_url': 'http://example.com/avatar.jpg',
            'html_url': 'https://github.com/githubuser',
            'name': 'GitHub User',
            'company': 'GitHub',
            'blog': 'https://blog.example.com',
            'location': 'San Francisco',
            'bio': 'GitHub bio'
        }
        mock_get.return_value = mock_user_response

        with app.app_context():
            response = client.get(
                url_for('account.oauth_github_callback', code='test_code', state='login'),
                follow_redirects=True
            )

            assert response.status_code == 200
            assert b'Account created with GitHub successfully' in response.data

            # Verify user was created
            from toolkit.models.user import User, OAuth
            user = User.query.filter_by(email='github@example.com').first()
            assert user is not None
            assert user.username.startswith('githubuser')

            # Verify OAuth connection was created
            oauth = OAuth.find_by_provider_user_id('github', '12345')
            assert oauth is not None
            assert oauth.user_id == user.id

    @patch('requests.post')
    @patch('requests.get')
    def test_oauth_github_callback_existing_user(self, mock_get, mock_post, app, client, db, user_factory):
        """Test GitHub OAuth callback for existing user."""
        # Create user with existing OAuth connection
        user = user_factory()
        from toolkit.models.oauth import OAuth
        oauth = OAuth(
            user_id=user.id,
            provider='github',
            provider_user_id='12345',
            access_token='old_token'
        )
        db.session.add(oauth)
        db.session.commit()

        # Mock token response
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {'access_token': 'new_token'}
        mock_post.return_value = mock_token_response

        # Mock user info response
        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {
            'id': 12345,
            'login': 'githubuser',
            'email': user.email
        }
        mock_get.return_value = mock_user_response

        with app.app_context():
            response = client.get(
                url_for('account.oauth_github_callback', code='test_code', state='login'),
                follow_redirects=True
            )

            assert response.status_code == 200
            assert b'Logged in with GitHub successfully' in response.data

            # Verify token was updated
            db.session.refresh(oauth)
            assert oauth.access_token == 'new_token'

    def test_oauth_unbind(self, client, user_factory, db):
        """Test unbinding OAuth connection."""
        user = user_factory(password='password123')

        # Create OAuth connection
        from toolkit.models.oauth import OAuth
        oauth = OAuth(
            user_id=user.id,
            provider='github',
            provider_user_id='12345'
        )
        db.session.add(oauth)
        db.session.commit()

        # Login
        client.post(url_for('account.login'), data={
            'username': user.username,
            'password': 'password123'
        })

        # Try to unbind (requires POST)
        response = client.post(url_for('account.oauth_unbind', provider='github'), follow_redirects=True)
        assert response.status_code == 200
        assert b'disconnected successfully' in response.data

        # Verify OAuth was removed
        oauth = OAuth.find_by_user_and_provider(user.id, 'github')
        assert oauth is None

    def test_oauth_unbind_last_auth_method(self, client, user_factory, db):
        """Test unbinding last authentication method."""
        user = user_factory(password=None)  # No password set

        # Create OAuth connection (only auth method)
        from toolkit.models.oauth import OAuth
        oauth = OAuth(
            user_id=user.id,
            provider='github',
            provider_user_id='12345'
        )
        db.session.add(oauth)
        db.session.commit()

        # Login via OAuth (simulate)
        from flask_login import login_user
        with client.application.test_request_context():
            login_user(user)

        # Try to unbind - should fail
        response = client.post(url_for('account.oauth_unbind', provider='github'), follow_redirects=True)
        assert response.status_code == 200
        assert b'Cannot remove last authentication method' in response.data

        # Verify OAuth still exists
        oauth = OAuth.find_by_user_and_provider(user.id, 'github')
        assert oauth is not None