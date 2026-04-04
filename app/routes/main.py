from flask import Blueprint, render_template
from flask_login import login_required, current_user

from ..constants import BAND_LABELS
from ..db import dict_cursor, get_db

bp = Blueprint('main', __name__)


@bp.route('/')
@bp.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    cur  = dict_cursor(conn)

    if current_user.is_admin:
        cur.execute('SELECT COUNT(*) AS cnt FROM coordination_records')
        total = cur.fetchone()['cnt']

        cur.execute('''
            SELECT status, COUNT(*) AS cnt
            FROM coordination_records
            GROUP BY status ORDER BY cnt DESC
        ''')
        by_status = {r['status']: r['cnt'] for r in cur.fetchall()}

        cur.execute('''
            SELECT app_type, COUNT(*) AS cnt
            FROM coordination_records
            GROUP BY app_type ORDER BY cnt DESC
        ''')
        by_type = {r['app_type']: r['cnt'] for r in cur.fetchall()}

        cur.execute('''
            SELECT band, COUNT(*) AS cnt
            FROM coordination_records
            GROUP BY band ORDER BY cnt DESC
        ''')
        by_band = {r['band']: r['cnt'] for r in cur.fetchall()}

        stats = {
            'total':     total,
            'by_status': by_status,
            'by_type':   by_type,
            'by_band':   by_band,
        }
        cur.execute(
            'SELECT * FROM coordination_records WHERE user_id = %s ORDER BY mod_date DESC',
            (current_user.id,)
        )
        my_records = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('main/dashboard_admin.html', stats=stats, my_records=my_records,
                               band_labels=BAND_LABELS)

    cur.execute(
        'SELECT * FROM coordination_records WHERE user_id = %s ORDER BY mod_date DESC',
        (current_user.id,)
    )
    records = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('main/dashboard_user.html', records=records)
