# Database Migrations

This directory contains SQL and Python migration scripts for database schema changes.

## Running Migrations

### Backup First!
Always backup your database before running migrations:
```bash
cp data/xo_so_prizes_all_logic.db data/xo_so_prizes_all_logic.db.backup
```

### 001: Add DE Metrics
Adds DE performance metric columns and bridge_audit table.

**Run:**
```bash
python scripts/migrations/add_de_metrics.py
```

**Verify:**
```bash
sqlite3 data/xo_so_prizes_all_logic.db "PRAGMA table_info(ManagedBridges);" | grep de_
sqlite3 data/xo_so_prizes_all_logic.db "SELECT name FROM sqlite_master WHERE name='bridge_audit';"
```

## Migration Safety
- All migrations are idempotent (can run multiple times)
- Transaction-based with rollback on errors
- Check table/column existence before modifications
- Clear logging of all actions
