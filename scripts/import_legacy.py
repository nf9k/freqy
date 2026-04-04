#!/usr/bin/env python3
"""
Import legacy Flexweb IRCINC flat-file data into the freqy-database schema.

Usage:
    python scripts/import_legacy.py [--dry-run] /path/to/IRCINC

The IRCINC directory should contain one subdirectory per callsign, each with:
  params.txt                  — account / user data
  {RECORD_ID}/params.txt      — coordination record
  {RECORD_ID}/changelog.txt   — changelog entries
"""

import argparse
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

import bcrypt
import MySQLdb
import MySQLdb.cursors
from dotenv import load_dotenv

# ---------------------------------------------------------------
# Config
# ---------------------------------------------------------------

NONE_VALUES = {'NONE-ON-FILE', 'N/A', '', None}

EXPIRATION_RE = re.compile(r'^\d{8}$')   # YYYYMMDD

# ---------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------

def get_db():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWORD'),
        db=os.getenv('DB_NAME'),
        charset='utf8mb4',
    )


def dict_cursor(conn):
    return conn.cursor(MySQLdb.cursors.DictCursor)


# ---------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------

def parse_params(path):
    """Parse a Flexweb KEY="value file. First occurrence of a key wins."""
    data = {}
    try:
        with open(path, 'r', errors='replace') as f:
            for line in f:
                line = line.strip()
                if '="' not in line:
                    continue
                key, _, val = line.partition('="')
                key = key.strip()
                if key and key not in data:
                    data[key] = val.strip() if val.strip() else None
    except OSError:
        pass
    return data


def clean(val):
    """Return None for empty / NONE-ON-FILE values, else stripped string."""
    if val is None:
        return None
    v = str(val).strip()
    return None if v in NONE_VALUES else v


def flag(val):
    """Y/N/1/0 → True/False, else None."""
    v = clean(val)
    if v is None:
        return None
    return v.upper() in ('Y', '1', 'TRUE')


def parse_date(val):
    """YYYYMMDD string → date, or None."""
    v = clean(val)
    if not v or not EXPIRATION_RE.match(v):
        return None
    try:
        return date(int(v[:4]), int(v[4:6]), int(v[6:8]))
    except ValueError:
        return None


def parse_decimal(val):
    """Return float or None; reject 0.0 as meaningful for lat/lng."""
    v = clean(val)
    if v is None:
        return None
    try:
        f = float(v)
        return f if f != 0.0 else None
    except ValueError:
        return None


def parse_int(val):
    v = clean(val)
    if v is None:
        return None
    try:
        return int(float(v))
    except ValueError:
        return None


def parse_changelog(path):
    """Return list of (changed_by, changed_at, summary) tuples from changelog.txt."""
    entries = []
    try:
        with open(path, 'r', errors='replace') as f:
            text = f.read()
    except OSError:
        return entries

    # Split on the separator lines
    blocks = re.split(r'\*{20,}', text)
    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Try to extract date and actor
        # Patterns seen: "Change Date: April 10, 2020 09:46\nBy: KA9VXS"
        # or: "Import from previous database: December 15, 2019 18:12\nBy: SYSTEM"
        date_match = re.search(
            r'(?:Change Date|Import from previous database):\s*(.+?)(?:\n|$)', block
        )
        by_match = re.search(r'By:\s*(\S+)', block)

        changed_at = None
        if date_match:
            try:
                changed_at = datetime.strptime(date_match.group(1).strip(), '%B %d, %Y %H:%M')
            except ValueError:
                pass

        changed_by = by_match.group(1).strip() if by_match else 'SYSTEM'
        entries.append((changed_by, changed_at, block))

    return entries


# ---------------------------------------------------------------
# Import logic
# ---------------------------------------------------------------

