import pytest
import datetime
import jwt
from toolkit.models.user import User, UserSettings
from toolkit.models.oauth import OAuth
from werkzeug.security import check_password_hash


class TestUserModel:
    """Test User model."""

    def test_create_user(self, db):
        """Test creating a user."""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hash'
        )
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.password_hash == 'hash'
        assert user.display_name is None
        assert user.avatar_url is None
        assert user.bio is None
        assert user.is_admin is False
        assert user.is_active is True
        assert user.email_verified is False
        assert user.last_seen is not None
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_repr(self, db):
        """Test user string representation."""
        user = User(username='test', email='test@example.com', password_hash='hash')
        db.session.add(user)
        db.session.commit()

        assert repr(user) == '<User test>'

    def test_set_password(self):
        """Test password hashing."""
        user = User(username='test', email='test@example.com')
        user.set_password('password123')

        assert user.password_hash is not None
        assert user.password_hash != 'password123'
        assert check_password_hash(user.password_hash, 'password123')
        assert not check_password_hash(user.password_hash, 'wrongpassword')

    def test_check_password(self, db):
        """Test password checking."""
        user = User(username='test', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        assert user.check_password('password123') is True
        assert user.check_password('wrongpassword') is False

    def test_get_reset_password_token(self, app, db):
        """Test password reset token generation."""
        with app.app_context():
            user = User(username='test', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

            token = user.get_reset_password_token()
            assert token is not None

            # Verify token can be decoded
            decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            assert decoded['reset_password'] == user.id
            assert 'exp' in decoded

    def test_verify_reset_password_token_valid(self, app, db):
        """Test valid password reset token verification."""
        with app.app_context():
            user = User(username='test', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

            token = user.get_reset_password_token()
            verified_user = User.verify_reset_password_token(token)

            assert verified_user is not None
            assert verified_user.id == user.id

    def test_verify_reset_password_token_invalid(self, app):
        """Test invalid password reset token verification."""
        with app.app_context():
            # Invalid token
            user = User.verify_reset_password_token('invalid.token.here')
            assert user is None

            # Expired token
            expired_token = jwt.encode(
                {'reset_password': 1, 'exp': datetime.datetime.utcnow() - datetime.timedelta(seconds=1)},
                app.config['SECRET_KEY'],
                algorithm='HS256'
            )
            user = User.verify_reset_password_token(expired_token)
            assert user is None

    def test_to_dict(self, db):
        """Test user dictionary conversion."""
        user = User(
            username='testuser',
            email='test@example.com',
            display_name='Test User',
            avatar_url='http://example.com/avatar.jpg',
            bio='Test bio',
            is_admin=False,
            is_active=True
        )
        user.set_password('password')
        db.session.add(user)
        db.session.commit()

        user_dict = user.to_dict()

        assert user_dict['id'] == user.id
        assert user_dict['username'] == 'testuser'
        assert user_dict['email'] == 'test@example.com'
        assert user_dict['display_name'] == 'Test User'
        assert user_dict['avatar_url'] == 'http://example.com/avatar.jpg'
        assert user_dict['bio'] == 'Test bio'
        assert user_dict['is_admin'] is False
        assert user_dict['is_active'] is True
        assert 'last_seen' in user_dict
        assert 'created_at' in user_dict

    def test_ping(self, db):
        """Test last_seen update."""
        user = User(username='test', email='test@example.com', password_hash='hash')
        db.session.add(user)
        db.session.commit()

        original_last_seen = user.last_seen

        # Wait a moment to ensure time difference
        import time
        time.sleep(0.01)

        user.ping()
        db.session.commit()

        assert user.last_seen > original_last_seen

    def test_user_relationships(self, db):
        """Test user relationships."""
        user = User(username='test', email='test@example.com', password_hash='hash')
        db.session.add(user)
        db.session.commit()

        # Check settings relationship
        settings = UserSettings(user_id=user.id)
        db.session.add(settings)
        db.session.commit()

        assert user.settings is not None
        assert user.settings.user_id == user.id
        assert user.settings.user == user


class TestUserSettingsModel:
    """Test UserSettings model."""

    def test_create_user_settings(self, db):
        """Test creating user settings."""
        user = User(username='test', email='test@example.com', password_hash='hash')
        db.session.add(user)
        db.session.commit()

        settings = UserSettings(
            user_id=user.id,
            theme='dark',
            language='zh',
            timezone='Asia/Shanghai',
            email_notifications=False,
            push_notifications=True,
            two_factor_enabled=True,
            two_factor_secret='secret123'
        )
        db.session.add(settings)
        db.session.commit()

        assert settings.id is not None
        assert settings.user_id == user.id
        assert settings.theme == 'dark'
        assert settings.language == 'zh'
        assert settings.timezone == 'Asia/Shanghai'
        assert settings.email_notifications is False
        assert settings.push_notifications is True
        assert settings.two_factor_enabled is True
        assert settings.two_factor_secret == 'secret123'
        assert settings.created_at is not None
        assert settings.updated_at is not None

    def test_user_settings_repr(self, db):
        """Test user settings string representation."""
        user = User(username='test', email='test@example.com', password_hash='hash')
        db.session.add(user)
        db.session.commit()

        settings = UserSettings(user_id=user.id)
        db.session.add(settings)
        db.session.commit()

        assert repr(settings) == f'<UserSettings user_id={user.id}>'

    def test_user_settings_relationship(self, db):
        """Test user settings relationship with user."""
        user = User(username='test', email='test@example.com', password_hash='hash')
        settings = UserSettings(user=user)
        db.session.add(user)
        db.session.add(settings)
        db.session.commit()

        assert user.settings == settings
        assert settings.user == user


class TestOAuthModel:
    """Test OAuth model."""

    def test_create_oauth(self, db, user_factory):
        """Test creating OAuth connection."""
        user = user_factory()

        oauth = OAuth(
            user_id=user.id,
            provider='github',
            provider_user_id='12345',
            access_token='access_token_123',
            refresh_token='refresh_token_123',
            token_expires=datetime.datetime.utcnow() + datetime.timedelta(hours=1),
            profile_data={'login': 'testuser', 'avatar_url': 'http://example.com/avatar.jpg'}
        )
        db.session.add(oauth)
        db.session.commit()

        assert oauth.id is not None
        assert oauth.user_id == user.id
        assert oauth.provider == 'github'
        assert oauth.provider_user_id == '12345'
        assert oauth.access_token == 'access_token_123'
        assert oauth.refresh_token == 'refresh_token_123'
        assert oauth.token_expires is not None
        assert oauth.profile_data['login'] == 'testuser'
        assert oauth.created_at is not None
        assert oauth.updated_at is not None

    def test_oauth_repr(self, db, user_factory):
        """Test OAuth string representation."""
        user = user_factory()
        oauth = OAuth(user_id=user.id, provider='github', provider_user_id='12345')
        db.session.add(oauth)
        db.session.commit()

        assert repr(oauth) == f'<OAuth github:12345 for user {user.id}>'

    def test_oauth_to_dict(self, db, user_factory):
        """Test OAuth dictionary conversion."""
        user = user_factory()
        oauth = OAuth(user_id=user.id, provider='github', provider_user_id='12345')
        db.session.add(oauth)
        db.session.commit()

        oauth_dict = oauth.to_dict()

        assert oauth_dict['id'] == oauth.id
        assert oauth_dict['provider'] == 'github'
        assert oauth_dict['provider_user_id'] == '12345'
        assert 'created_at' in oauth_dict
        assert 'updated_at' in oauth_dict

    def test_find_by_provider_user_id(self, db, user_factory):
        """Test finding OAuth by provider and provider user ID."""
        user = user_factory()
        oauth = OAuth(user_id=user.id, provider='github', provider_user_id='12345')
        db.session.add(oauth)
        db.session.commit()

        found = OAuth.find_by_provider_user_id('github', '12345')
        assert found is not None
        assert found.id == oauth.id
        assert found.user_id == user.id

        # Not found
        not_found = OAuth.find_by_provider_user_id('github', '99999')
        assert not_found is None

    def test_find_by_user_and_provider(self, db, user_factory):
        """Test finding OAuth by user ID and provider."""
        user = user_factory()
        oauth = OAuth(user_id=user.id, provider='github', provider_user_id='12345')
        db.session.add(oauth)
        db.session.commit()

        found = OAuth.find_by_user_and_provider(user.id, 'github')
        assert found is not None
        assert found.id == oauth.id
        assert found.provider_user_id == '12345'

        # Not found
        not_found = OAuth.find_by_user_and_provider(user.id, 'google')
        assert not_found is None

    def test_create_or_update_new(self, db, user_factory):
        """Test create_or_update for new connection."""
        user = user_factory()

        oauth = OAuth.create_or_update(
            user_id=user.id,
            provider='github',
            provider_user_id='12345',
            access_token='token123',
            profile_data={'login': 'test'}
        )

        assert oauth is not None
        assert oauth.user_id == user.id
        assert oauth.provider == 'github'
        assert oauth.provider_user_id == '12345'
        assert oauth.access_token == 'token123'
        assert oauth.profile_data['login'] == 'test'

        # Verify it was saved
        found = OAuth.query.filter_by(user_id=user.id, provider='github').first()
        assert found is not None
        assert found.id == oauth.id

    def test_create_or_update_existing(self, db, user_factory):
        """Test create_or_update for existing connection."""
        user = user_factory()

        # Create initial connection
        oauth1 = OAuth.create_or_update(
            user_id=user.id,
            provider='github',
            provider_user_id='12345',
            access_token='old_token',
            profile_data={'login': 'old'}
        )

        original_id = oauth1.id
        original_created_at = oauth1.created_at

        # Update connection
        oauth2 = OAuth.create_or_update(
            user_id=user.id,
            provider='github',
            provider_user_id='12345',
            access_token='new_token',
            profile_data={'login': 'new'}
        )

        assert oauth2.id == original_id  # Same record
        assert oauth2.created_at == original_created_at  # Created_at unchanged
        assert oauth2.access_token == 'new_token'  # Updated
        assert oauth2.profile_data['login'] == 'new'  # Updated
        assert oauth2.updated_at > original_created_at  # Updated_at changed

    def test_unique_constraints(self, db, user_factory):
        """Test OAuth unique constraints."""
        user1 = user_factory(username='user1')
        user2 = user_factory(username='user2')

        # Same provider + provider_user_id should be unique
        oauth1 = OAuth(user_id=user1.id, provider='github', provider_user_id='12345')
        db.session.add(oauth1)
        db.session.commit()

        # Attempt to create another with same provider + provider_user_id
        oauth2 = OAuth(user_id=user2.id, provider='github', provider_user_id='12345')
        db.session.add(oauth2)

        with pytest.raises(Exception):  # Should raise integrity error
            db.session.commit()
        db.session.rollback()

        # Same user + provider should be unique
        oauth3 = OAuth(user_id=user1.id, provider='github', provider_user_id='67890')
        db.session.add(oauth3)
        db.session.commit()

        # Attempt to create another with same user + provider
        oauth4 = OAuth(user_id=user1.id, provider='github', provider_user_id='99999')
        db.session.add(oauth4)

        with pytest.raises(Exception):
            db.session.commit()