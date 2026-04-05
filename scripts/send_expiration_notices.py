#!/usr/bin/env python3
"""
Send expiration reminder emails for coordination records nearing their expires_date.

Thresholds: 90, 60, 30, 14, 7, 1 days before expiration.
Each (record_id, days_threshold) pair fires exactly once, tracked in
the expiration_notices table.

Skips records whose status is Cancelled, Expired, Placeholder, or N/A.
Skips records with no expires_date (NULL).

Usage:
    python scripts/send_expiration_notices.py [--dry-run]

Environment variables (same .env as the Flask app):
    DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
    SMTP_FROM_NAME, SMTP_FROM_EMAIL
    APP_URL
"""

import argparse
import os
import smtplib
import sys
from datetime import date, timedelta
from email.message import EmailMessage
from pathlib import Path

import MySQLdb
import MySQLdb.cursors
from dotenv import load_dotenv

# ── Config ─────────────────────────────────────────────────────

THRESHOLDS = [90, 60, 30, 14, 7, 1]

SKIP_STATUSES = {'Cancelled', 'Expired', 'Placeholder'}


# ── DB ─────────────────────────────────────────────────────────

def get_conn():
    load_dotenv(Path(__file__).parent.parent / '.env')
    return MySQLdb.connect(
        host=os.environ['DB_HOST'],
        user=os.environ['DB_USER'],
        passwd=os.environ['DB_PASSWORD'],
        db=os.environ['DB_NAME'],
        charset='utf8mb4',
    )


def dict_cursor(conn):
    return conn.cursor(MySQLdb.cursors.DictCursor)


# ── Email ───────────────────────────────────────────────────────

def smtp_cfg():
    return {
        'host':     os.getenv('SMTP_HOST', 'mail.smtp2go.com'),
        'port':     int(os.getenv('SMTP_PORT', 587)),
        'user':     os.getenv('SMTP_USER', ''),
        'password': os.getenv('SMTP_PASSWORD', ''),
        'from_name':  os.getenv('SMTP_FROM_NAME', 'freqy'),
        'from_email': os.getenv('SMTP_FROM_EMAIL', 'noreply@example.com'),
    }


def send_email(to_addr, subject, body, cfg, dry_run=False):
    if dry_run:
        print(f'    [DRY-RUN] To: {to_addr}  Subject: {subject}')
        return

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From']    = f"{cfg['from_name']} <{cfg['from_email']}>"
    msg['To']      = to_addr
    msg.set_content(body)

    with smtplib.SMTP(cfg['host'], cfg['port']) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(cfg['user'], cfg['password'])
        smtp.send_message(msg)


# ── Core logic ──────────────────────────────────────────────────

def run(dry_run=False):
    conn = get_conn()
    cur  = dict_cursor(conn)
    cfg  = smtp_cfg()
    app_url = os.getenv('APP_URL', 'http://localhost:5000')
    today   = date.today()

    sent = 0
    errors = 0

    for days in THRESHOLDS:
        target_date = today + timedelta(days=days)

        # Records expiring exactly `days` days from today that:
        # - have an expires_date
        # - are not in a skip status
        # - have not already had this threshold fired
        cur.execute('''
            SELECT r.id, r.subdir, r.subdsc, r.status, r.expires_date,
                   u.callsign, u.email, u.fname,
                   sc.callsign  AS sec_callsign,
                   sc.email     AS sec_email,
                   sc.fname     AS sec_fname
            FROM coordination_records r
            JOIN users u ON u.id = r.user_id
            LEFT JOIN users sc ON sc.id = r.secondary_contact_id
            WHERE r.expires_date = %s
              AND r.status NOT IN ('Cancelled', 'Expired', 'Placeholder')
              AND r.expires_date IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM expiration_notices en
                  WHERE en.record_id = r.id
                    AND en.days_threshold = %s
              )
        ''', (target_date.strftime('%Y-%m-%d'), days))

        records = cur.fetchall()

        for rec in records:
            record_url = f"{app_url}/records/{rec['subdir']}"
            expires_str = rec['expires_date'].strftime('%m/%d/%Y') if hasattr(rec['expires_date'], 'strftime') else str(rec['expires_date'])
            description = rec['subdsc'] or rec['subdir']

            body = (
                f"Hello {rec['fname'] or rec['callsign']},\n\n"
                f"This is a reminder that your frequency coordination record "
                f"is expiring in {days} day{'s' if days != 1 else ''}.\n\n"
                f"Record:      {rec['subdir']}\n"
                f"Description: {description}\n"
                f"Status:      {rec['status']}\n"
                f"Expires:     {expires_str}\n\n"
                f"Please log in to review and renew your coordination:\n"
                f"{record_url}\n\n"
                f"If you have questions, contact the coordination team.\n\n"
                f"73,\nfreqy by NF9K\n"
            )
            subject = f"Freqy — Coordination {rec['subdir']} expires in {days} day{'s' if days != 1 else ''}"

            # Primary contact
            recipients = []
            if rec['email']:
                recipients.append((rec['email'], rec['callsign']))

            # Secondary contact (if different email)
            if rec['sec_email'] and rec['sec_email'] != rec['email']:
                recipients.append((rec['sec_email'], rec['sec_callsign']))

            if not recipients:
                print(f"  SKIP {rec['subdir']} ({days}d) — no email address on record", flush=True)
            else:
                all_ok = True
                for email, callsign in recipients:
                    try:
                        send_email(email, subject, body, cfg, dry_run=dry_run)
                        print(f"  {'[DRY] ' if dry_run else ''}Sent {days}d notice for {rec['subdir']} → {callsign} <{email}>", flush=True)
                    except Exception as exc:
                        print(f"  ERROR sending to {email} for {rec['subdir']}: {exc}", file=sys.stderr, flush=True)
                        all_ok = False
                        errors += 1
                if all_ok:
                    sent += 1

            # Record the notice as sent (even if no email — prevents repeated skips)
            if not dry_run:
                cur.execute(
                    'INSERT IGNORE INTO expiration_notices (record_id, days_threshold) VALUES (%s, %s)',
                    (rec['id'], days)
                )
                conn.commit()

    cur.close()
    conn.close()

    print(f'Done. {sent} notice(s) sent, {errors} error(s).', flush=True)
    return errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send coordination expiration reminders')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print what would be sent without sending or recording')
    args = parser.parse_args()

    try:
        errs = run(dry_run=args.dry_run)
    except Exception as exc:
        print(f'FATAL: {exc}', file=sys.stderr, flush=True)
        sys.exit(1)

    sys.exit(1 if errs else 0)
