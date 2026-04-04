# freqy-database — User Manual

**Amateur Radio Frequency Coordination Database**

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
9. [Admin Guide](#admin-guide)
   - [User Management](#user-management)
   - [Record Management](#record-management)
   - [Review Changes](#review-changes)
   - [FCC Callsign Lookup](#fcc-callsign-lookup)
10. [Application Statuses](#application-statuses)
11. [Frequency Bands](#frequency-bands)
12. [Technical Reference](#technical-reference)

---

## Overview

freqy-database is a web-based frequency coordination management system for amateur radio operators. It replaces legacy flat-file coordination systems with a modern, searchable database accessible from any browser.

**Key capabilities:**

- Submit and track coordination applications for repeaters, links, control receivers, and beacons
- View coordination details including frequency, tone/digital access, site information, and antenna data
- Receive automated email reminders when your coordination is approaching expiration
- Manage your account profile and secondary contacts
- Administrators can manage all records and users across the system

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

Enter your callsign and password on the login page. Sessions last 24 hours.

---

## Dashboard

After logging in you are taken to your dashboard, which shows all coordination records associated with your account — either as the primary owner or secondary contact.

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

## Coordination Records

### Record Detail

The record detail page shows all information for a coordination in a tabbed layout:

- **Overview** — status, dates, system ID, access type
- **Frequency** — output/input frequencies, bandwidth, emission designators, tone/digital access codes
- **Site & Antenna** — TX site location with map, antenna specifications, RX site if separate
- **System** — sponsor information
- **Trustee** — trustee contact information
- **Notes** — user-visible comments and changelog

### Secondary Contact

If you are the record owner, you can set a secondary contact callsign directly on the record detail page. The secondary contact can view the record on their dashboard and edit it.

To set or change: enter the callsign in the **Secondary Contact** field and click **Update**.

To remove: clear the field and click **Update**.

### Changelog

Every change to a record is logged at the bottom of the Notes tab, showing who made the change and when.

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
- **Sponsor** — sponsoring organization name, abbreviation, and website

### Frequency Tab
- **Band** *(required)* — select the frequency band; the input frequency will be calculated automatically from the standard offset for the selected band
- **Output Freq** *(required)* — output frequency in MHz
- **Input Freq** — auto-calculated; override if non-standard split
- **Bandwidth** — 12.5 kHz, 20 kHz, or 25 kHz
- **Emission Designator** — FCC emission designator; common values are available in the dropdown
- **TX Power** — transmitter power in watts
- **ERP** — calculated automatically from TX power, antenna gain, and feedline loss
- **Tone / Digital Access** — CTCSS (TX/RX), DCS (TX/RX), DMR Color Code, P25 NAC, NXDN RAN, Fusion DSQ

### Site & Antenna Tab
- **TX Site Location** — building, street, city, county, state, region
- **Coordinates** — latitude/longitude; click the map to set, or drag the marker to adjust
- **TX Antenna** — type, gain (dBd), HAAT, AMSL, HAGL, polarization, feedline loss, favored direction, beamwidth, front-to-back ratio
- **RX Site** — if the receive site differs from the transmit site, enter RX coordinates and antenna data here

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
- **Site & Antenna tab** — TX site, antenna, RX site
- **System tab** — sponsor information
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

### FCC Callsign Lookup

The system maintains a local copy of the FCC ULS amateur license database, updated daily. Lookups are instant and work offline. The database is populated automatically when the stack starts and refreshed every 24 hours.

FCC data is available in three places:

| Location | Behavior |
|----------|----------|
| Registration form | Pre-fills name and address on callsign blur |
| Profile / Admin user edit | Compares FCC record against current profile; apply button to update |
| New application — System ID | Shows licensee name + license class + Active/Expired status as a validation hint |

---

## Application Statuses

| Status | Description |
|--------|-------------|
| **New** | Application received, pending review |
| **Construction Permit** | Approved for construction; not yet final |
| **Final** | Coordination complete and active |
| **On Hold** | Pending additional information |
| **Audit** | Under review |
| **Expired** | Coordination has lapsed |
| **Cancelled** | Coordination withdrawn or revoked |
| **Placeholder** | Reserved record; not active |
| **Other** | Miscellaneous status |

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

## Technical Reference

### Record IDs

Legacy records imported from the Flexweb system retain their original IDs (format `A00001`). New records submitted through this system are assigned sequential IDs starting at `B00001`.

### Expiration

Coordination records are valid for 2 years. Automated email reminders are sent to the record owner and secondary contact at 90, 60, 30, 14, 7, and 1 day(s) before expiration. Each threshold fires exactly once per record.

Records with status Cancelled, Expired, or Placeholder do not receive expiration notices.

### Coordinate Convention

Coordinates are stored in decimal degrees. Latitude is positive north. Longitude is negative west (standard US convention), e.g. Chicago is approximately `41.881, -87.623`.

---

*freqy-database — open source frequency coordination for amateur radio*
*https://github.com/nf9k/freqy-database*
