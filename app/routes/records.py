import math
from datetime import date, timedelta

from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_mail import Message

from .. import mail
from ..constants import APP_TYPES, BANDS, BAND_LABELS, REGIONS, CTCSS_TONES, DCS_CODES, DMR_COLOR_CODES, P25_NACS, WILLBE_OPTIONS
from ..db import dict_cursor, get_db

bp = Blueprint('records', __name__, url_prefix='/records')


@bp.route('/<subdir>')
@login_required
def detail(subdir):
    conn = get_db()
    cur  = dict_cursor(conn)

    cur.execute('SELECT * FROM coordination_records WHERE subdir = %s', (subdir,))
    record = cur.fetchone()

    if record is None:
        abort(404)

    # Users can only view their own records; admins can view any
    if not current_user.is_admin and record['user_id'] != current_user.id and record['secondary_contact_id'] != current_user.id:
        abort(403)

    # Secondary contact
    secondary = None
    if record['secondary_contact_id']:
        cur.execute(
            'SELECT callsign, fname, lname, email, phone_home, phone_cell FROM users WHERE id = %s',
            (record['secondary_contact_id'],)
        )
        secondary = cur.fetchone()

    # Changelog
    cur.execute(
        '''SELECT changed_by, changed_at, summary
           FROM record_changelog WHERE record_id = %s
           ORDER BY changed_at DESC''',
        (record['id'],)
    )
    changelog = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('records/detail.html', r=record, changelog=changelog, secondary=secondary)


# ── User record edit ──────────────────────────────────────────

@bp.route('/<subdir>/edit', methods=['GET', 'POST'])
@login_required
def edit_record(subdir):
    conn = get_db()
    cur  = dict_cursor(conn)

    cur.execute('SELECT * FROM coordination_records WHERE subdir = %s', (subdir,))
    record = cur.fetchone()
    if not record:
        cur.close()
        conn.close()
        abort(404)

    if not current_user.is_admin and record['user_id'] != current_user.id:
        cur.close()
        conn.close()
        abort(403)

    # Admins use their own edit form
    if current_user.is_admin:
        cur.close()
        conn.close()
        return redirect(url_for('admin.edit_record', subdir=subdir))

    if request.method == 'POST':
        f = request.form

        def val(k):
            v = f.get(k, '').strip()
            return v if v else None

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

        def dateval(k):
            v = f.get(k, '').strip()
            if not v:
                return None
            for fmt in ('%m/%d/%Y', '%Y-%m-%d'):
                try:
                    from datetime import datetime as dt
                    return dt.strptime(v, fmt).strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return None

        # Resolve secondary contact
        sec_call = val('secondary_contact_callsign')
        sec_id = None
        if sec_call:
            cur.execute('SELECT id FROM users WHERE callsign = %s', (sec_call.upper(),))
            row = cur.fetchone()
            if row:
                sec_id = row['id']
            else:
                flash(f'Secondary contact callsign {sec_call} not found — field cleared.', 'warning')

        from datetime import date
        cur.execute('''
            UPDATE coordination_records SET
                subdsc=%s, system_id=%s, app_type=%s, willbe=%s,
                secondary_contact_id=%s,
                eq_ready=%s, eq_ready_date=%s,
                mod_date=%s,
                comments=%s,
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
                system_sponsor=%s, sponsor_abbrev=%s, sponsor_url=%s,
                trustee_name=%s, trustee_callsign=%s,
                trustee_phone_day=%s, trustee_phone_eve=%s, trustee_phone_cell=%s,
                trustee_email=%s
            WHERE subdir=%s
        ''', (
            val('subdsc'), val('system_id'), val('app_type'), val('willbe'),
            sec_id,
            1 if f.get('eq_ready') else 0, dateval('eq_ready_date'),
            date.today().strftime('%Y-%m-%d'),
            val('comments'),
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
            val('system_sponsor'), val('sponsor_abbrev'), val('sponsor_url'),
            val('trustee_name'), val('trustee_callsign'),
            val('trustee_phone_day'), val('trustee_phone_eve'), val('trustee_phone_cell'),
            val('trustee_email'),
            subdir,
        ))

        cur.execute(
            'INSERT INTO record_changelog (record_id, changed_by, summary) VALUES (%s, %s, %s)',
            (record['id'], current_user.callsign, 'Record updated by owner.')
        )
        conn.commit()
        cur.close()
        conn.close()

        flash('Record updated.', 'success')
        return redirect(url_for('records.detail', subdir=subdir))

    # GET — resolve secondary contact callsign for display
    sec_callsign = None
    if record['secondary_contact_id']:
        cur.execute('SELECT callsign FROM users WHERE id = %s', (record['secondary_contact_id'],))
        row = cur.fetchone()
        if row:
            sec_callsign = row['callsign']

    cur.close()
    conn.close()
    return render_template('records/edit_record.html', r=record,
                           sec_callsign=sec_callsign,
                           app_types=APP_TYPES, bands=BANDS, band_labels=BAND_LABELS,
                           regions=REGIONS, ctcss_tones=CTCSS_TONES, dcs_codes=DCS_CODES,
                           dmr_color_codes=DMR_COLOR_CODES, p25_nacs=P25_NACS,
                           willbe_options=WILLBE_OPTIONS)