def import_user(conn, p, dry_run):
    """Insert or update a user row. Returns user id."""
    callsign = clean(p.get('CALLS'))
    if not callsign:
        return None

    passcode = clean(p.get('PASSCODE'))
    if dry_run:
        pw_hash = '*dry-run*'
    elif passcode:
        pw_hash = bcrypt.hashpw(passcode.encode(), bcrypt.gensalt(rounds=10)).decode()
    else:
        # No password on file — set a locked hash; admin can trigger reset
        pw_hash = bcrypt.hashpw(b'*locked*', bcrypt.gensalt(rounds=10)).decode()

    row = {
        'callsign':    callsign,
        'password_hash': pw_hash,
        'email':       clean(p.get('EMAIL')),
        'fname':       clean(p.get('FNAME')),
        'mname':       clean(p.get('MNAME')),
        'lname':       clean(p.get('LNAME')),
        'suffix':      clean(p.get('SUFFIX')),
        'address':     clean(p.get('STADR')),
        'city':        clean(p.get('CITYX')),
        'state':       clean(p.get('STATE')),
        'zip':         clean(p.get('ZIPCO')),
        'phone_home':  clean(p.get('HPHON')),
        'phone_work':  clean(p.get('WPHON')),
        'phone_cell':  clean(p.get('CPHON')),
        'is_admin':    0,
    }

    if dry_run:
        return callsign  # placeholder

    cur = dict_cursor(conn)
    cur.execute('SELECT id FROM users WHERE callsign = %s', (callsign,))
    existing = cur.fetchone()

    if existing:
        cur.execute('''
            UPDATE users SET email=%s, fname=%s, mname=%s, lname=%s, suffix=%s,
                address=%s, city=%s, state=%s, zip=%s,
                phone_home=%s, phone_work=%s, phone_cell=%s
            WHERE callsign=%s
        ''', (
            row['email'], row['fname'], row['mname'], row['lname'], row['suffix'],
            row['address'], row['city'], row['state'], row['zip'],
            row['phone_home'], row['phone_work'], row['phone_cell'],
            callsign,
        ))
        conn.commit()
        return existing['id']

    cur.execute('''
        INSERT INTO users
            (callsign, password_hash, email, fname, mname, lname, suffix,
             address, city, state, zip, phone_home, phone_work, phone_cell, is_admin)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ''', (
        row['callsign'], row['password_hash'], row['email'],
        row['fname'], row['mname'], row['lname'], row['suffix'],
        row['address'], row['city'], row['state'], row['zip'],
        row['phone_home'], row['phone_work'], row['phone_cell'],
        row['is_admin'],
    ))
    conn.commit()
    return cur.lastrowid


