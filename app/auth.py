import secrets
from datetime import datetime, timedelta
from functools import wraps

import bcrypt
from flask import flash, redirect, url_for
from flask_login import LoginManager, UserMixin, current_user

from .db import get_db, dict_cursor

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'


class User(UserMixin):
    def __init__(self, id, callsign, email, is_admin):
        self.id       = id
        self.callsign = callsign
        self.email    = email
        self.is_admin = bool(is_admin)

    # Flask-Login uses str(user.id) for session cookie
    def get_id(self):
        return str(self.id)


@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cur  = dict_cursor(conn)
    cur.execute(
        'SELECT id, callsign, email, is_admin FROM users WHERE id = %s',
        (user_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        return None
    return User(row['id'], row['callsign'], row['email'], row['is_admin'])


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin privileges required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


# ---------- password helpers ----------

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ---------- reset token helpers ----------

def create_reset_token(user_id):
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=24)
    conn = get_db()
    cur  = dict_cursor(conn)
    cur.execute(
        'INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)',
        (user_id, token, expires_at)
    )
    conn.commit()
    cur.close()
    conn.close()
    return token


def verify_reset_token(token):
    conn = get_db()
    cur  = dict_cursor(conn)
    cur.execute(
        '''SELECT user_id FROM password_reset_tokens
           WHERE token = %s AND expires_at > NOW() AND used = 0''',
        (token,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row['user_id'] if row else None


def consume_reset_token(token, new_password):
    user_id = verify_reset_token(token)
    if user_id is None:
        return False
    pw_hash = hash_password(new_password)
    conn = get_db()
    cur  = dict_cursor(conn)
    cur.execute('UPDATE users SET password_hash = %s WHERE id = %s', (pw_hash, user_id))
    cur.execute('UPDATE password_reset_tokens SET used = 1 WHERE token = %s', (token,))
    conn.commit()
    cur.close()
    conn.close()
    return True
