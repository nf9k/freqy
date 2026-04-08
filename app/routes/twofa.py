import json

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, send_file, session, url_for)
from flask_login import current_user, login_required, login_user
import io

from .. import limiter
from ..auth import User, check_password
from ..db import dict_cursor, get_db
from ..twofa import (
    delete_webauthn_credential,
    generate_backup_codes,
    generate_qr_png,
    generate_totp_secret,
    get_totp_uri,
    get_webauthn_credentials,
    unused_backup_code_count,
    verify_backup_code,
    verify_totp,
    webauthn_begin_authentication,
    webauthn_begin_registration,
    webauthn_complete_authentication,
    webauthn_complete_registration,
)

bp = Blueprint('twofa', __name__, url_prefix='/2fa')


# ---------------------------------------------------------------
# Challenge (step 2 of login)
# ---------------------------------------------------------------

@bp.route('/challenge', methods=['GET', 'POST'])
@limiter.limit('10 per minute', methods=['POST'])
def challenge():
    user_id = session.get('pending_2fa_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute(
        'SELECT id, callsign, email, is_admin, totp_secret, totp_enabled, webauthn_enabled '
        'FROM users WHERE id = %s',
        (user_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        session.pop('pending_2fa_user_id', None)
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        if not code:
            flash('Please enter your verification code.', 'danger')
            return render_template('twofa/challenge.html', row=row)

        # Try TOTP (6 digits)
        if row['totp_enabled'] and row['totp_secret'] and len(code) == 6 and code.isdigit():
            if verify_totp(row['totp_secret'], code):
                return _complete_challenge(row)
            flash('Invalid code. Please try again.', 'danger')
            return render_template('twofa/challenge.html', row=row)

        # Try backup code (anything that isn't 6 plain digits)
        if verify_backup_code(user_id, code):
            remaining = unused_backup_code_count(user_id)
            _complete_challenge(row)  # log in first
            user = User(row['id'], row['callsign'], row['email'], row['is_admin'])
            login_user(user, remember=True)
            next_url = session.pop('pending_2fa_next', url_for('main.dashboard'))
            session.pop('pending_2fa_user_id', None)
            if remaining <= 2:
                flash(
                    f'Backup code accepted. You have {remaining} code(s) remaining — '
                    'consider regenerating them in your security settings.',
                    'warning',
                )
            else:
                flash('Backup code accepted.', 'success')
            return redirect(next_url)

        flash('Invalid code. Please try again.', 'danger')

    return render_template('twofa/challenge.html', row=row)


def _complete_challenge(row):
    user = User(row['id'], row['callsign'], row['email'], row['is_admin'])
    login_user(user, remember=True)
    next_url = session.pop('pending_2fa_next', url_for('main.dashboard'))
    session.pop('pending_2fa_user_id', None)
    return redirect(next_url)


# ---------------------------------------------------------------
# WebAuthn authentication (AJAX, called from challenge page)
# ---------------------------------------------------------------

@bp.route('/webauthn/authenticate/begin', methods=['POST'])
def webauthn_auth_begin():
    user_id = session.get('pending_2fa_user_id')
    if not user_id:
        return jsonify({'error': 'No pending login'}), 400
    options_json, challenge_b64 = webauthn_begin_authentication(current_app._get_current_object(), user_id)
    session['webauthn_auth_challenge'] = challenge_b64
    return options_json, 200, {'Content-Type': 'application/json'}


@bp.route('/webauthn/authenticate/complete', methods=['POST'])
def webauthn_auth_complete():
    user_id = session.get('pending_2fa_user_id')
    challenge_b64 = session.pop('webauthn_auth_challenge', None)
    if not user_id or not challenge_b64:
        return jsonify({'success': False, 'message': 'Session expired'}), 400

    try:
        verified_user_id = webauthn_complete_authentication(
            current_app._get_current_object(),
            challenge_b64,
            request.get_json(force=True),
        )
    except Exception as e:
        current_app.logger.warning('WebAuthn authentication failed: %s', e)
        return jsonify({'success': False, 'message': 'Security key verification failed'}), 400

    if verified_user_id != user_id:
        return jsonify({'success': False, 'message': 'Key does not match account'}), 400

    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute('SELECT id, callsign, email, is_admin FROM users WHERE id = %s', (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    next_url = session.pop('pending_2fa_next', url_for('main.dashboard'))
    session.pop('pending_2fa_user_id', None)
    user = User(row['id'], row['callsign'], row['email'], row['is_admin'])
    login_user(user, remember=True)
    return jsonify({'success': True, 'redirect': next_url})


# ---------------------------------------------------------------
# TOTP setup
# ---------------------------------------------------------------

@bp.route('/setup/totp', methods=['GET', 'POST'])
@login_required
def setup_totp():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'generate':
            secret = generate_totp_secret()
            session['totp_pending_secret'] = secret
            return render_template('twofa/setup_totp.html', secret=secret,
                                   uri=get_totp_uri(secret, current_user.callsign))

        if action == 'verify':
            secret = session.get('totp_pending_secret')
            code = request.form.get('code', '').strip()
            if not secret:
                flash('Session expired — please start over.', 'danger')
                return render_template('twofa/setup_totp.html')
            if not verify_totp(secret, code):
                flash('Incorrect code. Scan the QR code and try again.', 'danger')
                return render_template('twofa/setup_totp.html', secret=secret,
                                       uri=get_totp_uri(secret, current_user.callsign))
            # Enable TOTP
            conn = get_db()
            cur = dict_cursor(conn)
            cur.execute(
                'UPDATE users SET totp_secret = %s, totp_enabled = 1 WHERE id = %s',
                (secret, current_user.id),
            )
            conn.commit()
            cur.close()
            conn.close()
            session.pop('totp_pending_secret', None)
            # Generate backup codes and show them
            codes = generate_backup_codes(current_user.id)
            flash('Authenticator app linked successfully.', 'success')
            return render_template('twofa/backup_codes.html', codes=codes, just_generated=True)

    return render_template('twofa/setup_totp.html')


@bp.route('/setup/totp/qr.png')
@login_required
def totp_qr():
    """Serve the QR code PNG for the pending TOTP secret."""
    secret = session.get('totp_pending_secret')
    if not secret:
        abort(404)
    png = generate_qr_png(get_totp_uri(secret, current_user.callsign))
    return send_file(io.BytesIO(png), mimetype='image/png')


# ---------------------------------------------------------------
# Backup codes
# ---------------------------------------------------------------

@bp.route('/backup-codes', methods=['GET', 'POST'])
@login_required
def backup_codes():
    if request.method == 'POST':
        # Require password confirmation before regenerating
        pw = request.form.get('password', '')
        conn = get_db()
        cur = dict_cursor(conn)
        cur.execute('SELECT password_hash FROM users WHERE id = %s', (current_user.id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        from ..auth import check_password
        if not check_password(pw, row['password_hash']):
            flash('Incorrect password.', 'danger')
            return render_template('twofa/backup_codes.html',
                                   remaining=unused_backup_code_count(current_user.id))
        codes = generate_backup_codes(current_user.id)
        return render_template('twofa/backup_codes.html', codes=codes, just_generated=True)

    return render_template('twofa/backup_codes.html',
                           remaining=unused_backup_code_count(current_user.id))


# ---------------------------------------------------------------
# Disable 2FA
# ---------------------------------------------------------------

@bp.route('/disable', methods=['POST'])
@login_required
def disable():
    pw = request.form.get('password', '')
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute('SELECT password_hash FROM users WHERE id = %s', (current_user.id,))
    row = cur.fetchone()
    if not check_password(pw, row['password_hash']):
        cur.close()
        conn.close()
        flash('Incorrect password — 2FA not disabled.', 'danger')
        return redirect(url_for('twofa.security'))

    cur.execute(
        'UPDATE users SET totp_secret = NULL, totp_enabled = 0, webauthn_enabled = 0 WHERE id = %s',
        (current_user.id,),
    )
    cur.execute('DELETE FROM totp_backup_codes WHERE user_id = %s', (current_user.id,))
    cur.execute('DELETE FROM webauthn_credentials WHERE user_id = %s', (current_user.id,))
    conn.commit()
    cur.close()
    conn.close()
    flash('Two-factor authentication has been disabled.', 'success')
    return redirect(url_for('twofa.security'))


# ---------------------------------------------------------------
# WebAuthn registration
# ---------------------------------------------------------------

@bp.route('/setup/webauthn', methods=['GET', 'POST'])
@login_required
def setup_webauthn():
    if request.method == 'POST':
        key_name = request.form.get('key_name', 'Security Key').strip() or 'Security Key'
        session['webauthn_reg_key_name'] = key_name
        return render_template('twofa/webauthn_register.html', key_name=key_name)
    return render_template('twofa/webauthn_register.html')


@bp.route('/webauthn/register/begin', methods=['POST'])
@login_required
def webauthn_reg_begin():
    options_json, challenge_b64 = webauthn_begin_registration(
        current_app._get_current_object(), current_user
    )
    session['webauthn_reg_challenge'] = challenge_b64
    return options_json, 200, {'Content-Type': 'application/json'}


@bp.route('/webauthn/register/complete', methods=['POST'])
@login_required
def webauthn_reg_complete():
    challenge_b64 = session.pop('webauthn_reg_challenge', None)
    if not challenge_b64:
        return jsonify({'success': False, 'message': 'Session expired'}), 400

    key_name = session.pop('webauthn_reg_key_name', 'Security Key')
    try:
        webauthn_complete_registration(
            current_app._get_current_object(),
            challenge_b64,
            request.get_json(force=True),
            current_user.id,
            key_name,
        )
    except Exception as e:
        current_app.logger.warning('WebAuthn registration failed: %s', e)
        return jsonify({'success': False, 'message': 'Security key registration failed'}), 400

    return jsonify({'success': True, 'redirect': url_for('twofa.security')})


@bp.route('/webauthn/delete/<int:cred_id>', methods=['POST'])
@login_required
def webauthn_delete(cred_id):
    delete_webauthn_credential(cred_id, current_user.id)
    flash('Security key removed.', 'success')
    return redirect(url_for('twofa.security'))


# ---------------------------------------------------------------
# Security settings overview page
# ---------------------------------------------------------------

@bp.route('/security')
@login_required
def security():
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute(
        'SELECT totp_enabled, webauthn_enabled FROM users WHERE id = %s', (current_user.id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    keys = get_webauthn_credentials(current_user.id)
    remaining = unused_backup_code_count(current_user.id) if row['totp_enabled'] else 0
    return render_template('twofa/security.html', row=row, keys=keys, remaining=remaining)