def import_record(conn, user_id, p, dry_run):
    """Insert or update a coordination record. Returns record id."""
    subdir = clean(p.get('SUBDIR'))
    if not subdir:
        return None

    # Longitude: legacy stores as positive for West — negate
    lat = parse_decimal(p.get('LOC_LATDISP'))
    lng = parse_decimal(p.get('LOC_LNGDISP'))
    if lng is not None:
        lng = -abs(lng)

    rx_lat = parse_decimal(p.get('LOC_LATD_RX'))   # fallback: use D/M/S later if needed
    rx_lng = parse_decimal(p.get('LOC_LNGD_RX'))
    # If RX coords match TX (same site), store NULL
    if rx_lat == lat and rx_lng == lng:
        rx_lat = rx_lng = None
    elif rx_lng is not None:
        rx_lng = -abs(rx_lng)

    row = {
        'subdir':           subdir,
        'subdsc':           clean(p.get('SUBDSC')),
        'user_id':          user_id,
        'system_id':        clean(p.get('SYSTEM_ID')),
        'system_sponsor':   clean(p.get('SYSTEM_SPONSOR')),
        'sponsor_abbrev':   clean(p.get('ABB_SPONSOR')),
        'sponsor_url':      clean(p.get('SYSTEM_SPONSOR_HTTP')),
        'parent_record_id': None,   # resolved in second pass if PARENT_SYSTEM set
        'app_type':         clean(p.get('APP_TYPE')) or 'Repeater',
        'status':           clean(p.get('APPSTAT')) or 'New',
        'last_action':      clean(p.get('LAST_ACTION')),
        'willbe':           clean(p.get('WILLBE')),
        'orig_date':        parse_date(p.get('ODATE')),
        'mod_date':         parse_date(p.get('MDATE')),
        'expires_date':     parse_date(p.get('EXPIRES')),   # N/A → None
        'eq_ready':         flag(p.get('EQREADY')),
        'eq_ready_date':    parse_date(p.get('EQREADY_DATE')),
        'inherit':          flag(p.get('INHERIT')),
        'comments':         clean(p.get('COMMENTS')),
        'audit_comments':   clean(p.get('AUDITCOMMENTS')),
        'rdnotes':          clean(p.get('RDNOTES')),
        'rdnotes2':         clean(p.get('RDNOTES2')),
        'band':             clean(p.get('SFP_BAND')),
        'freq_output':      parse_decimal(p.get('SFP_OUTPUT')),
        'freq_input':       parse_decimal(p.get('SFP_INPUT')),
        'bandwidth':        clean(p.get('SFP_BANDWIDTH')),
        'emission_des':     clean(p.get('EMIDES')),
        'emission_des2':    clean(p.get('EMIDES_2')),
        'tx_pl':            clean(p.get('TX_PL')),
        'rx_pl':            clean(p.get('RX_PL')),
        'tx_dcs':           clean(p.get('TX_DCS')),
        'dmr_cc':           parse_int(p.get('DMR_CC')),
        'p25_nac':          clean(p.get('P25_NAC')),
        'nxdn_ran':         clean(p.get('NXDN_RAN')),
        'fusion_dsq':       clean(p.get('FUSION_DSQ')),
        'tx_power':         parse_int(p.get('TX_POWER')),
        'loc_lat':          lat,
        'loc_lng':          lng,
        'loc_building':     clean(p.get('LOC_BUILDING')),
        'loc_street':       clean(p.get('LOC_STREET')),
        'loc_city':         clean(p.get('LOC_CITY')),
        'loc_county':       clean(p.get('LOC_COUNTY')),
        'loc_state':        clean(p.get('LOC_STATE')),
        'loc_region':       clean(p.get('LOC_REGION')),
        'ant_type':         clean(p.get('ANT_TYPE')),
        'ant_gain':         parse_decimal(p.get('ANT_GAIN')),
        'ant_haat':         parse_int(p.get('ANT_HAAT')),
        'ant_amsl':         parse_int(p.get('ANT_AMSL')),
        'ant_ahag':         parse_int(p.get('ANT_AHAG')),
        'ant_favor':        clean(p.get('ANT_FAVOR')),
        'ant_beamwidth':    clean(p.get('ANT_BEAMWIDTH')),
        'ant_frontback':    clean(p.get('ANT_FRONTBACK')),
        'ant_polarization': clean(p.get('ANT_POLARIZATION')),
        'ant_comment':      clean(p.get('ANT_COMMENT')),
        'fdl_loss':         parse_decimal(p.get('FDL_LOSS')),
        'rx_lat':           rx_lat,
        'rx_lng':           rx_lng,
        'ant_type_rx':      clean(p.get('ANT_TYPE_RX')),
        'ant_gain_rx':      parse_decimal(p.get('ANT_GAIN_RX')),
        'ant_ahag_rx':      parse_int(p.get('ANT_AHAG_RX')),
        'ant_favor_rx':     clean(p.get('ANT_FAVOR_RX')),
        'ant_beamwidth_rx': clean(p.get('ANT_BEAMWIDTH_RX')),
        'ant_frontback_rx': clean(p.get('ANT_FRONTBACK_RX')),
        'ant_polarization_rx': clean(p.get('ANT_POLARIZATION_RX')),
        'ant_comment_rx':   clean(p.get('ANT_COMMENT_RX')),
        'fdl_loss_rx':      parse_decimal(p.get('FDL_LOSS_RX')),
        'trustee_name':     clean(p.get('SYSTEM_TRUSTEE')),
        'trustee_callsign': clean(p.get('SYSTEM_TRUSTEE_CALL')),
        'trustee_phone_day':  clean(p.get('SYSTEM_TRUSTEE_DPH')),
        'trustee_phone_eve':  clean(p.get('SYSTEM_TRUSTEE_EPH')),
        'trustee_phone_cell': clean(p.get('SYSTEM_TRUSTEE_CPH')),
        'trustee_email':    clean(p.get('SYSTEM_TRUSTEE_EML')),
    }

    if dry_run:
        return subdir

    cur = dict_cursor(conn)
    cur.execute('SELECT id FROM coordination_records WHERE subdir = %s', (subdir,))
    existing = cur.fetchone()

    cols = [k for k in row if k != 'parent_record_id']
    if existing:
        sets = ', '.join(f'{c}=%s' for c in cols if c != 'user_id')
        vals = [row[c] for c in cols if c != 'user_id'] + [subdir]
        cur.execute(f'UPDATE coordination_records SET {sets} WHERE subdir=%s', vals)
        conn.commit()
        return existing['id']

    placeholders = ', '.join(['%s'] * len(cols))
    col_names = ', '.join(cols)
    vals = [row[c] for c in cols]
    cur.execute(
        f'INSERT INTO coordination_records ({col_names}) VALUES ({placeholders})',
        vals,
    )
    conn.commit()
    return cur.lastrowid


