from flask import Blueprint, render_template, current_app

bp = Blueprint('www', __name__)


@bp.route('/')
def index():
    """Home page."""
    return render_template('www/index.html')


@bp.route('/about')
def about():
    """About page."""
    return render_template('www/about.html')


@bp.route('/features')
def features():
    """Features page."""
    return render_template('www/features.html')


@bp.route('/pricing')
def pricing():
    """Pricing page."""
    return render_template('www/pricing.html')


@bp.route('/contact')
def contact():
    """Contact page."""
    return render_template('www/contact.html')


@bp.route('/status')
def status():
    """System status page."""
    # Check database connection
    db_status = 'ok'
    try:
        current_app.db.session.execute('SELECT 1')
    except Exception as e:
        db_status = f'error: {str(e)}'

    # Check Redis connection
    redis_status = 'ok'
    try:
        current_app.redis_client.ping()
    except Exception as e:
        redis_status = f'error: {str(e)}'

    # Check Elasticsearch connection
    es_status = 'ok'
    try:
        current_app.es.ping()
    except Exception as e:
        es_status = f'error: {str(e)}'

    return {
        'database': db_status,
        'redis': redis_status,
        'elasticsearch': es_status,
        'status': 'operational' if all(s == 'ok' for s in [db_status, redis_status, es_status]) else 'degraded'
    }