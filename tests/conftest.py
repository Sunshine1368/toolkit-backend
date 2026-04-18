import pytest
import os
import sys
from flask import template_rendered
from contextlib import contextmanager
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


@pytest.fixture(scope='session')
def app():
    """Create and configure a Flask app for testing."""
    # Set environment variable before importing config
    os.environ['TEST_DATABASE_URL'] = 'sqlite:///:memory:'

    # Now import after setting environment variable
    from toolkit import create_app, db as _db

    app = create_app('testing')

    # Push application context
    with app.app_context():
        yield app


@pytest.fixture(scope='function')
def db(app):
    """Create and drop database tables for each test."""
    from toolkit import db as _db
    _db.create_all()
    yield _db
    _db.drop_all()
    _db.session.remove()


@pytest.fixture(scope='function')
def client(app, db):
    """Test client."""
    with app.test_client() as client:
        yield client


@pytest.fixture
def runner(app):
    """CLI test runner."""
    return app.test_cli_runner()


@contextmanager
def captured_templates(app):
    """Capture templates rendered during request."""
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append((template, context))

    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)


@pytest.fixture
def captured_templates_fixture(app):
    """Fixture for captured templates."""
    with captured_templates(app) as templates:
        yield templates


# Form test helper
@pytest.fixture(autouse=True)
def app_context_for_forms(app):
    """Automatically provide app context for form tests."""
    # This fixture is automatically used by all tests
    # but we need to be careful about side effects
    # For now, we'll let tests manage their own contexts
    pass

# Model factories
@pytest.fixture
def user_factory(db):
    """Factory for creating test users."""
    from toolkit.models.user import User, UserSettings
    from werkzeug.security import generate_password_hash

    def create_user(username='testuser', email='test@example.com', password='password123', **kwargs):
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            **kwargs
        )
        settings = UserSettings(user=user)
        db.session.add(user)
        db.session.add(settings)
        db.session.commit()
        return user

    return create_user


@pytest.fixture
def oauth_factory(db):
    """Factory for creating OAuth connections."""
    from toolkit.models.oauth import OAuth

    def create_oauth(user_id, provider='github', provider_user_id='12345', **kwargs):
        oauth = OAuth(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            **kwargs
        )
        db.session.add(oauth)
        db.session.commit()
        return oauth

    return create_oauth