import csv
import io
import json
import math
import xml.etree.ElementTree as ET
from datetime import date, datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for, current_app, Response
from flask_login import current_user
from flask_mail import Message

from .. import mail
from ..auth import admin_required, create_reset_token, hash_password
from ..constants import STATUSES, APP_TYPES, BANDS, BAND_LABELS, REGIONS, CTCSS_TONES, DCS_CODES, DMR_COLOR_CODES, P25_NACS, WILLBE_OPTIONS
from ..db import dict_cursor, get_db

bp = Blueprint('admin', __name__, url_prefix='/admin')


# ── Record edit ───────────────────────────────────────────────

@bp.route('/applications/<subdir>/edit', methods=['GET', 'POST'])
@admin_required
def edit_record(subdir):
    conn = get_db()
    cur  = dict_cursor(conn)

    if request.method == 'POST':
        f = request.form

        def val(k):
            v = f.get(k, '').strip()
            return v if v else None

        def dateval(k):
            v = f.get(k, '').strip()
            if not v:
                return None
            for fmt in ('%m/%d/%Y', '%Y-%m-%d'):
                try:
                    from datetime import datetime
                    return datetime.strptime(v, fmt).strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return None

        def num(k):
            v = f.get(k, '').strip()
            try:
                return float(v) if v else None
            except ValueError:
                return None

        def intval(k):
            v = f.get(k, '').strip()
            try:
                return int(float(v)) if v else None
            except ValueError:
                return None

        # Resolve secondary contact callsign → id
        sec_call = val('secondary_contact_callsign')
        sec_id = None
        if sec_call:
            cur.execute('SELECT id FROM users WHERE callsign = %s', (sec_call.upper(),))
            row = cur.fetchone()
            if row:
                sec_id = row['id']
            else:
                flash(f'Secondary contact callsign {sec_call} not found — field cleared.', 'warning')

        cur.execute('''
            UPDATE coordination_records SET
                system_id=%s, secondary_contact_id=%s,
                system_sponsor=%s, sponsor_abbrev=%s, sponsor_url=%s,
                app_type=%s, status=%s, last_action=%s, willbe=%s,
                orig_date=%s, mod_date=%s, expires_date=%s,
                eq_ready=%s, eq_ready_date=%s, inherit=%s,
                comments=%s, audit_comments=%s, rdnotes=%s, rdnotes2=%s,
                band=%s, freq_output=%s, freq_input=%s, bandwidth=%s,
                emission_des=%s, emission_des2=%s,
                tx_pl=%s, rx_pl=%s, tx_dcs=%s, rx_dcs=%s, dmr_cc=%s,
                p25_nac=%s, nxdn_ran=%s, fusion_dsq=%s,
                tx_power=%s,
                loc_lat=%s, loc_lng=%s,
                loc_building=%s, loc_street=%s, loc_city=%s,
                loc_county=%s, loc_state=%s, loc_region=%s,
                ant_type=%s, ant_gain=%s, ant_haat=%s, ant_amsl=%s, ant_ahag=%s,
                ant_favor=%s, ant_beamwidth=%s, ant_frontback=%s,
                ant_polarization=%s, ant_comment=%s, fdl_loss=%s,
                rx_lat=%s, rx_lng=%s,
                ant_type_rx=%s, ant_gain_rx=%s, ant_ahag_rx=%s,
                ant_favor_rx=%s, ant_beamwidth_rx=%s, ant_frontback_rx=%s,
                ant_polarization_rx=%s, ant_comment_rx=%s, fdl_loss_rx=%s,
                trustee_name=%s, trustee_callsign=%s,
                trustee_phone_day=%s, trustee_phone_eve=%s, trustee_phone_cell=%s,
                trustee_email=%s
            WHERE subdir=%s
        ''', (
            val('system_id'), sec_id,
            val('system_sponsor'), val('sponsor_abbrev'), val('sponsor_url'),
            val('app_type'), val('status'), val('last_action'), val('willbe'),
            dateval('orig_date'), dateval('mod_date'), dateval('expires_date'),
            1 if f.get('eq_ready') else 0, dateval('eq_ready_date'),
            1 if f.get('inherit') else 0,
            val('comments'), val('audit_comments'), val('rdnotes'), val('rdnotes2'),
            val('band'), num('freq_output'), num('freq_input'), val('bandwidth'),
            val('emission_des'), val('emission_des2'),
            val('tx_pl'), val('rx_pl'), val('tx_dcs'), val('rx_dcs'), intval('dmr_cc'),
            val('p25_nac'), val('nxdn_ran'), val('fusion_dsq'),
            intval('tx_power'),
            num('loc_lat'), num('loc_lng'),
            val('loc_building'), val('loc_street'), val('loc_city'),
            val('loc_county'), val('loc_state'), val('loc_region'),
            val('ant_type'), num('ant_gain'), intval('ant_haat'), intval('ant_amsl'), intval('ant_ahag'),
            val('ant_favor'), val('ant_beamwidth'), val('ant_frontback'),
            val('ant_polarization'), val('ant_comment'), num('fdl_loss'),
            num('rx_lat'), num('rx_lng'),
            val('ant_type_rx'), num('ant_gain_rx'), intval('ant_ahag_rx'),
            val('ant_favor_rx'), val('ant_beamwidth_rx'), val('ant_frontback_rx'),
            val('ant_polarization_rx'), val('ant_comment_rx'), num('fdl_loss_rx'),
            val('trustee_name'), val('trustee_callsign'),
            val('trustee_phone_day'), val('trustee_phone_eve'), val('trustee_phone_cell'),
            val('trustee_email'),
            subdir,
        ))
        conn.commit()
        cur.close()
        conn.close()
        flash('Record updated.', 'success')
        return redirect(url_for('records.detail', subdir=subdir))

    # GET
    cur.execute('SELECT * FROM coordination_records WHERE subdir = %s', (subdir,))
    record = cur.fetchone()
    if not record:
        cur.close()
        conn.close()
        flash('Record not found.', 'danger')
        return redirect(url_for('admin.applications'))

    # Resolve secondary contact id → callsign for display
    sec_callsign = None
    if record['secondary_contact_id']:
        cur.execute('SELECT callsign FROM users WHERE id = %s', (record['secondary_contact_id'],))
        row = cur.fetchone()
        if row:
            sec_callsign = row['callsign']

    cur.close()
    conn.close()
    return render_template('admin/edit_record.html', r=record,
                           sec_callsign=sec_callsign,
                           statuses=STATUSES, app_types=APP_TYPES,
                           bands=BANDS, band_labels=BAND_LABELS, regions=REGIONS,
                           ctcss_tones=CTCSS_TONES, dcs_codes=DCS_CODES,
                           dmr_color_codes=DMR_COLOR_CODES, p25_nacs=P25_NACS,
                           willbe_options=WILLBE_OPTIONS)