# ── New application ────────────────────────────────────────────

def _next_subdir(cur):
    cur.execute("SELECT MAX(subdir) AS m FROM coordination_records WHERE subdir LIKE 'B%'")
    row = cur.fetchone()
    if row['m']:
        num = int(row['m'][1:]) + 1
    else:
        num = 1
    return f'B{num:05d}'


@bp.route('/applications/new', methods=['GET', 'POST'])
@login_required
def new_application():
    if request.method == 'POST':
        f = request.form

        def val(k):
            v = f.get(k, '').strip()
            return v if v else None

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

        conn = get_db()
        cur  = dict_cursor(conn)

        subdir    = _next_subdir(cur)
        today     = date.today()
        expires   = today + timedelta(days=730)

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
            INSERT INTO coordination_records (
                subdir, subdsc, user_id, secondary_contact_id, system_id,
                app_type, status, willbe,
                orig_date, mod_date, expires_date,
                eq_ready, eq_ready_date,
                comments,
                band, freq_output, freq_input, bandwidth,
                emission_des, emission_des2,
                tx_pl, rx_pl, tx_dcs, rx_dcs, dmr_cc,
                p25_nac, nxdn_ran, fusion_dsq,
                tx_power,
                loc_lat, loc_lng,
                loc_building, loc_street, loc_city,
                loc_county, loc_state, loc_region,
                ant_type, ant_gain, ant_haat, ant_amsl, ant_ahag,
                ant_favor, ant_beamwidth, ant_frontback,
                ant_polarization, ant_comment, fdl_loss,
                rx_lat, rx_lng,
                ant_type_rx, ant_gain_rx, ant_ahag_rx,
                ant_favor_rx, ant_beamwidth_rx, ant_frontback_rx,
                ant_polarization_rx, ant_comment_rx, fdl_loss_rx,
                trustee_name, trustee_callsign,
                trustee_phone_day, trustee_phone_eve, trustee_phone_cell,
                trustee_email
            ) VALUES (
                %s,%s,%s,%s,%s,
                %s,'New',%s,
                %s,%s,%s,
                %s,%s,
                %s,
                %s,%s,%s,%s,
                %s,%s,
                %s,%s,%s,%s,%s,
                %s,%s,%s,
                %s,
                %s,%s,
                %s,%s,%s,
                %s,%s,%s,
                %s,%s,%s,%s,%s,
                %s,%s,%s,
                %s,%s,%s,
                %s,%s,
                %s,%s,%s,
                %s,%s,%s,
                %s,%s,%s,
                %s,%s,
                %s,%s,%s,
                %s
            )
        ''', (
            subdir, val('subdsc'), current_user.id, sec_id, val('system_id'),
            val('app_type'), val('willbe'),
            today, today, expires,
            1 if f.get('eq_ready') else 0, val('eq_ready_date'),
            val('comments'),
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
        ))
        conn.commit()

        cur.execute(
            'INSERT INTO record_changelog (record_id, changed_by, summary) '
            'SELECT id, %s, %s FROM coordination_records WHERE subdir = %s',
            (current_user.callsign, 'Application submitted.', subdir)
        )
        conn.commit()
        cur.close()
        conn.close()

        _notify_admins_new(subdir, val('subdsc') or subdir, current_user.callsign)

        flash(f'Application {subdir} submitted successfully.', 'success')
        return redirect(url_for('records.detail', subdir=subdir))

    return render_template('records/new_application.html',
                           app_types=APP_TYPES, bands=BANDS, band_labels=BAND_LABELS, regions=REGIONS,
                           ctcss_tones=CTCSS_TONES, dcs_codes=DCS_CODES,
                           dmr_color_codes=DMR_COLOR_CODES, p25_nacs=P25_NACS,
                           willbe_options=WILLBE_OPTIONS)


def _notify_admins_new(subdir, description, callsign):
    recipients = current_app.config.get('ADMIN_NOTIFY_EMAILS', [])
    if not recipients:
        return
    record_url = f"{current_app.config['APP_URL']}/records/{subdir}"
    msg = Message(
        subject=f'Freqy — New Application {subdir}',
        recipients=recipients,
        body=(
            f"A new coordination application has been submitted.\n\n"
            f"Record:      {subdir}\n"
            f"Description: {description}\n"
            f"Submitted by: {callsign}\n\n"
            f"Review it here:\n{record_url}\n\n"
            f"73,\nfreqy by NF9K\n"
        ),
    )
    try:
        mail.send(msg)
    except Exception as e:
        current_app.logger.error('Failed to send new application notification: %s', e)


# ── Secondary contact update ───────────────────────────────────

@bp.route('/<subdir>/secondary-contact', methods=['POST'])
@login_required
def update_secondary(subdir):
    conn = get_db()
    cur  = dict_cursor(conn)

    cur.execute('SELECT id, user_id FROM coordination_records WHERE subdir = %s', (subdir,))
    record = cur.fetchone()
    if not record:
        cur.close()
        conn.close()
        abort(404)

    if not current_user.is_admin and record['user_id'] != current_user.id:
        cur.close()
        conn.close()
        abort(403)

    callsign = request.form.get('secondary_contact_callsign', '').strip().upper()
    sec_id = None
    if callsign:
        cur.execute('SELECT id FROM users WHERE callsign = %s', (callsign,))
        row = cur.fetchone()
        if row:
            sec_id = row['id']
        else:
            cur.close()
            conn.close()
            flash(f'Callsign {callsign} not found.', 'danger')
            return redirect(url_for('records.detail', subdir=subdir))

    cur.execute(
        'UPDATE coordination_records SET secondary_contact_id = %s WHERE subdir = %s',
        (sec_id, subdir)
    )
    conn.commit()
    cur.close()
    conn.close()

    if sec_id:
        flash(f'Secondary contact set to {callsign}.', 'success')
    else:
        flash('Secondary contact cleared.', 'success')
    return redirect(url_for('records.detail', subdir=subdir))


# ── NOPC email ────────────────────────────────────────────────

def _compute_erp(tx_power, fdl_loss, ant_gain):
    """Compute EIRP and ERP from TX power (W), feedline loss (dB), and antenna gain (dBd)."""
    tx_w = float(tx_power or 0)
    loss_db = float(fdl_loss or 0)
    gain_dbd = float(ant_gain or 0)
    if tx_w <= 0:
        return 0, 0, 0, 0
    tx_dbm = 10 * math.log10(1000 * tx_w)
    after = tx_dbm - loss_db
    eirp_dbm = after + gain_dbd
    eirp_watts = 10 ** ((eirp_dbm - 30) / 10)
    erp_dbm = eirp_dbm - 2.15
    erp_watts = 10 ** ((erp_dbm - 30) / 10)
    return eirp_dbm, eirp_watts, erp_dbm, erp_watts


def _build_nopc_body(r):
    """Build the NOPC email body text from a coordination record dict."""
    eirp_dbm, eirp_watts, erp_dbm, erp_watts = _compute_erp(
        r.get('tx_power'), r.get('fdl_loss'), r.get('ant_gain'))

    lat = r.get('loc_lat')
    lng = r.get('loc_lng')
    coord_dec = f"{lat} N / {lng} W" if lat and lng else "—"

    lines = [
        "Adjacent Area Frequency Coordinators:",
        "",
        "Please review the following proposal and provide your comments within 30",
        "days. Send your replies to the IRC Chairman.",
        "",
        "Thank you.",
        "",
        "System Information",
        "----------------------------",
        f"Record: {r.get('subdir', '—')}",
        f"Transmitter Callsign: {r.get('system_id') or '—'}",
        f"Output Frequency: {r.get('freq_output') or '—'}",
        f"Output Tone: {r.get('tx_pl') or '—'}",
        f"Input Frequency: {r.get('freq_input') or '—'}",
        f"Input Tone: {r.get('rx_pl') or '—'}",
        f"Mode(s): {r.get('rdnotes2') or '—'}",
        f"Record Type: {r.get('app_type') or '—'}",
        "",
        "Trustee Information",
        "----------------------------",
        f"Callsign: {r.get('trustee_callsign') or '—'}",
        f"Name: {r.get('trustee_name') or '—'}",
        f"Email: {r.get('trustee_email') or '—'}",
        f"Phone: {r.get('trustee_phone_day') or r.get('trustee_phone_eve') or r.get('trustee_phone_cell') or '—'}",
        "",
        "Site Information",
        "----------------------------",
        f"Address: {r.get('loc_street') or '—'}",
        f"Building: {r.get('loc_building') or '—'}",
        f"City: {r.get('loc_city') or '—'}",
        f"Coordinates: {coord_dec}",
        f"Antenna HAAT (ft): {r.get('ant_haat') or '—'}",
        f"Antenna AMSL (ft): {r.get('ant_amsl') or '—'}",
        f"Antenna Type: {r.get('ant_type') or '—'}",
        f"Antenna Gain: {r.get('ant_gain') or '—'} dBd",
        f"Transmitter Power: {r.get('tx_power') or '—'} W",
        f"System Loss: {r.get('fdl_loss') or '—'} dB",
        f"EIRP: {eirp_dbm:.2f} dBm (~{eirp_watts:.2f} W)",
        f"ERP: {erp_dbm:.2f} dBm (~{erp_watts:.2f} W)",
        "",
    ]
    return "\n".join(lines)


@bp.route('/<subdir>/nopc-preview')
@login_required
def nopc_preview(subdir):
    if not current_user.is_admin:
        abort(403)
    recipients = current_app.config.get('NOPC_EMAIL_TO', [])
    if not recipients:
        return jsonify(success=False, message='NOPC_EMAIL_TO is not configured.'), 400
    from_addrs = current_app.config.get('NOPC_EMAIL_FROM', [])
    if not from_addrs:
        return jsonify(success=False, message='NOPC_EMAIL_FROM is not configured.'), 400

    conn = get_db()
    cur  = dict_cursor(conn)
    cur.execute('SELECT * FROM coordination_records WHERE subdir = %s', (subdir,))
    record = cur.fetchone()
    cur.close()
    conn.close()

    if not record:
        return jsonify(success=False, message='Record not found.'), 404

    body = _build_nopc_body(record)
    subject = f"New NOPC from Indiana: {record.get('freq_output') or subdir}"
    return jsonify(success=True, subject=subject, body=body,
                   recipients=', '.join(recipients), from_addrs=from_addrs)


@bp.route('/<subdir>/nopc-send', methods=['POST'])
@login_required
def nopc_send(subdir):
    if not current_user.is_admin:
        abort(403)
    recipients = current_app.config.get('NOPC_EMAIL_TO', [])
    if not recipients:
        return jsonify(success=False, message='NOPC_EMAIL_TO is not configured.'), 400
    from_addrs = current_app.config.get('NOPC_EMAIL_FROM', [])
    if not from_addrs:
        return jsonify(success=False, message='NOPC_EMAIL_FROM is not configured.'), 400

    data = request.get_json(silent=True) or {}
    chosen_from = data.get('from_addr', '').strip()
    if chosen_from not in from_addrs:
        return jsonify(success=False, message='Invalid sender address.'), 400

    conn = get_db()
    cur  = dict_cursor(conn)
    cur.execute('SELECT * FROM coordination_records WHERE subdir = %s', (subdir,))
    record = cur.fetchone()
    cur.close()
    conn.close()

    if not record:
        return jsonify(success=False, message='Record not found.'), 404

    body = _build_nopc_body(record)
    subject = f"New NOPC from Indiana: {record.get('freq_output') or subdir}"

    msg = Message(subject=subject, recipients=recipients, body=body, sender=chosen_from)
    try:
        mail.send(msg)
    except Exception as e:
        current_app.logger.error('Failed to send NOPC email for %s: %s', subdir, e)
        return jsonify(success=False, message=f'Failed to send: {e}'), 500

    return jsonify(success=True, message=f'NOPC sent to {", ".join(recipients)} from {chosen_from}.')
