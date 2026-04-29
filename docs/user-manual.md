# freqy — User Manual

**Amateur Radio Frequency Coordination**

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Dashboard](#dashboard)
4. [Coordination Records](#coordination-records)
5. [Submitting a New Application](#submitting-a-new-application)
6. [Editing Your Record](#editing-your-record)
7. [Your Profile](#your-profile)
8. [Password Management](#password-management)
9. [Two-Factor Authentication](#two-factor-authentication)
10. [Admin Guide](#admin-guide)
   - [User Management](#user-management)
   - [Record Management](#record-management)
   - [Review Changes](#review-changes)
   - [Coordination/NOPC Check](#coordinationnopc-check)
   - [Coverage Plots](#coverage-plots)
   - [DB Export](#db-export)
   - [FCC Callsign Lookup](#fcc-callsign-lookup)
11. [Application Statuses](#application-statuses)
12. [Frequency Bands](#frequency-bands)
13. [Technical Reference](#technical-reference)

---

## Overview

freqy is a web-based frequency coordination management system for amateur radio operators. It replaces legacy flat-file coordination systems with a modern, searchable database accessible from any browser.

**Key capabilities:**

- Submit and track coordination applications for repeaters, links, control receivers, and beacons
- View coordination details including frequency, tone/digital access, site information, and antenna data
- Receive automated email reminders when your coordination is approaching expiration
- Manage your account profile and secondary contacts
- Administrators can manage all records and users across the system

### Feature Access by Role

| Feature | User | Admin |
|---------|:----:|:-----:|
| Dashboard (own records) | Yes | ✓ |
| Dashboard Final Only filter | Yes | ✓ |
| Submit new application | Yes | ✓ |
| Edit own records | Yes | ✓ |
| Profile / password / 2FA | Yes | ✓ |
| Repeater directory + map | Yes | ✓ |
| CHIRP export | Yes | ✓ |
| Band plan visualization | Yes | ✓ |
| Applications list | — | Yes |
| User management | — | Yes |
| Edit any record | — | Yes |
| Review changes | — | Yes |
| DB export (CSV/JSON/XML/PDF) | — | Yes |
| Coordination/NOPC check | — | Yes |
| Pair finder | — | Yes |
| Distance calculator | — | Yes |
| Coverage plots (KMZ) | — | Yes |
| Send NOPC | — | Yes |
| Activity report | — | Yes |
| Status changes | — | Yes |

---

## Getting Started

### Creating an Account

1. Navigate to the login page and click **Create account**
2. Enter your **callsign** — the system will look up your FCC license record and pre-fill your name and address
3. Enter your **email address** — required for password recovery and expiration notices
4. Choose a **password** (minimum 8 characters)
5. Click **Create Account**
6. Log in with your callsign and password

> **Note:** Your callsign is your login username. It is stored and displayed in uppercase.

### Logging In

Enter your callsign and password on the login page. Sessions last 24 hours. If two-factor authentication is enabled on your account, you will be prompted for a verification code after your password is accepted.

---

## Dashboard

After logging in you are taken to your dashboard, which shows all coordination records where your account is the primary owner.

### Filter: Final Only

A toggle button appears next to the **New Application** button at the top of the dashboard. Click it to switch between showing **All Records** or **Final Only**. When set to Final Only, the dashboard hides records in other statuses (New, Construction Permit, Cancelled, etc.) and shows only your active, finalized coordinations. This preference is saved to your account and persists across sessions.

**Columns shown:**

| Column | Description |
|--------|-------------|
| Record | Legacy or system-assigned record ID |
| Description | Short description of the coordination |
| Band | Frequency band |
| Output | Output frequency in MHz |
| Location | City and region |
| Status | Current status badge |
| Expires | Expiration date |

Click any row to open the record detail view.

Click **New Application** to submit a new coordination request.

---

## Repeater Directory

The **Directory** link in the navigation bar opens a searchable listing of all Final (coordinated) repeaters.

**Filters:**

| Filter | Description |
|--------|-------------|
| Search | Text search across callsign, city, frequency, description |
| Band | Filter by frequency band |
| Type | Filter by application type (Repeater, Link, etc.) |
| Region | Filter by geographic region |
| State | Filter by state (2-letter code) |

**Views:**

- **Table** — sortable columns (click any header to sort). Click a row to open the read-only record detail.
- **Map** — Leaflet map with markers for all matching records. Click a marker popup for details.

### CHIRP Export

Click the **CHIRP Export** button on the directory page to download a CSV file compatible with CHIRP radio programming software. The export respects the current filters (band, region, etc.).

Import the file into CHIRP via **File → Import** to program your radio with coordinated repeater frequencies, tones, and offsets.

---

## Band Plan Visualization

The **Band Plan** link in the navigation bar shows a graphical spectrum display of occupied channels.

1. Select a band using the buttons at the top
2. Each vertical bar represents an occupied frequency, color-coded by status:
   - **Green** — Final (coordinated)
   - **Yellow** — Construction Permit
   - **Blue** — On Hold / Audit
3. Hover over a bar to see the record details (callsign, frequency, city, status)
4. Click a bar to open the record detail

---

## Coordination Records

### Record Detail

The record detail page shows all information for a coordination in a tabbed layout:

- **Overview** — status, dates, system ID, access type
- **Frequency** — output/input frequencies, bandwidth, emission designators, tone/digital access codes
- **Site & Antenna** — TX site location with inline Leaflet map, antenna specifications, RX site if separate (shown as second marker on map)
- **Sponsor** — sponsor information
- **Trustee** — trustee contact information
- **Linked Records** — if this record has child records (e.g., links, control receivers) or siblings under the same parent, they are listed with clickable links
- **Notes** — user-visible comments and changelog

### Secondary Contact

If you are the record owner, you can set a secondary contact callsign directly on the record detail page. The secondary contact can view the record by navigating to it directly.

To set or change: enter the callsign in the **Secondary Contact** field and click **Update**.

To remove: clear the field and click **Update**.

### Changelog

Every change to a record is logged at the bottom of the Notes tab, showing who made the change and when.

### Change Notifications

When an administrator edits your record, you will receive an email listing each field that changed, with the old and new values. No email is sent when you edit your own record.

---

## Submitting a New Application

Click **New Application** from the dashboard or navigation menu.

The form is organized into tabs:

### System Tab
- **System ID** *(required)* — the callsign of the system (may differ from your account callsign). The system will verify this against the FCC database and show the licensee name and license status.
- **App Type** *(required)* — Repeater, Link, Control RX, Beacon, or Other
- **Description** — short human-readable description, e.g. `W9XYZ/R 146.940 Chicago`
- **Access / Willbe** — Open, Closed, Private, etc.
- **Secondary Contact** — optional alternate contact callsign
- **Equipment Ready** — check if equipment is installed and operational

### Sponsor Tab
- **Sponsor** — sponsoring organization name, abbreviation, and website

### Frequency Tab
- **Band** *(required)* — select the frequency band; the input frequency will be calculated automatically from the standard offset for the selected band
- **Output Freq** *(required)* — output frequency in MHz
- **Input Freq** — auto-calculated; override if non-standard split
- **Bandwidth** — 12.5 kHz or 25 kHz
- **Emission Designator** — FCC emission designator; common values are available in the dropdown
- **TX Power** — transmitter power in watts
- **ERP** — effective radiated power in watts
- **Tone / Digital Access** — CTCSS (TX/RX), DCS (TX/RX), DMR Color Code, P25 NAC, NXDN RAN, Fusion DSQ

### Site & Antenna Tab
- **TX Site Location** — building, street, city, county, state, region
- **Coordinates** — latitude/longitude; click the map to set, or drag the marker to adjust
- **TX Antenna** — type, gain (dBd), HAAT, AMSL, HAGL, polarization, feedline loss, favored direction, beamwidth, front-to-back ratio
- **RX Site / Antenna** — check **Same as TX** to hide this section (default). Uncheck to enter separate RX coordinates and antenna data if the receive site differs from the transmit site.

### Trustee Tab
Trustee name, callsign, email, and phone numbers.

### Notes Tab
Free-text comments about the coordination request.

---

Once submitted, the application is assigned a record ID (format `B00001`, `B00002`, etc.) and its status is set to **New**. An administrator will review and process the application.

---

## Editing Your Record

If you are the record owner, an **Edit Record** button appears on the record detail page.

You can edit all technical fields — frequency, site, antenna, system info, notes, trustee — but not administrative fields such as status, expiration dates, or audit comments. Those are managed by administrators.

Saving an edit automatically updates the **Mod Date** and adds a changelog entry.

---

## Your Profile

Access your profile via the user menu in the top-right corner → **My Profile**.

You can update your name, email address, phone numbers, and mailing address.

**Refresh from FCC** — click this button to compare your profile against the FCC license database. If your FCC record differs from your profile, a comparison panel shows old vs. new values. Click **Apply FCC Data** to update your profile with the FCC values, then save.

---

## Password Management

### Change Password

Go to the user menu → **Change Password**. Enter your current password and choose a new one (minimum 8 characters).

### Forgot Password

On the login page, click **Forgot password?** Enter the email address on file for your account. If a match is found, a reset link is emailed to you. The link expires in 24 hours.

---

## Two-Factor Authentication

Two-factor authentication (2FA) adds a second verification step at login. It is optional but recommended.

Access 2FA settings via the user menu → **Security & 2FA**.

### Authenticator App (TOTP)

1. Click **Set Up** next to Authenticator App
2. Click **Generate QR Code**
3. Scan the QR code with your authenticator app (Google Authenticator, Authy, 1Password, etc.) — or enter the text key manually if your app supports it
4. Enter the 6-digit code shown in your app to confirm it's working
5. Your app is linked and 2FA is enabled

After setup, a set of **backup codes** is displayed. Save these somewhere safe — each code can be used once if you lose access to your authenticator app.

### Security Keys (YubiKey / FIDO2)

1. Click **Add Key** next to Security Keys
2. Give the key a name (e.g. "YubiKey 5")
3. Click **Touch Security Key to Register** and tap your key when prompted
4. The key is registered and can be used at login

You can register multiple keys. To remove a key, click **Remove** next to it in the Security Keys list.

### Logging In with 2FA

After entering your callsign and password, you are taken to a verification page:

- **Authenticator app** — enter the 6-digit code shown in your app
- **Security key** — click **Use Security Key** and tap your key
- **Backup code** — enter one of your saved backup codes if you don't have access to your other methods

### Backup Codes

Backup codes are available under **Security & 2FA → Backup Codes**. The page shows how many unused codes remain. To regenerate a fresh set, confirm your password and click **Regenerate Backup Codes** — this invalidates all existing codes.

> If you have 2 or fewer codes remaining, freqy will remind you to regenerate them after a successful backup code login.

### Disabling 2FA

At the bottom of the Security & 2FA page, enter your password and click **Disable 2FA**. This removes your authenticator app, all registered security keys, and all backup codes.

---

## Admin Guide

Administrators have an **Admin** menu in the navigation bar with access to Applications, Users, and Review Changes.

### User Management

**Users list** (`Admin → Users`)

Shows all accounts with record counts. Search by callsign, name, or email. Click any row to open the user detail page. Click **Add User** to create a new account.

---

**User detail page**

Displays and edits all profile information for a user. Additional sidebar cards:

**FCC License Data** — automatically looks up the user's callsign in the FCC database when the page loads. Shows license class (Extra, General, etc.) and status (Active/Expired). If FCC data differs from the profile, a comparison table highlights mismatches in amber. Click **Apply FCC Data** to fill in the form, then **Save Changes**.

**Password Reset** — sends a password reset link to the user's email address.

**Delete User** — permanently removes the account. Blocked if the user has records attached.

**Records** — sidebar list of all records owned by or associated with this user. Click any row to open the record.

---

**Adding a user** (`Admin → Users → Add User`)

Enter the callsign, optional name, optional email, and admin checkbox. If an email address is provided, the system sends an account creation email with a password-set link. If no email is provided, use the Reset Password button on their profile to send a link later.

---

### Record Management

**Applications list** (`Admin → Applications`)

Searchable, filterable list of all coordination records. Filter by status, band, region, and app type, or search by record ID, description, system ID, or city.

---

**Editing a record** (`Edit Record` button on any record detail page)

Administrators have access to all fields including:

- **Status tab** — status, last action, audit comments, dates (orig/mod/expires), equipment ready, inherit flag
- **Frequency tab** — all frequency and tone/digital fields
- **Site & Antenna tab** — TX site, antenna, RX site (with "Same as TX" toggle)
- **Sponsor tab** — sponsor information
- **Notes tab** — user comments and audit comments
- **Trustee tab** — trustee information

**Status** can be updated quickly from the record detail page without opening the full edit form — use the status panel on the right side of the record detail.

---

### Review Changes

`Admin → Review Changes` shows a searchable changelog of all record modifications.

**Filters:**

| Filter | Description |
|--------|-------------|
| From / To | Date range |
| Changed By | Filter by callsign |
| Record | Filter to a specific record ID |

Results are capped at 500 entries. Click any row to open the record.

---

### Coordination/NOPC Check

The **Coordination/NOPC Check** button in the top navigation bar opens the frequency coordination check tool (admin only).

**Purpose:** Before issuing a coordination or processing an NOPC, check a proposed output frequency against existing records for co-channel and adjacent-channel separation conflicts.

**Step 1 — Enter coordinates** using one of three modes:

| Mode | Description |
|------|-------------|
| Decimal | Enter latitude and longitude as decimal degrees (negative for West/South) |
| DMS | Enter degrees, minutes, seconds with N/S and E/W selectors |
| Map | Click the map to place a marker; drag to adjust |

**Step 2 — Enter the output frequency** in MHz. A band detection hint confirms the coordinated band.

**Step 3 — Click Check Frequency.** Results are split into two tables:

**Co-channel** — records on the same frequency (within 0.1 kHz). Minimum separation is 120 miles for all bands. Failing records (under the minimum) are highlighted in red.

**Adjacent channel** — records within the adjacent channel window for the band. Separation requirements vary by offset and band per IRC Coordination Policy v1.1:

| Band | Offset ≤ | Min Separation |
|------|----------|---------------|
| 6m | 20 kHz | 20 mi |
| 2m | 10 kHz | 40 mi |
| 2m | 15 kHz | 30 mi |
| 2m | 20 kHz | 25 mi |
| 2m | 30 kHz | 20 mi |
| 222 | 20 kHz | 25 mi |
| 222 | 40 kHz | 5 mi |
| 440 | 25 kHz | 5 mi |
| 440 | 50 kHz | 1 mi |
| 902/1296 | same as 440 | |

Results include only active records (status: Final, Construction Permit, On Hold, or Audit). Each row links to the full record. A green check indicates the separation rule is met; a red X with the actual distance indicates a conflict.

> **Note:** Separation distances are configurable via environment variables if your region uses different rules. `FREQ_CO_CHANNEL_MILES` accepts a JSON object keyed by band (`"50"`, `"144"`, `"222"`, `"440"`, `"902"`, `"1296"`) with the minimum co-channel separation in miles for each. `FREQ_ADJ_RULES` accepts a JSON object with the same band keys, each containing a list of `[max_offset_khz, min_separation_miles]` pairs.

---

### Pair Finder

The **Pair Finder** button in the top navigation bar opens the frequency pair suggestion tool (admin only).

**Purpose:** Find available frequency pairs for a given band and location, based on IRC coordination rules and existing coordinations.

1. Select a **band** from the dropdown
2. Enter coordinates by clicking the map or typing latitude/longitude
3. Click **Find Pairs**

Results show all standard channels for the selected band per the IRC band plan, sorted by clearance margin (cleanest first):

- **Occupied** (red) — frequency is already coordinated
- **Conflict** (yellow) — adjacent channel separation rule violated
- **Available** (green) — passes all co-channel and adjacent separation rules
- **Clear** (green) — no nearby records at all

Each row shows the candidate output/input frequencies, the nearest existing record, distance, and required separation. All separation distances follow IRC Coordination Policy v1.1 Section 7.

> **Note:** The 902 MHz band correctly excludes the 927.075–927.125 simplex segment from candidate pairs.

---

### Distance Calculator

`Admin → Tools → Distance Calculator` computes the great circle (Haversine) distance between two points.

1. Click the map to set **Point A** (blue marker), click again for **Point B** (red marker)
2. Or enter coordinates manually in the four fields
3. Click **Calculate Distance**

The result shows the distance in both miles and kilometers. A dashed green line connects the two points on the map. Click the map again to reset and start over.

This is useful when evaluating repeater move requests or checking separation distances by hand.

---

### Coverage Plots

`Admin → Tools → Coverage Plots` generates KMZ signal coverage overlays for eligible records using an external Signal Server instance.

**Prerequisites:** The `SIGNAL_SERVER_URL` environment variable must point to a running Signal Server wrapper (default: `http://signal-server:5001`). Generated KMZ files are stored in the directory set by `KMZ_DIR` (default: `/data/kmz`), which is mounted as a Docker volume.

**Page layout:**

- **Stats row** — counts of eligible records, records with plots, failures, and pending records
- **Batch Generation** — enter how many pending records to process, then click **Generate**. A progress bar shows the current record and running totals. The page reloads automatically when the batch completes.
- **Records table** — one row per eligible record (those with TX coordinates and output frequency). Each row shows the plot status (date generated, error, or pending) and two action buttons:
  - Download KMZ — saves the `.kmz` file locally for import into Google Earth or similar
  - Regenerate — triggers a fresh plot for that record, replacing any existing result

**ERP calculation:** Effective radiated power is computed from TX power (W), antenna gain (dBd), and feedline loss (dB). If TX power is not set, 10 W is assumed.

Records missing TX latitude/longitude or output frequency are excluded from the table.

---

### Activity Report

`Admin → Activity` shows Final records that have not confirmed activity within the configured interval (default: 365 days).

Each row has a checkmark button to manually mark a record as confirmed (e.g., after a phone or in-person confirmation). Automated email confirmations are sent by the `send_activity_checks.py` cron script, which emails owners a one-click confirmation link.

The check interval is configurable via the `ACTIVITY_CHECK_DAYS` environment variable.

---

### Send NOPC

On any record detail page, admins can click the green **Send NOPC** button to notify adjacent area frequency coordinators about a new or changed coordination.

1. Click **Send NOPC** — a modal opens with a preview of the email
2. Select the **From** address from the dropdown (configured via `NOPC_EMAIL_FROM`)
3. Review the message — it includes system info, trustee details, site/antenna data, and computed EIRP/ERP
4. The **To** line shows the configured recipient list
5. Click **Send NOPC** to send, or **Close** to cancel

The recipient list is configured via `NOPC_EMAIL_TO` and the sender addresses via `NOPC_EMAIL_FROM` (both comma-separated). The button will display an error if either is not set.

The email subject follows the format: `New NOPC from Indiana: [output frequency]`

---

### DB Export

`Admin → DB Export` provides a one-click download of all **Final** status coordination records. User accounts are not included.

| Format | Description |
|--------|-------------|
| CSV | All fields, spreadsheet compatible; title on first line as a `#` comment |
| JSON | All fields, machine readable; wrapped as `{"title": "...", "records": [...]}` |
| XML | All fields, structured data exchange; title as root element attribute |
| PDF | Key fields in a printable landscape table; title centered at top of each page |

The title line is configurable via the `EXPORT_TITLE` environment variable. Use `{date}` as a placeholder for the current date (formatted MM/DD/YYYY). Default: `Frequency Coordination Database Export as of {date}`.

---

### FCC Callsign Lookup

The system maintains a local copy of the FCC ULS amateur license database, updated daily. Lookups are instant and work offline. The database is populated automatically when the stack starts and refreshed every 24 hours.

FCC data is available in three places:

| Location | Behavior |
|----------|----------|
| Registration form | Pre-fills name and address on callsign blur |
| Profile / Admin user edit | Compares FCC record against current profile; apply button to update |
| New application — System ID | Shows licensee name + license class + Active/Expired status as a validation hint |

### ZIP Code Lookup

On profile and admin user edit forms, entering a ZIP code and tabbing out will automatically look up city and state from the same local FCC dataset.

- If the city field is empty, city and state are filled automatically
- If the city field already has a value (e.g. pre-filled by callsign lookup), matching options appear as clickable badges below the ZIP field without overwriting the current value
- If the ZIP maps to multiple cities, the first result auto-fills and alternates appear as clickable badges

---

## Application Statuses

| Status | Description |
|--------|-------------|
| **New** | Application recently submitted to the system. |
| **Construction Permit** | Trustee has 180 days from grant date to get the repeater in place and in operation. |
| **Final** | Coordination has been granted and is in good standing with the IRC. |
| **On Hold** | Application is on hold pending NOPC process or other administrative action. |
| **Audit** | Record is under administrative review. |
| **Expired** | Two years have passed since last update by trustee. Coordination is no longer in good standing with the IRC. Expired coordinations may be subject to frequency pair forfeiture. |
| **Cancelled** | Coordination surrendered or cancelled due to other administrative action and is therefore invalid. |
| **Placeholder** | Coordinator use only. Intended to communicate in-flight coordination to other coordinators. |
| **Other** | Contact the coordination team to find out what's going on. |

---

## Frequency Bands

| Band | Display | Standard Offsets |
|------|---------|-----------------|
| 29 | 10m | +100 kHz |
| 50 | 6m | +1.000 MHz |
| 144 | 2m | ±600 kHz (below/above 147.000) |
| 222 | 222 | -1.600 MHz |
| 440 | 440 | ±5.000 MHz (below/above 445.000) |
| GHZ | 902/1240 | — |

---

## IRC Policy Compliance

freqy enforces and references IRC Coordination Policy v1.1 in the following areas:

**Geographical separation** (Section 7) — the Coordination/NOPC Check and Pair Finder tools apply the official co-channel (120 miles all bands) and adjacent channel separation rules per the policy table.

**Band plan channels** (Section 6) — the Pair Finder generates candidate frequencies only within IRC-designated repeater output sub-bands, with correct channel spacing and offsets per band.

**Default digital codes** (Section 8.2.7) — when entering digital access codes on the new application or record edit forms, a yellow advisory note appears if a prohibited default code is selected:

| Code Type | Prohibited Values |
|-----------|------------------|
| DMR Color Code | 1 |
| P25 NAC | $293, $F7E, $F7F |
| NXDN RAN | 0 |
| Fusion DSQ | 0 |

These warnings are advisory only and do not prevent saving.

---

## Technical Reference

### Record IDs

Records imported from a legacy system retain their original IDs (format `A00001`). New records submitted through freqy are assigned sequential IDs starting at `B00001`.

### Expiration

Coordination records are valid for 2 years. Automated email reminders are sent to the record owner and secondary contact at 90, 60, 30, 14, 7, and 1 day(s) before expiration. Each threshold fires exactly once per record.

Records with status Cancelled, Expired, or Placeholder do not receive expiration notices.

### Coordinate Convention

Coordinates are stored in decimal degrees. Latitude is positive north. Longitude is negative west (standard US convention), e.g. Chicago is approximately `41.881, -87.623`.

---

*freqy — open source frequency coordination for amateur radio*
*https://github.com/nf9k/freqy-database*