# ── Applications list ──────────────────────────────────────────

@bp.route('/applications')
@admin_required
def applications():
    q        = request.args.get('q', '').strip()
    status   = request.args.get('status', '')
    band     = request.args.get('band', '')
    region   = request.args.get('region', '')
    app_type = request.args.get('app_type', '')

    conditions = []
    params     = []

    if q:
        conditions.append('(subdir LIKE %s OR subdsc LIKE %s OR system_id LIKE %s OR loc_city LIKE %s)')
        like = f'%{q}%'
        params.extend([like, like, like, like])
    if status:
        conditions.append('status = %s')
        params.append(status)
    if band:
        conditions.append('band = %s')
        params.append(band)
    if region:
        conditions.append('loc_region = %s')
        params.append(region)
    if app_type:
        conditions.append('app_type = %s')
        params.append(app_type)

    where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

    conn = get_db()
    cur  = dict_cursor(conn)
    cur.execute(f'''
        SELECT subdir, subdsc, system_id, app_type, status,
               band, freq_output, loc_city, loc_region, expires_date
        FROM coordination_records
        {where}
        ORDER BY subdir
    ''', params)
    records = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('admin/applications.html',
        records=records, q=q, status=status, band=band,
        region=region, app_type=app_type,
        statuses=STATUSES, app_types=APP_TYPES, bands=BANDS, band_labels=BAND_LABELS, regions=REGIONS,
    )


