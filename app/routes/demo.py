import os
from flask import Blueprint, current_app, jsonify, request, abort
from flask_login import current_user

from ..db import get_db

bp = Blueprint('demo', __name__, url_prefix='/demo')


@bp.route('/reset', methods=['POST'])
def reset():
    if not current_app.config.get('DEMO_MODE'):
        abort(404)

    token    = request.args.get('token') or request.form.get('token')
    is_admin = current_user.is_authenticated and current_user.is_admin
    cfg_tok  = current_app.config.get('DEMO_RESET_TOKEN', '')

    if not is_admin and (not cfg_tok or token != cfg_tok):
        abort(403)

    seed_path = os.path.join(current_app.root_path, '..', 'demo', 'seed.sql')
    try:
        sql = open(seed_path).read()
    except FileNotFoundError:
        return jsonify({'success': False, 'message': 'seed.sql not found'}), 500

    conn = get_db()
    cur  = conn.cursor()
    for stmt in sql.split(';\n'):
        stmt = stmt.strip().rstrip(';')
        if stmt and not stmt.startswith('--'):
            cur.execute(stmt)
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'success': True, 'message': 'Demo data has been reset.'})
