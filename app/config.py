import os
import urllib.parse

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-me')
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours

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