# ── Record status update ───────────────────────────────────────

@bp.route('/applications/<subdir>/status', methods=['POST'])
@admin_required
def update_status(subdir):
    new_status   = request.form.get('status', '').strip()
    last_action  = request.form.get('last_action', '').strip() or None
    audit_notes  = request.form.get('audit_comments', '').strip() or None

    if new_status not in STATUSES:
        flash('Invalid status.', 'danger')
        return redirect(url_for('records.detail', subdir=subdir))

    conn = get_db()
    cur  = dict_cursor(conn)
    cur.execute('''
        UPDATE coordination_records
        SET status=%s, last_action=%s, audit_comments=%s
        WHERE subdir=%s
    ''', (new_status, last_action, audit_notes, subdir))
    conn.commit()
    cur.close()
    conn.close()

    flash(f'Status updated to {new_status}.', 'success')
    return redirect(url_for('records.detail', subdir=subdir))


# ── Add user ──────────────────────────────────────────────────

@bp.route('/users/new', methods=['GET', 'POST'])
@admin_required
def new_user():
    if request.method == 'POST':
        callsign = request.form.get('callsign', '').strip().upper()
        email    = request.form.get('email', '').strip() or None
        fname    = request.form.get('fname', '').strip() or None
        lname    = request.form.get('lname', '').strip() or None
        is_admin = 1 if request.form.get('is_admin') else 0

        if not callsign:
            flash('Callsign is required.', 'danger')
            return render_template('admin/new_user.html')

        conn = get_db()
        cur  = dict_cursor(conn)
        cur.execute('SELECT id FROM users WHERE callsign = %s', (callsign,))
        if cur.fetchone():
            cur.close()
            conn.close()
            flash(f'Callsign {callsign} is already in use.', 'danger')
            return render_template('admin/new_user.html')

        import secrets as _secrets
        temp_pw = _secrets.token_urlsafe(16)

        cur.execute('''
            INSERT INTO users (callsign, email, password_hash, fname, lname, is_admin)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (callsign, email, hash_password(temp_pw), fname, lname, is_admin))
        conn.commit()
        new_id = cur.lastrowid

        # Send password-set email if email provided
        if email:
            token     = create_reset_token(new_id)
            reset_url = f"{current_app.config['APP_URL']}/reset-password/{token}"
            msg = Message(
                subject='Freqy — Your account has been created',
                recipients=[email],
                body=(
                    f"Hello {fname or callsign},\n\n"
                    f"An administrator has created a freqy account for you.\n\n"
                    f"Callsign: {callsign}\n\n"
                    f"Set your password here:\n{reset_url}\n\n"
                    f"This link expires in 24 hours.\n\n"
                    f"73,\nfreqy by NF9K\n"
                ),
            )
            try:
                mail.send(msg)
                flash(f'User {callsign} created and welcome email sent to {email}.', 'success')
            except Exception as e:
                current_app.logger.error('Failed to send welcome email: %s', e)
                flash(f'User {callsign} created but failed to send welcome email.', 'warning')
        else:
            flash(f'User {callsign} created. No email on file — set password manually via the reset button.', 'warning')

        cur.close()
        conn.close()
        return redirect(url_for('admin.user_detail', user_id=new_id))

    return render_template('admin/new_user.html')


# ── User list ──────────────────────────────────────────────────

@bp.route('/users')
@admin_required
def users():
    conn = get_db()
    cur  = dict_cursor(conn)
    cur.execute('''
        SELECT u.id, u.callsign, u.fname, u.lname, u.email, u.is_admin,
               COUNT(r.id) AS record_count
        FROM users u
        LEFT JOIN coordination_records r ON r.user_id = u.id
        GROUP BY u.id
        ORDER BY u.callsign
    ''')
    users = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin/users.html', users=users)


# ── User detail / edit ─────────────────────────────────────────

@bp.route('/users/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def user_detail(user_id):
    conn = get_db()
    cur  = dict_cursor(conn)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'save_profile':
            new_callsign = request.form.get('callsign', '').strip().upper()
            is_admin     = 1 if request.form.get('is_admin') else 0

            cur.execute('SELECT callsign FROM users WHERE id = %s', (user_id,))
            old = cur.fetchone()
            if old and new_callsign and new_callsign != old['callsign']:
                cur.execute('SELECT id FROM users WHERE callsign = %s AND id != %s',
                            (new_callsign, user_id))
                if cur.fetchone():
                    flash(f'Callsign {new_callsign} is already in use.', 'danger')
                    cur.close()
                    conn.close()
                    return redirect(url_for('admin.user_detail', user_id=user_id))

            cur.execute('''
                UPDATE users SET
                    callsign=%s, fname=%s, mname=%s, lname=%s, suffix=%s, email=%s,
                    address=%s, city=%s, state=%s, zip=%s,
                    phone_home=%s, phone_work=%s, phone_cell=%s,
                    is_admin=%s, license_class=%s
                WHERE id=%s
            ''', (
                new_callsign,
                request.form.get('fname', '').strip() or None,
                request.form.get('mname', '').strip() or None,
                request.form.get('lname', '').strip() or None,
                request.form.get('suffix', '').strip() or None,
                request.form.get('email', '').strip() or None,
                request.form.get('address', '').strip() or None,
                request.form.get('city', '').strip() or None,
                request.form.get('state', '').strip().upper() or None,
                request.form.get('zip', '').strip() or None,
                request.form.get('phone_home', '').strip() or None,
                request.form.get('phone_work', '').strip() or None,
                request.form.get('phone_cell', '').strip() or None,
                is_admin,
                request.form.get('license_class', '').strip() or None,
                user_id,
            ))
            conn.commit()
            flash('User updated.', 'success')

        cur.close()
        conn.close()
        return redirect(url_for('admin.user_detail', user_id=user_id))

    cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        flash('User not found.', 'danger')
        return redirect(url_for('admin.users'))

    cur.execute('''
        SELECT subdir, subdsc, band, status, expires_date
        FROM coordination_records
        WHERE user_id = %s
        ORDER BY mod_date DESC
    ''', (user_id,))
    records = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('admin/user_detail.html', user=user, records=records)


# ── User delete ───────────────────────────────────────────────

@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': 'You cannot delete your own account.'}), 400

    conn = get_db()
    cur  = dict_cursor(conn)

    cur.execute('''
        SELECT COUNT(*) AS cnt FROM coordination_records
        WHERE user_id = %s OR secondary_contact_id = %s
    ''', (user_id, user_id))
    if cur.fetchone()['cnt'] > 0:
        cur.close()
        conn.close()
        return jsonify({'success': False, 'message': 'Cannot delete — user has records attached.'}), 400

    cur.execute('DELETE FROM users WHERE id = %s', (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'success': True})


# ── Review Changes ────────────────────────────────────────────

@bp.route('/changes')
@admin_required
def review_changes():
    date_from = request.args.get('from', '').strip()
    date_to   = request.args.get('to', '').strip()
    callsign  = request.args.get('callsign', '').strip().upper()
    subdir    = request.args.get('subdir', '').strip().upper()

    conditions = []
    params     = []

    if date_from:
        conditions.append('cl.changed_at >= %s')
        params.append(date_from + ' 00:00:00')
    if date_to:
        conditions.append('cl.changed_at <= %s')
        params.append(date_to + ' 23:59:59')
    if callsign:
        conditions.append('cl.changed_by = %s')
        params.append(callsign)
    if subdir:
        conditions.append('r.subdir = %s')
        params.append(subdir)

    where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

    conn = get_db()
    cur  = dict_cursor(conn)
    cur.execute(f'''
        SELECT cl.changed_at, cl.changed_by, cl.summary,
               r.subdir, r.subdsc, r.status
        FROM record_changelog cl
        JOIN coordination_records r ON r.id = cl.record_id
        {where}
        ORDER BY cl.changed_at DESC
        LIMIT 500
    ''', params)
    entries = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('admin/review_changes.html',
                           entries=entries,
                           date_from=date_from, date_to=date_to,
                           callsign=callsign, subdir=subdir)


# ── FCC callsign lookup (AJAX) ────────────────────────────────

@bp.route('/users/lookup/<callsign>')
@admin_required
def callsign_lookup(callsign):
    conn = get_db()
    cur  = dict_cursor(conn)
    cur.execute('SELECT * FROM fcc_licenses WHERE callsign = %s', (callsign.strip().upper(),))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return jsonify({'found': False})
    # Convert datetime to string for JSON serialisation
    if row.get('updated_at'):
        row['updated_at'] = str(row['updated_at'])
    return jsonify({'found': True, **row})


# ── Password reset (AJAX) ──────────────────────────────────────

@bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_password(user_id):
    conn = get_db()
    cur  = dict_cursor(conn)
    cur.execute('SELECT callsign, email FROM users WHERE id = %s', (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return jsonify({'success': False, 'message': 'User not found.'}), 404
    if not user['email']:
        return jsonify({'success': False, 'message': 'User has no email address on file.'}), 400

    token     = create_reset_token(user_id)
    reset_url = f"{current_app.config['APP_URL']}/reset-password/{token}"
    msg = Message(
        subject='Freqy — Password Reset',
        recipients=[user['email']],
        body=(
            f"Hello {user['callsign']},\n\n"
            f"An administrator has initiated a password reset for your account.\n\n"
            f"Click the link below to set a new password:\n{reset_url}\n\n"
            f"This link expires in 24 hours.\n\n73,\nfreqy by NF9K\n"
        ),
    )
    try:
        mail.send(msg)
        return jsonify({'success': True, 'message': f"Reset email sent to {user['email']}."})
    except Exception as e:
        current_app.logger.error('Failed to send reset email: %s', e)
        return jsonify({'success': False, 'message': 'Failed to send email.'}), 500


# ── Frequency coordination check ─────────────────────────────────

# Co-channel minimum separation (miles) — all bands
def _get_co_channel_miles():
    return current_app.config['FREQ_CO_CHANNEL_MILES']

def _get_adj_rules():
    # Config stores lists (JSON-safe); convert inner lists to tuples for consistency.
    return {k: [tuple(pair) for pair in v]
            for k, v in current_app.config['FREQ_ADJ_RULES'].items()}


def _haversine_miles(lat1, lon1, lat2, lon2):
    R = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a  = math.sin(dp/2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def _rules_key(freq_mhz):
    """Return the separation-rules band key for a given output frequency."""
    if   50.0  <= freq_mhz <  54.0:  return '50'
    elif 144.0 <= freq_mhz < 148.0:  return '144'
    elif 222.0 <= freq_mhz < 225.0:  return '222'
    elif 420.0 <= freq_mhz < 450.0:  return '440'
    elif 900.0 <= freq_mhz < 930.0:  return '902'
    elif 1200.0 <= freq_mhz < 1300.0: return '1296'
    return None


def _adj_rule(rules, offset_khz):
    """Return (max_offset_khz, min_sep_miles) for offset, or None if out of range."""
    for max_off, min_sep in rules:
        if offset_khz <= max_off + 0.05:   # float tolerance
            return max_off, min_sep
    return None


@bp.route('/export')
@admin_required
def db_export():
    return render_template('admin/db_export.html')


@bp.route('/export/<fmt>')
@admin_required
def db_export_download(fmt):
    if fmt not in ('csv', 'json', 'xml', 'pdf'):
        return 'Invalid format', 400

    conn = get_db()
    cur  = dict_cursor(conn)
    cur.execute('''
        SELECT
            r.subdir, r.subdsc, u.callsign AS owner, r.system_id,
            r.app_type, r.status, r.band,
            r.freq_output, r.freq_input, r.bandwidth, r.emission_des, r.emission_des2,
            r.tx_pl, r.rx_pl, r.tx_dcs, r.dmr_cc, r.p25_nac, r.nxdn_ran, r.fusion_dsq,
            r.tx_power,
            r.loc_lat, r.loc_lng, r.loc_building, r.loc_street,
            r.loc_city, r.loc_county, r.loc_state,
            r.ant_type, r.ant_gain, r.ant_haat, r.ant_amsl, r.ant_ahag,
            r.ant_favor, r.ant_polarization,
            r.willbe, r.rdnotes, r.rdnotes2,
            r.orig_date, r.mod_date, r.expires_date,
            r.comments
        FROM coordination_records r
        JOIN users u ON u.id = r.user_id
        WHERE r.status = 'Final'
        ORDER BY r.subdir
    ''')
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Serialize date/decimal/other non-primitive types to strings
    def _clean(v):
        if v is None:
            return ''
        if isinstance(v, (date, datetime)):
            return str(v)
        if hasattr(v, '__float__'):   # Decimal
            return float(v)
        return v

    records = [{k: _clean(v) for k, v in row.items()} for row in rows]
    now = datetime.now()
    timestamp = now.strftime('%Y%m%d')
    date_str  = now.strftime('%m/%d/%Y')
    title = current_app.config.get('EXPORT_TITLE', 'Frequency Coordination Database Export as of {date}')
    title = title.replace('{date}', date_str)

    if fmt == 'csv':
        buf = io.StringIO()
        buf.write(f'# {title}\n')
        if records:
            writer = csv.DictWriter(buf, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
        return Response(
            buf.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=freqy_export_{timestamp}.csv'},
        )

    if fmt == 'json':
        payload = {'title': title, 'records': records}
        return Response(
            json.dumps(payload, indent=2),
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename=freqy_export_{timestamp}.json'},
        )

    if fmt == 'xml':
        root = ET.Element('coordination_records', title=title)
        for rec in records:
            el = ET.SubElement(root, 'record')
            for k, v in rec.items():
                child = ET.SubElement(el, k)
                child.text = str(v)
        xml_bytes = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        return Response(
            xml_bytes,
            mimetype='application/xml',
            headers={'Content-Disposition': f'attachment; filename=freqy_export_{timestamp}.xml'},
        )

    if fmt == 'pdf':
        from fpdf import FPDF
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=True, margin=10)

        def _add_page_with_title():
            pdf.add_page()
            pdf.set_font('Helvetica', 'B', 9)
            pdf.cell(0, 6, title, ln=True, align='C')
            pdf.ln(1)

        _add_page_with_title()
        pdf.set_font('Helvetica', 'B', 7)

        # Key columns for PDF (too many fields for one page — pick the most useful)
        cols = [
            ('ID',        'subdir',       14),
            ('Owner',     'owner',        16),
            ('System',    'system_id',    16),
            ('Type',      'app_type',     18),
            ('Band',      'band',         10),
            ('Output',    'freq_output',  18),
            ('Input',     'freq_input',   18),
            ('TX PL',     'tx_pl',        12),
            ('Power',     'tx_power',     12),
            ('City',      'loc_city',     28),
            ('ST',        'loc_state',     8),
            ('Expires',   'expires_date', 20),
            ('Notes',     'rdnotes',      30),
        ]

        # Header
        for label, _, w in cols:
            pdf.cell(w, 5, label, border=1, align='C')
        pdf.ln()

        pdf.set_font('Helvetica', '', 6)
        fill = False
        for rec in records:
            if pdf.get_y() > 190:
                _add_page_with_title()
                pdf.set_font('Helvetica', 'B', 7)
                for label, _, w in cols:
                    pdf.cell(w, 5, label, border=1, align='C')
                pdf.ln()
                pdf.set_font('Helvetica', '', 6)
                fill = False
            pdf.set_fill_color(240, 240, 240) if fill else pdf.set_fill_color(255, 255, 255)
            for _, field, w in cols:
                val = str(rec.get(field, ''))
                pdf.cell(w, 4, val[:28], border='LR', fill=True)
            pdf.ln()
            fill = not fill

        # Closing border line
        for _, _, w in cols:
            pdf.cell(w, 0, '', border='T')

        pdf_bytes = pdf.output()
        return Response(
            bytes(pdf_bytes),
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=freqy_export_{timestamp}.pdf'},
        )


@bp.route('/frequency-check', methods=['GET', 'POST'])
@admin_required
def frequency_check():
    results = None
    form_data = {}

    if request.method == 'POST':
        coord_mode = request.form.get('coord_mode', 'decimal')
        try:
            if coord_mode == 'dms':
                def _dms(d, m, s, direction, neg_dirs):
                    v = abs(float(d)) + float(m)/60 + float(s)/3600
                    return -v if direction in neg_dirs else v
                lat = _dms(
                    request.form.get('lat_d', 0), request.form.get('lat_m', 0),
                    request.form.get('lat_s', 0), request.form.get('lat_dir', 'N'), ('S',)
                )
                lon = _dms(
                    request.form.get('lon_d', 0), request.form.get('lon_m', 0),
                    request.form.get('lon_s', 0), request.form.get('lon_dir', 'W'), ('W',)
                )
            else:
                lat = float(request.form.get('lat', ''))
                lon = float(request.form.get('lon', ''))

            freq_str = request.form.get('freq', '')
            freq = float(freq_str)
        except (ValueError, TypeError):
            flash('Invalid coordinates or frequency.', 'danger')
            return render_template('admin/frequency_check.html', results=None, form_data=request.form)

        form_data = {**request.form, 'lat': lat, 'lon': lon, 'freq': freq_str}

        key = _rules_key(freq)
        if key is None:
            flash('Frequency is not in a coordinated band (6m, 2m, 222, 440, 902, 1296).', 'warning')
            return render_template('admin/frequency_check.html', results=None, form_data=form_data)

        adj_rules  = _get_adj_rules().get(key, [])
        max_adj_mhz = adj_rules[-1][0] / 1000.0 if adj_rules else 0.0

        conn = get_db()
        cur  = dict_cursor(conn)
        cur.execute('''
            SELECT r.id, r.subdir, r.system_id, r.subdsc, r.freq_output,
                   r.band, r.status, r.loc_lat, r.loc_lng, r.loc_city, r.loc_state,
                   u.callsign
            FROM   coordination_records r
            JOIN   users u ON u.id = r.user_id
            WHERE  r.freq_output IS NOT NULL
              AND  r.loc_lat  IS NOT NULL
              AND  r.loc_lng  IS NOT NULL
              AND  ABS(r.freq_output - %s) <= %s
              AND  r.status IN ('Final', 'Construction Permit', 'On Hold', 'Audit')
        ''', (freq, max_adj_mhz + 0.0001))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        co_channel = []
        adjacent   = []

        for row in rows:
            dist       = _haversine_miles(lat, lon, float(row['loc_lat']), float(row['loc_lng']))
            offset_khz = round(abs(float(row['freq_output']) - freq) * 1000, 3)

            co_channel_miles = _get_co_channel_miles()
            if offset_khz < 0.1:                        # co-channel
                passes = dist >= co_channel_miles
                co_channel.append({
                    **row,
                    'distance':       round(dist, 1),
                    'offset_khz':     0,
                    'required_miles': co_channel_miles,
                    'passes':         passes,
                })
            else:
                rule = _adj_rule(adj_rules, offset_khz)
                if rule:
                    _, min_sep = rule
                    adjacent.append({
                        **row,
                        'distance':       round(dist, 1),
                        'offset_khz':     offset_khz,
                        'required_miles': min_sep,
                        'passes':         dist >= min_sep,
                    })

        co_channel.sort(key=lambda r: r['distance'])
        adjacent.sort(key=lambda r: r['distance'])

        results = {
            'co_channel': co_channel,
            'adjacent':   adjacent,
            'freq':        freq,
            'band_key':    key,
            'lat':         lat,
            'lon':         lon,
        }

    return render_template('admin/frequency_check.html', results=results, form_data=form_data)
