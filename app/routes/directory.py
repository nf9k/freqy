import csv
import io
from datetime import date, datetime

from flask import Blueprint, Response, abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from ..constants import APP_TYPES, BANDS, BAND_LABELS, REGIONS
from ..db import dict_cursor, get_db

bp = Blueprint('directory', __name__, url_prefix='/directory')

# Columns safe for public display (no audit_comments, trustee contact, etc.)
_PUBLIC_SELECT = '''
    r.subdir, r.subdsc, u.callsign AS owner, r.system_id,
    r.app_type, r.status, r.band,
    r.freq_output, r.freq_input, r.bandwidth, r.emission_des,
    r.tx_pl, r.rx_pl, r.tx_dcs, r.dmr_cc, r.p25_nac, r.nxdn_ran, r.fusion_dsq,
    r.tx_power, r.willbe,
    r.loc_lat, r.loc_lng, r.loc_city, r.loc_county, r.loc_state,
    r.loc_building, r.loc_street,
    r.ant_type, r.ant_gain, r.ant_haat, r.ant_amsl, r.ant_ahag,
    r.ant_polarization, r.ant_favor,
    r.rdnotes, r.rdnotes2,
    r.orig_date, r.mod_date, r.expires_date,
    r.comments
'''


def _build_query(params):
    """Build WHERE clauses from filter params. Returns (where_sql, bind_values)."""
    clauses = ["r.status = 'Final'"]
    values = []

    band = params.get('band', '')
    if band and band in BANDS:
        clauses.append('r.band = %s')
        values.append(band)

    app_type = params.get('type', '')
    if app_type and app_type in APP_TYPES:
        clauses.append('r.app_type = %s')
        values.append(app_type)

    region = params.get('region', '')
    if region and region in REGIONS:
        clauses.append('r.loc_region = %s')
        values.append(region)

    state = params.get('state', '')
    if state:
        clauses.append('r.loc_state = %s')
        values.append(state.upper()[:2])

    q = params.get('q', '').strip()
    if q:
        clauses.append('''(
            r.subdir LIKE %s OR r.subdsc LIKE %s OR r.system_id LIKE %s
            OR u.callsign LIKE %s OR r.loc_city LIKE %s
            OR CAST(r.freq_output AS CHAR) LIKE %s
        )''')
        like = f'%{q}%'
        values.extend([like] * 6)

    where = ' AND '.join(clauses)
    return where, values


def _clean(v):
    if v is None:
        return None
    if isinstance(v, (date, datetime)):
        return str(v)
    if hasattr(v, '__float__'):
        return float(v)
    return v


# ── Directory main page ─────────────────────────────────────

@bp.route('/')
@login_required
def index():
    conn = get_db()
    cur = dict_cursor(conn)

    where, values = _build_query(request.args)
    cur.execute(f'''
        SELECT {_PUBLIC_SELECT}
        FROM coordination_records r
        JOIN users u ON u.id = r.user_id
        WHERE {where}
        ORDER BY r.freq_output
    ''', values)
    records = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('directory/index.html',
                           records=records,
                           bands=BANDS, band_labels=BAND_LABELS,
                           app_types=APP_TYPES, regions=REGIONS,
                           filters=request.args)


# ── JSON API for map markers ─────────────────────────────────

@bp.route('/api/records')
@login_required
def api_records():
    conn = get_db()
    cur = dict_cursor(conn)

    where, values = _build_query(request.args)
    cur.execute(f'''
        SELECT r.subdir, r.subdsc, r.system_id, u.callsign AS owner,
               r.freq_output, r.band, r.app_type, r.willbe,
               r.loc_lat, r.loc_lng, r.loc_city, r.loc_state,
               r.tx_pl, r.dmr_cc
        FROM coordination_records r
        JOIN users u ON u.id = r.user_id
        WHERE {where}
          AND r.loc_lat IS NOT NULL AND r.loc_lng IS NOT NULL
        ORDER BY r.freq_output
    ''', values)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([{k: _clean(v) for k, v in r.items()} for r in rows])


# ── Read-only record detail ──────────────────────────────────

@bp.route('/<subdir>')
@login_required
def detail(subdir):
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute(f'''
        SELECT {_PUBLIC_SELECT}
        FROM coordination_records r
        JOIN users u ON u.id = r.user_id
        WHERE r.subdir = %s AND r.status = 'Final'
    ''', (subdir,))
    record = cur.fetchone()
    cur.close()
    conn.close()

    if not record:
        abort(404)

    return render_template('directory/detail.html', r=record, band_labels=BAND_LABELS)


# ── CHIRP CSV export ─────────────────────────────────────────

