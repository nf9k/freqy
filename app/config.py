import json
import os
import urllib.parse

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'dev-secret-change-me'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.getenv('APP_URL', '').startswith('https')

    DB_HOST     = os.getenv('DB_HOST', 'db')
    DB_NAME     = os.getenv('DB_NAME', 'freqy')
    DB_USER     = os.getenv('DB_USER', 'freqy_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    MAIL_SERVER         = os.getenv('SMTP_HOST', 'mail.smtp2go.com')
    MAIL_PORT           = int(os.getenv('SMTP_PORT', 587))
    # Port 465 = implicit SSL; 587/2525 = STARTTLS
    MAIL_USE_SSL        = int(os.getenv('SMTP_PORT', 587)) == 465
    MAIL_USE_TLS        = int(os.getenv('SMTP_PORT', 587)) != 465
    MAIL_USERNAME       = os.getenv('SMTP_USER', '')
    MAIL_PASSWORD       = os.getenv('SMTP_PASSWORD', '')
    MAIL_DEFAULT_SENDER = (
        os.getenv('SMTP_FROM_NAME', 'freqy'),
        os.getenv('SMTP_FROM_EMAIL', 'noreply@example.com'),
    )

    APP_URL             = os.getenv('APP_URL', 'http://localhost:5000')
    ADMIN_NOTIFY_EMAILS = [
        e.strip() for e in os.getenv('ADMIN_NOTIFY_EMAILS', '').split(',') if e.strip()
    ]

    _parsed_url     = urllib.parse.urlparse(os.getenv('APP_URL', 'http://localhost:5000'))
    WEBAUTHN_RP_ID  = _parsed_url.hostname or 'localhost'
    WEBAUTHN_ORIGIN = os.getenv('APP_URL', 'http://localhost:5000')

    HCAPTCHA_SITE_KEY   = os.getenv('HCAPTCHA_SITE_KEY', '')
    HCAPTCHA_SECRET_KEY = os.getenv('HCAPTCHA_SECRET_KEY', '')

    NOPC_EMAIL_TO = [
        e.strip() for e in os.getenv('NOPC_EMAIL_TO', '').split(',') if e.strip()
    ]
    NOPC_EMAIL_FROM = [
        e.strip() for e in os.getenv('NOPC_EMAIL_FROM', '').split(',') if e.strip()
    ]

    EXPORT_TITLE = os.getenv('EXPORT_TITLE', 'Frequency Coordination Database Export as of {date}')

    ACTIVITY_CHECK_DAYS = int(os.getenv('ACTIVITY_CHECK_DAYS', '365'))

    DEMO_MODE         = os.getenv('DEMO_MODE', 'false').lower() == 'true'
    DEMO_RESET_TOKEN  = os.getenv('DEMO_RESET_TOKEN', '')

    FREQ_CO_CHANNEL_MILES = json.loads(os.getenv('FREQ_CO_CHANNEL_MILES', json.dumps({
        '50':   120,
        '144':  120,
        '222':  120,
        '440':  120,
        '902':  120,
        '1296': 120,
    })))
    FREQ_ADJ_RULES = json.loads(os.getenv('FREQ_ADJ_RULES', json.dumps({
        '50':   [[20, 20]],
        '144':  [[10, 40], [15, 30], [20, 25], [30, 20]],
        '222':  [[20, 25], [40, 5]],
        '440':  [[25, 5],  [50, 1]],
        '902':  [[25, 5],  [50, 1]],
        '1296': [[25, 5],  [50, 1]],
    })))
