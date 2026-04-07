# freqy — Claude Code Context

## Project Overview

Docker-based web application for **amateur radio frequency coordination**. Users submit coordination applications; admins manage them through a defined workflow. This is an open source replacement for an existing legacy system (available locally for reference data).

## Stack

| Layer | Choice |
|-------|--------|
| Language | Python 3.x |
| Web framework | Flask |
| Auth | Flask-Login |
| Email | Flask-Mail (SMTP2GO provider) |
| DB driver | MySQLdb with DictCursor |
| Database | MariaDB |
| Password hashing | bcrypt |
| Token generation | `secrets.token_urlsafe(32)` |
| Frontend | Bootstrap 5.3, Bootstrap Icons |
| Templating | Jinja2 (server-side, no SPA) |
| Container | Docker + docker compose |

## Application Workflow

**Application statuses** (from live data):
`New` → `Construction Permit` → `Final`
Other states: `Cancelled`, `Audit`, `On Hold`, `Expired`, `Placeholder`, `Other`

**Application types** (from live data): `Repeater`, `Link`, `Control RX`, `Beacon`, `Other`

**Record lifetime:** Valid for 2 years. Email reminders sent at 90, 60, 30, 14, 7, and 1 day(s) before expiration. Cancelled/expired records have `EXPIRES="N/A"` in legacy data — store as NULL.

## Frequency Bands Supported

Legacy `SFP_BAND` values → display labels:
- `29` → 10m
- `50` → 6m
- `144` → 2m
- `222` → 222
- `440` → 440
- `GHZ` → 902/1240 (catch-all for 900 MHz and 1.2 GHz bands)

## User Roles & Access

**Regular users:**
- Submit new coordination applications
- View and edit their own records (user profile + repeater records)
- Cannot see or edit other users' records
- Password reset via email

**Admins:**
- Full view and edit of any application/applicant
- Change callsign: moves account and all associated records to a new callsign
- Move record: moves a specific record from one callsign/account to another
- Review changes: filter all changes by date range
- Set/change application status

## Key Patterns (from irc-membership-portal)

- **DB connection:** `get_db_connection()` + `dict_cursor()` helpers; parameterized queries only (`%s` placeholders, never string interpolation)
- **Auth:** Flask-Login `UserMixin` class + `@login_manager.user_loader`; `@admin_required` decorator for admin routes
- **Password reset:** `password_reset_tokens` table with `token`, `expires_at` (24hr), `used` (bool); always show success message regardless of email existence (prevents enumeration)
- **Expiration notifications:** Standalone cron script (runs inside Docker); tracks sent notices per threshold in `expiration_notices` table (record_id, days_threshold, sent_at) — one row per threshold per record so each fires exactly once
- **Email:** Flask-Mail config from env vars; plain-text emails with callsign salutation
- **Admin-only fields:** Checked in both template (`{% if current_user.is_admin %}`) and backend before writing
- **AJAX admin actions:** Return `jsonify({'success': bool, 'message': str})`; no page reload for status changes, callsign moves, etc.
- **Session lifetime:** 24 hours (`PERMANENT_SESSION_LIFETIME`)

## Database Schema

### `users` table

| Column | Type | Notes |
|--------|------|-------|
| `id` | INT PK AUTO_INCREMENT | |
| `callsign` | VARCHAR(10) UNIQUE | Login key, stored uppercase; legacy `CALLS` / `UNUM` |
| `password_hash` | VARCHAR(255) | bcrypt; legacy `PASSCODE` is plaintext — hash on import |
| `email` | VARCHAR(255) | Used for notifications and password reset; legacy `EMAIL` |
| `fname` | VARCHAR(100) | Legacy `FNAME` |
| `mname` | VARCHAR(50) | Legacy `MNAME` |
| `lname` | VARCHAR(100) | Legacy `LNAME` |
| `suffix` | VARCHAR(20) | Legacy `SUFFIX` |
| `address` | VARCHAR(255) | Legacy `STADR` |
| `city` | VARCHAR(100) | Legacy `CITYX` |
| `state` | CHAR(2) | Legacy `STATE` |
| `zip` | VARCHAR(10) | Legacy `ZIPCO` |
| `phone_home` | VARCHAR(20) | Legacy `HPHON` |
| `phone_work` | VARCHAR(20) | Legacy `WPHON` |
| `phone_cell` | VARCHAR(20) | Legacy `CPHON` |
| `is_admin` | TINYINT(1) | 0/1 |
| `created_at` | DATETIME | |
| `updated_at` | DATETIME | |

### `password_reset_tokens` table

| Column | Type | Notes |
|--------|------|-------|
| `id` | INT PK AUTO_INCREMENT | |
| `user_id` | INT FK → users.id | |
| `token` | VARCHAR(64) UNIQUE | `secrets.token_urlsafe(32)` |
| `expires_at` | DATETIME | 24hr from creation |
| `used` | TINYINT(1) | Default 0; set 1 after use |
| `created_at` | DATETIME | |

### `coordination_records` table

