#!/usr/bin/env python3
"""
Send activity confirmation emails for coordination records that haven't
confirmed activity within the configured interval (ACTIVITY_CHECK_DAYS).

Each record gets a unique token link. Clicking the link confirms activity
and clears the token. Only sends to records that don't already have a
pending token (prevents duplicate sends).

Usage:
    python scripts/send_activity_checks.py [--dry-run]

Environment variables (same .env as the Flask app):
    DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
    SMTP_FROM_NAME, SMTP_FROM_EMAIL
    APP_URL
    ACTIVITY_CHECK_DAYS (default: 365)
"""

import argparse
import os
import secrets
import smtplib
import sys
from datetime import date
from email.message import EmailMessage
from pathlib import Path

import MySQLdb
import MySQLdb.cursors
from dotenv import load_dotenv


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


def smtp_cfg():
    return {
        'host':       os.getenv('SMTP_HOST', 'mail.smtp2go.com'),
        'port':       int(os.getenv('SMTP_PORT', 587)),
        'user':       os.getenv('SMTP_USER', ''),
        'password':   os.getenv('SMTP_PASSWORD', ''),
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


def run(dry_run=False):
    conn = get_conn()
    cur  = dict_cursor(conn)
    cfg  = smtp_cfg()
    app_url = os.getenv('APP_URL', 'http://localhost:5000')
    check_days = int(os.getenv('ACTIVITY_CHECK_DAYS', '365'))
    today = date.today()

    # Find Final records needing activity check:
    # - Never confirmed, or confirmed more than check_days ago
    # - Don't already have a pending token (avoid re-sending)
    cur.execute('''
        SELECT r.id, r.subdir, r.subdsc, r.last_activity_confirmed,
               u.callsign, u.email, u.fname
        FROM coordination_records r
        JOIN users u ON u.id = r.user_id
        WHERE r.status = 'Final'
          AND r.activity_confirm_token IS NULL
          AND (r.last_activity_confirmed IS NULL
               OR r.last_activity_confirmed < DATE_SUB(CURDATE(), INTERVAL %s DAY))
    ''', (check_days,))
    records = cur.fetchall()

    print(f'[{today}] Found {len(records)} records needing activity confirmation '
          f'(interval: {check_days} days)', flush=True)

    sent = 0
    errors = 0

    for rec in records:
        if not rec['email']:
            continue

        token = secrets.token_urlsafe(32)
        confirm_url = f"{app_url}/directory/confirm-activity/{token}"
        name = rec['fname'] or rec['callsign']

        body = (
            f"Hello {name},\n\n"
            f"This is a periodic activity check for your coordination record:\n\n"
            f"  Record:      {rec['subdir']}\n"
            f"  Description: {rec['subdsc']}\n\n"
            f"Please confirm that this coordination is still active by clicking the link below:\n\n"
            f"  {confirm_url}\n\n"
            f"If this coordination is no longer in use, please contact your frequency coordinator.\n\n"
            f"73,\nfreqy by NF9K\n"
        )

        try:
            send_email(
                rec['email'],
                f'Freqy — Activity Confirmation Required: {rec["subdir"]}',
                body, cfg, dry_run=dry_run,
            )
            if not dry_run:
                cur.execute(
                    'UPDATE coordination_records SET activity_confirm_token = %s WHERE id = %s',
                    (token, rec['id'])
                )
                conn.commit()
            sent += 1
        except Exception as e:
            print(f'  ERROR sending to {rec["email"]} for {rec["subdir"]}: {e}',
                  file=sys.stderr, flush=True)
            errors += 1

    cur.close()
    conn.close()
    print(f'  Sent: {sent}  Errors: {errors}', flush=True)
    return 1 if errors else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send activity confirmation emails')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print what would be sent without sending or updating DB')
    args = parser.parse_args()
    sys.exit(run(dry_run=args.dry_run))
