from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..db import dict_cursor, get_db

bp = Blueprint('profile', __name__)


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def edit():
    conn = get_db()
    cur  = dict_cursor(conn)

    if request.method == 'POST':
        fields = {
            'fname':      request.form.get('fname', '').strip() or None,
            'mname':      request.form.get('mname', '').strip() or None,
            'lname':      request.form.get('lname', '').strip() or None,
            'suffix':     request.form.get('suffix', '').strip() or None,
            'email':      request.form.get('email', '').strip() or None,
            'address':    request.form.get('address', '').strip() or None,
            'city':       request.form.get('city', '').strip() or None,
            'state':      request.form.get('state', '').strip().upper() or None,
            'zip':        request.form.get('zip', '').strip() or None,
            'phone_home': request.form.get('phone_home', '').strip() or None,
            'phone_work': request.form.get('phone_work', '').strip() or None,
            'phone_cell': request.form.get('phone_cell', '').strip() or None,
        }

        cur.execute('''
            UPDATE users SET
                fname=%s, mname=%s, lname=%s, suffix=%s, email=%s,
                address=%s, city=%s, state=%s, zip=%s,
                phone_home=%s, phone_work=%s, phone_cell=%s
            WHERE id=%s
        ''', (
            fields['fname'], fields['mname'], fields['lname'], fields['suffix'], fields['email'],
            fields['address'], fields['city'], fields['state'], fields['zip'],
            fields['phone_home'], fields['phone_work'], fields['phone_cell'],
            current_user.id,
        ))
        conn.commit()
        cur.close()
        conn.close()

        flash('Profile updated.', 'success')
        return redirect(url_for('profile.edit'))

    cur.execute('SELECT * FROM users WHERE id = %s', (current_user.id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('profile/edit.html', user=user)
