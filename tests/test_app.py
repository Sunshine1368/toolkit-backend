import pytest
from flask import current_app, url_for
from toolkit import create_app, db, login, socketio, csrf, cors
from config import DevelopmentConfig, TestingConfig, ProductionConfig


class TestAppFactory:
    """Test application factory and configuration."""

    def test_create_app_default(self):
        """Test creating app with default config."""
        app = create_app()
        assert app is not None
        assert app.config['DEBUG'] is True
        assert app.config['TESTING'] is False

    def test_create_app_testing(self):
        """Test creating app with testing config."""
        app = create_app('testing')
        assert app is not None
        assert app.config['TESTING'] is True
        assert app.config['WTF_CSRF_ENABLED'] is False

    def test_create_app_production(self):
        """Test creating app with production config."""
        app = create_app('production')
        assert app is not None
        assert app.config['DEBUG'] is False
        assert app.config['TESTING'] is False

    def test_extensions_initialized(self, app):
        """Test that all extensions are initialized."""
        assert 'sqlalchemy' in app.extensions
        # Flask-Login sets app.login_manager
        assert hasattr(app, 'login_manager')
        assert socketio.server is not None
        # Flask-WTF CSRF registers in extensions
        assert 'csrf' in app.extensions
        # Flask-CORS is initialized but may not register in extensions
        # Check that CORS configuration is set
        assert 'CORS_ORIGINS' in app.config

    def test_blueprints_registered(self, app):
        """Test that all blueprints are registered."""
        blueprints = set(app.blueprints.keys())
        expected = {'www', 'account', 'settings', 'notice', 'contacts', 'chat'}
        assert expected.issubset(blueprints)

    def test_subdomain_routing(self, app):
        """Test that blueprints are registered with correct subdomains."""
        # This is a basic check; actual subdomain routing requires SERVER_NAME config
        with app.app_context():
            # Check that account blueprint routes exist
            # With subdomain routing, URLs include subdomain
            login_url = url_for('account.login')
            register_url = url_for('account.register')
            assert login_url.endswith('/login')
            assert register_url.endswith('/register')
            # Verify subdomain is included
            assert 'account.localhost' in login_url
            assert 'account.localhost' in register_url


class TestErrorHandlers:
    """Test error handlers."""

    def test_404_handler(self, client):
        """Test 404 error handler."""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        # Check that custom error page is served
        assert b'Page Not Found' in response.data or b'404' in response.data

    def test_500_handler(self):
        """Test 500 error handler."""
        # Create a fresh app for this test to avoid route addition conflicts
        from toolkit import create_app
        app = create_app('testing')
        # Disable TESTING mode to allow error handler to catch exceptions
        app.config['TESTING'] = False
        app.config['PROPAGATE_EXCEPTIONS'] = False

        # Create a route that raises an exception
        @app.route('/test-500')
        def test_500():
            raise Exception('Test exception')

        with app.test_client() as client:
            response = client.get('/test-500')
            assert response.status_code == 500
            # Error page should contain some indication of error
            assert len(response.data) > 0

    def test_403_handler(self, client):
        """Test 403 error handler."""
        # TODO: Implement when authentication is tested
        pass


class TestCliCommands:
    """Test CLI commands."""

    def test_init_db_command(self, runner, db):
        """Test init-db command."""
        # Tables should already be created by db fixture
        result = runner.invoke(args=['init-db'])
        assert result.exit_code == 0
        assert 'Database initialized' in result.output

    def test_create_admin_command(self, runner, db):
        """Test create-admin command."""
        from toolkit.models.user import User

        # Check no admin exists initially
        admin = User.query.filter_by(username='admin').first()
        assert admin is None

        result = runner.invoke(args=['create-admin'])
        assert result.exit_code == 0
        assert 'Admin user created' in result.output

        # Verify admin was created
        admin = User.query.filter_by(username='admin').first()
        assert admin is not None
        assert admin.email == 'admin@toolkit.uno'
        assert admin.is_admin is True


class TestConfigurations:
    """Test configuration classes."""

    def test_development_config(self):
        """Test development configuration."""
        config = DevelopmentConfig()
        assert config.DEBUG is True
        assert config.SQLALCHEMY_ECHO is True
        assert config.WTF_CSRF_ENABLED is True

    def test_testing_config(self):
        """Test testing configuration."""
        config = TestingConfig()
        assert config.TESTING is True
        assert config.WTF_CSRF_ENABLED is False
        assert 'sqlite' in config.SQLALCHEMY_DATABASE_URI.lower()

    def test_production_config(self):
        """Test production configuration."""
        config = ProductionConfig()
        assert config.DEBUG is False
        assert config.TESTING is False
        assert config.WTF_CSRF_ENABLED is True