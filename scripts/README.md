# Scripts

## import_legacy.py

Imports legacy Flexweb flat-file data into freqy-database.

```bash
# Dry run (no DB writes, fast)
python scripts/import_legacy.py --dry-run /path/to/legacy_data/

# Live import (requires DB running and .env configured)
python scripts/import_legacy.py /path/to/legacy_data/
```

Safe to re-run — uses INSERT/UPDATE (upsert) on callsign/subdir.
