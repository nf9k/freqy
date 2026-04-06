import requests as http_requests

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for, current_app
from flask_login import current_user, login_required, login_user, logout_user
from flask_mail import Message

from .. import mail
from ..auth import (User, check_password, hash_password, consume_reset_token,
                    create_reset_token, verify_reset_token)
from ..db import dict_cursor, get_db

bp = Blueprint('auth', __name__)


def _verify_hcaptcha():
    """Return True if hCaptcha passes or is not configured."""
    secret = current_app.config.get('HCAPTCHA_SECRET_KEY', '')
    if not secret:
        return True
    token = request.form.get('h-captcha-response', '')
    if not token:
        return False
    try:
        resp = http_requests.post(
            'https://hcaptcha.com/siteverify',
            data={'secret': secret, 'response': token},
            timeout=5,
        )
        return resp.json().get('success', False)
    except Exception:
        return False


@bp.route('/zip-lookup/<zip_code>')
def zip_lookup(zip_code):
    """Return distinct city/state matches for a zip code from local FCC data."""
    zip_code = zip_code.strip()[:10]
    conn = get_db()
    cur  = dict_cursor(conn)
    cur.execute('''
        SELECT DISTINCT city, state
        FROM fcc_licenses
        WHERE zip = %s AND city IS NOT NULL AND state IS NOT NULL
        ORDER BY city
        LIMIT 5
    ''', (zip_code,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{'city': r['city'].title(), 'state': r['state'].upper()} for r in rows])


@bp.route('/callsign-lookup/<callsign>')
def callsign_lookup(callsign):
    """Public FCC callsign lookup — data is from public FCC database."""
    from ..db import dict_cursor, get_db
    conn = get_db()
    cur  = dict_cursor(conn)
    cur.execute('SELECT * FROM fcc_licenses WHERE callsign = %s', (callsign.strip().upper(),))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return jsonify({'found': False})
    if row.get('updated_at'):
        row['updated_at'] = str(row['updated_at'])
    return jsonify({'found': True, **row})


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        if not _verify_hcaptcha():
            flash('Human verification failed. Please try again.', 'danger')
            return render_template('auth/register.html')

        callsign = request.form.get('callsign', '').strip().upper()
        email    = request.form.get('email', '').strip()
        pw       = request.form.get('password', '')
        pw2      = request.form.get('confirm_password', '')
        fname    = request.form.get('fname', '').strip() or None
        lname    = request.form.get('lname', '').strip() or None

        if not callsign:
            flash('Callsign is required.', 'danger')
            return render_template('auth/register.html')
        if not email:
            flash('Email address is required.', 'danger')
            return render_template('auth/register.html')
        if len(pw) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('auth/register.html')
        if pw != pw2:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        conn = get_db()
        cur  = dict_cursor(conn)
        cur.execute('SELECT id FROM users WHERE callsign = %s', (callsign,))
        if cur.fetchone():
            cur.close()
            conn.close()
            flash(f'Callsign {callsign} is already registered.', 'danger')
            return render_template('auth/register.html')

        cur.execute('''
            INSERT INTO users (callsign, email, password_hash, fname, lname)
            VALUES (%s, %s, %s, %s, %s)
        ''', (callsign, email, hash_password(pw), fname, lname))
        conn.commit()
        cur.close()
        conn.close()

        flash('Account created. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pw  = request.form.get('current_password', '')
        new_pw      = request.form.get('new_password', '')
        confirm_pw  = request.form.get('confirm_password', '')

        conn = get_db()
        cur  = dict_cursor(conn)
        cur.execute('SELECT password_hash FROM users WHERE id = %s', (current_user.id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not check_password(current_pw, row['password_hash']):
            flash('Current password is incorrect.', 'danger')
            return render_template('auth/change_password.html')

        if new_pw != confirm_pw:
            flash('New passwords do not match.', 'danger')
            return render_template('auth/change_password.html')

        if len(new_pw) < 8:
            flash('New password must be at least 8 characters.', 'danger')
            return render_template('auth/change_password.html')

        conn = get_db()
        cur  = dict_cursor(conn)
        cur.execute(
            'UPDATE users SET password_hash = %s WHERE id = %s',
            (hash_password(new_pw), current_user.id)
        )
        conn.commit()
        cur.close()
        conn.close()

        flash('Password updated successfully.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/change_password.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        if not _verify_hcaptcha():
            flash('Human verification failed. Please try again.', 'danger')
            return render_template('auth/login.html')

        callsign = request.form.get('callsign', '').upper().strip()
        password = request.form.get('password', '')

        conn = get_db()
        cur  = dict_cursor(conn)
        cur.execute(
            'SELECT id, callsign, email, password_hash, is_admin, totp_enabled, webauthn_enabled FROM users WHERE callsign = %s',
            (callsign,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row and check_password(password, row['password_hash']):
            # If 2FA is enabled, stage the user and redirect to challenge
            if row.get('totp_enabled') or row.get('webauthn_enabled'):
                session['pending_2fa_user_id'] = row['id']
                session['pending_2fa_next'] = request.args.get('next') or url_for('main.dashboard')
                return redirect(url_for('twofa.challenge'))

            user = User(row['id'], row['callsign'], row['email'], row['is_admin'])
            login_user(user, remember=True)
            return redirect(request.args.get('next') or url_for('main.dashboard'))

        flash('Invalid callsign or password.', 'danger')

    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        if not _verify_hcaptcha():
            flash('Human verification failed. Please try again.', 'danger')
            return render_template('auth/forgot_password.html')

        email = request.form.get('email', '').strip()

        conn = get_db()
        cur  = dict_cursor(conn)
        cur.execute('SELECT id, callsign FROM users WHERE email = %s', (email,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            token = create_reset_token(row['id'])
            ok = _send_reset_email(email, row['callsign'], token)
            if not ok:
                flash('Failed to send reset email — please contact an administrator.', 'danger')
                return render_template('auth/forgot_password.html')

        # Always show the same confirmation page — prevents email enumeration
        return render_template('auth/forgot_password_sent.html')

    return render_template('auth/forgot_password.html')


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if verify_reset_token(token) is None:
        flash('That reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        pw  = request.form.get('password', '')
        pw2 = request.form.get('confirm_password', '')

        if pw != pw2:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        if consume_reset_token(token, pw):
            flash('Password updated. Please log in.', 'success')
            return redirect(url_for('auth.login'))

        flash('Reset link is no longer valid.', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)


# ---------- helpers ----------

def _send_reset_email(to_email, callsign, token):
    reset_url = f"{current_app.config['APP_URL']}/reset-password/{token}"
    msg = Message(
        subject='Freqy — Password Reset Request',
        recipients=[to_email],
        body=(
            f"Hello {callsign},\n\n"
            f"Click the link below to reset your Freqy password:\n"
            f"{reset_url}\n\n"
            f"This link expires in 24 hours. If you did not request this, ignore this email.\n\n"
            f"73,\nfreqy by NF9K\n"
        ),
    )
    try:
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error('Failed to send reset email to %s: %s', to_email, e)
        return False
