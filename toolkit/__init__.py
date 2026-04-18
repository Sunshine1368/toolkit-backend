import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
import redis
from elasticsearch import Elasticsearch

# Extensions
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
socketio = SocketIO()
csrf = CSRFProtect()
cors = CORS()

# Redis client
redis_client = None

# Elasticsearch client
es = None


def create_app(config_name=None):
    """Application factory function."""
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    from config import config
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    socketio.init_app(app, message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'])
    csrf.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])

    # Initialize Redis client
    global redis_client
    redis_client = redis.from_url(app.config['REDIS_URL'])

    # Initialize Elasticsearch client
    global es
    es = Elasticsearch([app.config['ELASTICSEARCH_URL']])

    # Setup login manager
    login.login_view = 'account.login'
    login.login_message = 'Please log in to access this page.'
    login.login_message_category = 'info'

    # Register blueprints
    from .blueprints.www import bp as www_bp
    from .blueprints.account import bp as account_bp
    from .blueprints.settings import bp as settings_bp
    from .blueprints.notice import bp as notice_bp
    from .blueprints.contacts import bp as contacts_bp
    from .blueprints.chat import bp as chat_bp

    app.register_blueprint(www_bp, subdomain='www')
    app.register_blueprint(account_bp, subdomain='account')
    app.register_blueprint(settings_bp, subdomain='settings')
    app.register_blueprint(notice_bp, subdomain='notice')
    app.register_blueprint(contacts_bp, subdomain='contacts')
    app.register_blueprint(chat_bp, subdomain='chat')

    # Register error handlers
    register_error_handlers(app)

    # Register CLI commands
    register_commands(app)

    # Register context processors
    register_context_processors(app)

    return app


def register_error_handlers(app):
    """Register error handlers."""
    from flask import render_template

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403


def register_commands(app):
    """Register CLI commands."""
    @app.cli.command('init-db')
    def init_db():
        """Initialize the database."""
        db.create_all()
        print('Database initialized.')

    @app.cli.command('create-admin')
    def create_admin():
        """Create an admin user."""
        from .models.user import User
        from werkzeug.security import generate_password_hash

        admin = User(
            username='admin',
            email='admin@toolkit.uno',
            password_hash=generate_password_hash('admin123'),
            is_admin=True,
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print('Admin user created.')


def register_context_processors(app):
    """Register context processors."""
    @app.context_processor
    def inject_global_variables():
        from flask import request
        return {
            'current_subdomain': request.host.split('.')[0] if '.' in request.host else 'www'
        }