def import_changelog(conn, record_id, changelog_path, dry_run):
    if dry_run:
        return
    entries = parse_changelog(changelog_path)
    if not entries:
        return
    cur = dict_cursor(conn)
    for changed_by, changed_at, summary in entries:
        cur.execute(
            '''INSERT IGNORE INTO record_changelog (record_id, changed_by, changed_at, summary)
               VALUES (%s, %s, %s, %s)''',
            (record_id, changed_by, changed_at, summary[:65535])
        )
    conn.commit()


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Import legacy IRCINC data')
    parser.add_argument('ircinc_dir', help='Path to IRCINC directory')
    parser.add_argument('--dry-run', action='store_true',
                        help='Parse and report without writing to DB')
    args = parser.parse_args()

    ircinc = Path(args.ircinc_dir)
    if not ircinc.is_dir():
        sys.exit(f'Error: {ircinc} is not a directory')

    load_dotenv()

    conn = None
    if not args.dry_run:
        try:
            conn = get_db()
        except Exception as e:
            sys.exit(f'DB connection failed: {e}')

    stats = {
        'users_ok': 0, 'users_skip': 0,
        'records_ok': 0, 'records_skip': 0,
        'changelogs': 0,
        'errors': [],
    }

    callsign_dirs = sorted(d for d in ircinc.iterdir() if d.is_dir())
    print(f'Processing {len(callsign_dirs)} callsign directories...')

    for call_dir in callsign_dirs:
        callsign = call_dir.name
        user_params_file = call_dir / 'params.txt'

        if not user_params_file.exists():
            stats['users_skip'] += 1
            continue

        user_p = parse_params(user_params_file)
        if not clean(user_p.get('CALLS')):
            stats['users_skip'] += 1
            continue

        try:
            user_id = import_user(conn, user_p, args.dry_run)
            stats['users_ok'] += 1
        except Exception as e:
            stats['errors'].append(f'User {callsign}: {e}')
            stats['users_skip'] += 1
            continue

        # Records are subdirectories that look like A#####
        for rec_dir in sorted(call_dir.iterdir()):
            if not rec_dir.is_dir() or not re.match(r'^[A-Z]\d+$', rec_dir.name):
                continue

            rec_params_file = rec_dir / 'params.txt'
            if not rec_params_file.exists():
                stats['records_skip'] += 1
                continue

            rec_p = parse_params(rec_params_file)
            if not clean(rec_p.get('SUBDIR')):
                stats['records_skip'] += 1
                continue

            try:
                rec_id = import_record(conn, user_id, rec_p, args.dry_run)
                stats['records_ok'] += 1
            except Exception as e:
                stats['errors'].append(f'Record {callsign}/{rec_dir.name}: {e}')
                stats['records_skip'] += 1
                continue

            changelog_file = rec_dir / 'changelog.txt'
            if changelog_file.exists() and not args.dry_run:
                import_changelog(conn, rec_id, changelog_file, args.dry_run)
                stats['changelogs'] += 1

    if conn:
        conn.close()

    print()
    print('=' * 50)
    print(f"  Users imported:    {stats['users_ok']:>6}")
    print(f"  Users skipped:     {stats['users_skip']:>6}")
    print(f"  Records imported:  {stats['records_ok']:>6}")
    print(f"  Records skipped:   {stats['records_skip']:>6}")
    print(f"  Changelogs parsed: {stats['changelogs']:>6}")
    if stats['errors']:
        print(f"\n  Errors ({len(stats['errors'])}):")
        for e in stats['errors'][:20]:
            print(f"    {e}")
        if len(stats['errors']) > 20:
            print(f"    ... and {len(stats['errors']) - 20} more")
    print('=' * 50)

    if args.dry_run:
        print('\n[DRY RUN — no data written]')


if __name__ == '__main__':
    main()
