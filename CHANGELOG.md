# Changelog

All notable changes to freqy are documented here.

## [Unreleased]

### Added
- Status badge tooltips with plain-language descriptions for all coordination statuses
- Version footer displaying `freqy vX.XX by NF9K` (centered, bottom of page)
- `CONTRIBUTORS.md` crediting K9MMQ for the status tooltip suggestion
- `CLAUDE.md` added to repo; environment-specific details moved to local config
- README screenshot images and missing `review_changes` screenshot
- License class field replaced text input with a select dropdown
- **Coordination/NOPC Check** tool: admin-only frequency conflict checker with co-channel and adjacent-channel separation rules (Haversine distance)
- Co-channel and adjacent-channel separation rules configurable via `FREQ_CO_CHANNEL_MILES` and `FREQ_ADJ_RULES` env vars
- DNS readiness loop in `fcc-import` container startup to handle network attachment race condition
- Sandbox reset script on docker-core: nightly cron pulls fresh Flexweb data, purges non-admin DB records, re-imports

### Changed
- App renamed from **freqy-database** to **freqy** throughout (Docker project, volumes, directory)
- README and user manual updated: name sync, status descriptions, build instructions, Coordination/NOPC Check docs
- Admin navigation replaced dropdown with inline nav items and separator
- Base Docker image bumped to `python:3.13-slim`
- Widened `ant_type` and `loc_region` columns for legacy data compatibility
- `docker-compose.yml` renamed to `compose.yml`
- FCC import streams download to tempfile instead of BytesIO to prevent OOM kill on large zips

### Fixed
- Legacy import `parse_decimal` NaN handling
- Legacy import state field accepts full state names (e.g. "Indiana" → "IN")
- Legacy import NaN values on any field sanitized before INSERT to prevent MySQL errors
- Admin user detail incorrectly showing secondary contact records
- User manual inaccuracies
- License reference corrected from MIT to GPLv3
- Edit record form submission failing with 405 Method Not Allowed (history.replaceState URL mismatch)
- Frequency input field trailing zero truncation (146.940 preserved as entered)

### Removed
- Employer disclaimer removed from README

---

## [0.1.0] — 2026-04-04

- Initial application source, documentation, and Docker deployment added
- Project initialized
