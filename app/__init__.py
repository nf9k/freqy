from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect

from .config import Config

mail = Mail()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=[])


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config)

    @app.template_filter('date')
    def format_date(value):
        if not value:
            return '—'
        from datetime import date, datetime
        if isinstance(value, (date, datetime)):
            return value.strftime('%m/%d/%Y')
        # string fallback — try parsing YYYY-MM-DD
        try:
            return datetime.strptime(str(value), '%Y-%m-%d').strftime('%m/%d/%Y')
        except ValueError:
            return str(value)

    @app.template_filter('dateinput')
    def format_date_input(value):
        """Like |date but returns '' instead of '—' for use in form inputs."""
        if not value:
            return ''
        from datetime import date, datetime
        if isinstance(value, (date, datetime)):
            return value.strftime('%m/%d/%Y')
        try:
            return datetime.strptime(str(value), '%Y-%m-%d').strftime('%m/%d/%Y')
        except ValueError:
            return str(value)

    @app.template_filter('datetime')
    def format_datetime(value):
        if not value:
            return '—'
        from datetime import datetime
        if isinstance(value, datetime):
            return value.strftime('%m/%d/%Y %H%M')
        try:
            return datetime.strptime(str(value), '%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y %H%M')
        except ValueError:
            return str(value)

    @app.template_filter('format_freq')
    def format_freq(value, band):
        if value is None:
            return '—'
        places = 4 if band == 'GHZ' else 3
        return f'{value:.{places}f}'

    import os
    from .license import verify_license
    _license = verify_license()

    @app.context_processor
    def inject_globals():
        ver = os.environ.get('_FREQY_VERSION', 'dev')
        return {
            'app_version':       ver + ('+' if _license else ''),
            'hcaptcha_site_key': app.config.get('HCAPTCHA_SITE_KEY', ''),
            'demo_mode':         app.config.get('DEMO_MODE', False),
            'license':           _license,
        }

    # Extensions
    from .auth import login_manager
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    if app.config.get('DEMO_MODE'):
        mail.send = lambda msg: app.logger.debug('Demo mode: suppressed email to %s', msg.recipients)

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    # Blueprints
    from .routes.auth import bp as auth_bp
    from .routes.main import bp as main_bp
    from .routes.records import bp as records_bp
    from .routes.profile import bp as profile_bp
    from .routes.admin import bp as admin_bp
    from .routes.twofa import bp as twofa_bp
    from .routes.demo import bp as demo_bp
    from .routes.directory import bp as directory_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(records_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(twofa_bp)
    app.register_blueprint(demo_bp)
    app.register_blueprint(directory_bp)

    return app