@bp.route('/export/chirp')
@login_required
def export_chirp():
    conn = get_db()
    cur = dict_cursor(conn)

    where, values = _build_query(request.args)
    cur.execute(f'''
        SELECT r.system_id, r.subdsc, r.freq_output, r.freq_input,
               r.tx_pl, r.rx_pl, r.tx_dcs, r.dmr_cc, r.p25_nac,
               r.loc_city, r.loc_state, r.band
        FROM coordination_records r
        JOIN users u ON u.id = r.user_id
        WHERE {where}
        ORDER BY r.freq_output
    ''', values)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['Location', 'Name', 'Frequency', 'Duplex', 'Offset',
                     'Tone', 'rToneFreq', 'cToneFreq', 'DtcsCode', 'DtcsPolarity',
                     'Mode', 'TStep', 'Skip', 'Comment', 'URCALL', 'RPT1CALL', 'RPT2CALL'])

    for i, r in enumerate(rows, 1):
        out = float(r['freq_output']) if r['freq_output'] else 0
        inp = float(r['freq_input']) if r['freq_input'] else out

        # Duplex
        if inp < out:
            duplex = '-'
        elif inp > out:
            duplex = '+'
        else:
            duplex = ''
        offset = f'{abs(out - inp):.6f}'

        # Tone
        tx_pl = str(r['tx_pl'] or '')
        rx_pl = str(r['rx_pl'] or '')
        tx_dcs = str(r['tx_dcs'] or '')
        if tx_pl:
            tone_mode = 'Tone'
        elif tx_dcs:
            tone_mode = 'DTCS'
        else:
            tone_mode = ''

        rtone = tx_pl if tx_pl else '88.5'
        ctone = rx_pl if rx_pl else '88.5'
        dcs_code = tx_dcs.rstrip('NI') if tx_dcs else '023'
        dcs_pol = 'NN'

        # Mode
        if r.get('dmr_cc') is not None:
            mode = 'DMR'
        elif r.get('p25_nac'):
            mode = 'P25'
        else:
            mode = 'FM'

        name = (r['system_id'] or '')[:8]
        city = r['loc_city'] or ''
        state = r['loc_state'] or ''
        comment = f"{(r['subdsc'] or '')[:30]} {city}, {state}".strip()

        writer.writerow([i, name, f'{out:.6f}', duplex, offset,
                         tone_mode, rtone, ctone, dcs_code, dcs_pol,
                         mode, '5.00', '', comment, '', '', ''])

    resp = Response(buf.getvalue(), mimetype='text/csv')
    resp.headers['Content-Disposition'] = 'attachment; filename=freqy_chirp.csv'
    return resp


# ── Band plan data API ───────────────────────────────────────

_BAND_RANGES = {
    '29':  (29.0, 29.7),
    '50':  (50.0, 54.0),
    '144': (144.0, 148.0),
    '222': (222.0, 225.0),
    '440': (420.0, 450.0),
    '902': (902.0, 928.0),
    '1296': (1200.0, 1300.0),
}

# Map GHZ band key to sub-bands for display
_BAND_KEY_MAP = {'GHZ': ['902', '1296']}


@bp.route('/api/band-plan/<band>')
@login_required
def api_band_plan(band):
    if band not in _BAND_RANGES:
        return jsonify(success=False, message='Unknown band'), 400

    freq_lo, freq_hi = _BAND_RANGES[band]

    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute('''
        SELECT r.subdir, r.subdsc, r.system_id, u.callsign AS owner,
               r.freq_output, r.app_type, r.status,
               r.loc_city, r.loc_state, r.tx_pl, r.dmr_cc
        FROM coordination_records r
        JOIN users u ON u.id = r.user_id
        WHERE r.freq_output BETWEEN %s AND %s
          AND r.status IN ('Final', 'Construction Permit', 'On Hold', 'Audit')
        ORDER BY r.freq_output
    ''', (freq_lo, freq_hi))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    channels = []
    for r in rows:
        channels.append({
            'freq': float(r['freq_output']),
            'subdir': r['subdir'],
            'callsign': r['owner'],
            'system_id': r['system_id'],
            'subdsc': r['subdsc'] or '',
            'city': r['loc_city'] or '',
            'state': r['loc_state'] or '',
            'status': r['status'],
            'app_type': r['app_type'] or '',
            'tx_pl': str(r['tx_pl'] or ''),
            'dmr_cc': r['dmr_cc'],
        })

    return jsonify(band=band, range=[freq_lo, freq_hi], channels=channels)


# ── Band plan page ───────────────────────────────────────────

@bp.route('/band-plan')
@login_required
def band_plan():
    return render_template('directory/band_plan.html',
                           band_ranges=_BAND_RANGES, band_labels=BAND_LABELS)


# ── Activity confirmation (public, token-authenticated) ──────

@bp.route('/confirm-activity/<token>')
def confirm_activity(token):
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute('''
        SELECT id, subdir, subdsc FROM coordination_records
        WHERE activity_confirm_token = %s AND status = 'Final'
    ''', (token,))
    record = cur.fetchone()

    if not record:
        cur.close()
        conn.close()
        flash('This confirmation link is invalid or has already been used.', 'danger')
        return render_template('directory/activity_confirmed.html', success=False)

    cur.execute('''
        UPDATE coordination_records
        SET last_activity_confirmed = CURDATE(), activity_confirm_token = NULL
        WHERE id = %s
    ''', (record['id'],))
    cur.execute('''
        INSERT INTO activity_confirmations (record_id, confirmed_by, method)
        VALUES (%s, 'LINK', 'email')
    ''', (record['id'],))
    conn.commit()
    cur.close()
    conn.close()

    return render_template('directory/activity_confirmed.html',
                           success=True, record=record)
