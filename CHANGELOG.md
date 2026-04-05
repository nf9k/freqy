# Changelog

All notable changes to freqy are documented here.

## [Unreleased]

### Added
- Status badge tooltips with plain-language descriptions for all coordination statuses
- Version footer displaying `freqy vX.XX by NF9K`
- `CONTRIBUTORS.md` crediting K9MMQ for the status tooltip suggestion
- `CLAUDE.md` added to repo; environment-specific details moved to local config
- README screenshot images and missing `review_changes` screenshot
- License class field replaced text input with a select dropdown

### Changed
- App renamed from **freqy-database** to **freqy** throughout
- README and user manual updated: name sync, status descriptions, build instructions
- Admin navigation replaced dropdown with inline nav items and separator
- Base Docker image bumped to `python:3.13-slim`
- Widened `ant_type` and `loc_region` columns for legacy data compatibility

### Fixed
- Legacy import `parse_decimal` NaN handling
- Admin user detail incorrectly showing secondary contact records
- User manual inaccuracies
- License reference corrected from MIT to GPLv3

### Removed
- Employer disclaimer removed from README

---

## [0.1.0] — 2026-04-04

- Initial application source, documentation, and Docker deployment added
- Project initialized
