-- Migration: Add DE metric columns and bridge_audit table
-- For SQLite (CREATE TABLE IF NOT EXISTS, ALTER TABLE ADD COLUMN)

BEGIN TRANSACTION;

-- Create audit table if not exists
CREATE TABLE IF NOT EXISTS bridge_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bridge_id INTEGER,
    action TEXT NOT NULL,            -- e.g., 'auto_enable', 'auto_disable', 'manual_enable', 'manual_disable', 'metric_update'
    old_value TEXT,
    new_value TEXT,
    reason TEXT,
    actor TEXT,                      -- 'system' or username
    created_at TEXT DEFAULT (datetime('now'))
);

-- Add columns to ManagedBridges table
ALTER TABLE ManagedBridges ADD COLUMN de_win_count_last30 INTEGER DEFAULT 0;
ALTER TABLE ManagedBridges ADD COLUMN de_win_rate_last30 REAL DEFAULT 0.0;
ALTER TABLE ManagedBridges ADD COLUMN de_current_streak INTEGER DEFAULT 0;
ALTER TABLE ManagedBridges ADD COLUMN de_score REAL DEFAULT 0.0;
ALTER TABLE ManagedBridges ADD COLUMN de_auto_enabled INTEGER DEFAULT 0;
ALTER TABLE ManagedBridges ADD COLUMN de_manual_override INTEGER DEFAULT 0;
ALTER TABLE ManagedBridges ADD COLUMN de_manual_override_value INTEGER DEFAULT NULL;
ALTER TABLE ManagedBridges ADD COLUMN de_last_evaluated TEXT DEFAULT NULL;

-- Indexes to speed lookups by type / auto_enabled
CREATE INDEX IF NOT EXISTS idx_managed_bridges_type ON ManagedBridges(type);
CREATE INDEX IF NOT EXISTS idx_managed_bridges_de_auto ON ManagedBridges(de_auto_enabled);

COMMIT;
