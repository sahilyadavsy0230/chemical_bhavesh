# ============================================================
# app/__init__.py - Application Factory
# AI-Based Chemical Process Equipment Design Platform
# ============================================================

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import config

# ─── Extension Instances ─────────────────────────────────────
# These are initialised *without* an app; bound later in create_app()
db          = SQLAlchemy()
migrate     = Migrate()
login_manager = LoginManager()
csrf        = CSRFProtect()
limiter     = Limiter(key_func=get_remote_address)


def create_app(config_name: str = 'default') -> Flask:
    """
    Application factory.

    Args:
        config_name: One of 'development', 'testing', 'production', 'default'.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    # ── Load configuration ────────────────────────────────────
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # ── Bind extensions ───────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    CORS(app, resources={r'/api/*': {'origins': '*'}})
    limiter.init_app(app)

    # ── Flask-Login setup ─────────────────────────────────────
    login_manager.init_app(app)
    login_manager.login_view       = 'auth.login'
    login_manager.login_message    = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))

    # ── Register Blueprints ───────────────────────────────────
    _register_blueprints(app)

    # ── Register template filters / context processors ────────
    _register_template_helpers(app)

    # ── Register error handlers ───────────────────────────────
    _register_error_handlers(app)

    return app


# ─── Private Helpers ─────────────────────────────────────────

def _register_blueprints(app: Flask) -> None:
    """Import and register all Blueprints."""

    from app.routes.auth       import auth_bp
    from app.routes.dashboard  import dashboard_bp
    from app.routes.equipment  import equipment_bp
    from app.routes.api        import api_bp
    from app.routes.reports    import reports_bp
    from app.routes.admin      import admin_bp
    from app.routes.profile    import profile_bp

    app.register_blueprint(auth_bp,      url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(equipment_bp, url_prefix='/equipment')
    app.register_blueprint(api_bp,       url_prefix='/api/v1')
    app.register_blueprint(reports_bp,   url_prefix='/reports')
    app.register_blueprint(admin_bp,     url_prefix='/admin')
    app.register_blueprint(profile_bp,   url_prefix='/profile')


def _register_template_helpers(app: Flask) -> None:
    """Register Jinja2 filters and context processors."""

    import datetime

    @app.template_filter('datetime_format')
    def datetime_format(value, fmt='%d %b %Y, %H:%M'):
        if value is None:
            return '-'
        return value.strftime(fmt)

    @app.template_filter('round2')
    def round2(value):
        try:
            return round(float(value), 2)
        except (TypeError, ValueError):
            return value

    @app.context_processor
    def inject_globals():
        return {
            'app_name':    app.config['APP_NAME'],
            'app_version': app.config['APP_VERSION'],
            'now':         datetime.datetime.utcnow(),
        }


def _register_error_handlers(app: Flask) -> None:
    """Register HTTP error handlers."""

    from flask import render_template

    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html', error=e), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html', error=e), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html', error=e), 404

    @app.errorhandler(429)
    def rate_limited(e):
        return render_template('errors/429.html', error=e), 429

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('errors/500.html', error=e), 500
