from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail

from .config import Config

mail = Mail()


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
    @app.context_processor
    def inject_globals():
        return {
            'app_version':       os.environ.get('APP_VERSION', 'dev'),
            'hcaptcha_site_key': app.config.get('HCAPTCHA_SITE_KEY', ''),
        }

    # Extensions
    from .auth import login_manager
    login_manager.init_app(app)
    mail.init_app(app)

    # Blueprints
    from .routes.auth import bp as auth_bp
    from .routes.main import bp as main_bp
    from .routes.records import bp as records_bp
    from .routes.profile import bp as profile_bp
    from .routes.admin import bp as admin_bp
    from .routes.twofa import bp as twofa_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(records_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(twofa_bp)

    return app