| Column | Type | Notes |
|--------|------|-------|
| `id` | INT PK AUTO_INCREMENT | |
| `subdir` | VARCHAR(20) UNIQUE | Legacy record ID e.g. `A00315` |
| `subdsc` | VARCHAR(255) | Short description |
| `user_id` | INT FK → users.id | Account owner (legacy `CALLS`) |
| `secondary_contact_id` | INT FK → users.id | Alternate contact — one max, NULL if none |
| `system_id` | VARCHAR(10) | System callsign — may differ from account owner (legacy `SYSTEM_ID`) |
| `parent_record_id` | INT FK → coordination_records.id | NULL if top-level |
| `app_type` | VARCHAR(20) | `Repeater`, `Link`, `Control RX`, `Beacon`, `Other` |
| `status` | VARCHAR(30) | See workflow above |
| `last_action` | VARCHAR(100) | |
| `inherit` | TINYINT(1) | |
| `willbe` | VARCHAR(50) | Access type e.g. `Open` |
| `eq_ready` | TINYINT(1) | |
| `eq_ready_date` | DATE | |
| `orig_date` | DATE | |
| `mod_date` | DATE | |
| `expires_date` | DATE | Drive expiration notifications |
| `comments` | TEXT | User-visible |
| `audit_comments` | TEXT | Admin-only |
| `rdnotes` | VARCHAR(100) | Mode shorthand e.g. `Oe(XB)x` |
| `rdnotes2` | VARCHAR(100) | e.g. `[DMR:CC1]` |
| `created_at` | DATETIME | |
| `updated_at` | DATETIME | |
| **Frequency** | | |
| `band` | VARCHAR(10) | e.g. `440` |
| `freq_output` | DECIMAL(8,4) | MHz |
| `freq_input` | DECIMAL(8,4) | MHz |
| `bandwidth` | VARCHAR(30) | e.g. `Very Narrow` |
| `emission_des` | VARCHAR(20) | e.g. `7K60FXE` |
| `emission_des2` | VARCHAR(20) | |
| **Tone / Digital** | | |
| `tx_pl` | VARCHAR(10) | CTCSS tone Hz |
| `rx_pl` | VARCHAR(10) | |
| `tx_dcs` | VARCHAR(10) | DCS code |
| `dmr_cc` | TINYINT | Color code 0–15 |
| `p25_nac` | VARCHAR(10) | |
| `nxdn_ran` | VARCHAR(10) | |
| `fusion_dsq` | VARCHAR(10) | |
| **TX Site** | | |
| `tx_power` | SMALLINT | Watts |
| `loc_lat` | DECIMAL(9,6) | Decimal degrees (positive N) |
| `loc_lng` | DECIMAL(9,6) | Decimal degrees (negative W) — legacy `LOC_LNGDISP` is stored **positive**, negate on import |
| `loc_building` | VARCHAR(255) | |
| `loc_street` | VARCHAR(255) | |
| `loc_city` | VARCHAR(100) | |
| `loc_county` | VARCHAR(100) | |
| `loc_state` | CHAR(2) | |
| **TX Antenna** | | |
| `ant_type` | VARCHAR(50) | |
| `ant_gain` | DECIMAL(5,2) | dBd |
| `ant_haat` | SMALLINT | ft above average terrain |
| `ant_amsl` | SMALLINT | ft above mean sea level |
| `ant_ahag` | SMALLINT | ft above ground |
| `ant_favor` | VARCHAR(50) | Favored direction |
| `ant_beamwidth` | VARCHAR(20) | |
| `ant_frontback` | VARCHAR(20) | |
| `ant_polarization` | VARCHAR(10) | |
| `ant_comment` | VARCHAR(255) | e.g. `300' 7/8` |
| `fdl_loss` | DECIMAL(5,2) | dB |
| **RX Site** | | |
| `rx_lat` | DECIMAL(9,6) | NULL if same as TX; same sign convention — negate on import |
| `rx_lng` | DECIMAL(9,6) | NULL if same as TX |
| **RX Antenna** | | |
| `ant_type_rx` | VARCHAR(50) | |
| `ant_gain_rx` | DECIMAL(5,2) | |
| `ant_ahag_rx` | SMALLINT | |
| `ant_favor_rx` | VARCHAR(50) | |
| `ant_beamwidth_rx` | VARCHAR(20) | |
| `ant_frontback_rx` | VARCHAR(20) | |
| `ant_polarization_rx` | VARCHAR(10) | |
| `ant_comment_rx` | VARCHAR(255) | |
| `fdl_loss_rx` | DECIMAL(5,2) | |

### `expiration_notices` table

Tracks which reminder thresholds have fired for each record (prevents duplicate sends).

| Column | Type | Notes |
|--------|------|-------|
| `id` | INT PK AUTO_INCREMENT | |
| `record_id` | INT FK → coordination_records.id | |
| `days_threshold` | SMALLINT | 90, 60, 30, 14, 7, or 1 |
| `sent_at` | DATETIME | |

Unique constraint on `(record_id, days_threshold)`.

## Deploy Process

When shipping a feature:
1. Update `README.md` and `docs/user-manual.md` to reflect the change
2. Commit everything together (code + docs in one commit, or docs as immediate follow-up)
3. Build: `docker build --build-arg VERSION=X.XX -t nf9k/freqy:X.XX -t nf9k/freqy:latest .`
4. Push: `docker push nf9k/freqy:X.XX && docker push nf9k/freqy:latest`
5. Deploy: `ssh root@docker-core "cd /docker/arcane/data/projects/freqy && docker compose pull web && docker compose up -d web"`

Use `compose.yml`, not `docker-compose.yml`.

## Preferences

- Dates displayed to the user: **MM/DD/YYYY**
- Times displayed to the user: **military, no colon — HHMM** (e.g. 1430)

## Conventions

- Python: no type annotations required, no docstrings unless logic is non-obvious.
- All DB queries parameterized — never interpolate user input into SQL strings.
- All LDAP/DB logic in dedicated modules; routes stay thin.
- No error handling for scenarios that can't happen — only validate at system boundaries (user input, external APIs).
