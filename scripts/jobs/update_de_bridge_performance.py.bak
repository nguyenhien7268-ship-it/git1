#!/usr/bin/env python3
"""
Job: Update DE Bridge Performance Metrics

Computes and persists DE metrics for all DE_* bridges:
- de_win_count_last30: Win count in last 30 periods
- de_win_rate_last30: Win rate percentage
- de_current_streak: Current winning/losing streak
- de_score: Calculated bridge score
- de_auto_enabled: Auto-enable flag with hysteresis
- de_last_evaluated: Last evaluation timestamp

Creates audit entries when de_auto_enabled changes.

Usage:
  python scripts/jobs/update_de_bridge_performance.py [--dry-run] [--limit N] [--db path]
"""

import argparse
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def load_config():
    """Load configuration from constants or use defaults."""
    try:
        from logic.constants import DEFAULT_SETTINGS
        window_kys = DEFAULT_SETTINGS.get("DE_WINDOW_KYS", 30)
        enable_threshold = DEFAULT_SETTINGS.get("DE_DYN_ENABLE_RAW", 28)
        disable_threshold = DEFAULT_SETTINGS.get("DE_DYN_DISABLE_RAW", 26)
    except ImportError:
        # Fallback defaults
        window_kys = 30
        enable_threshold = 28
        disable_threshold = 26
    
    return {
        "window_kys": window_kys,
        "enable_threshold": enable_threshold,
        "disable_threshold": disable_threshold
    }


def get_db_connection(db_path):
    """Get database connection."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_de_bridges(conn, limit=None):
    """
    Get all DE_* bridges from ManagedBridges table.
    
    TODO: Adapt table name if your schema uses different naming.
    """
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ManagedBridges'")
    if not cursor.fetchone():
        print("⚠ WARNING: ManagedBridges table not found. Using fallback.")
        return []
    
    # Get DE bridges
    query = "SELECT * FROM ManagedBridges WHERE type LIKE 'DE_%'"
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    return [dict(row) for row in cursor.fetchall()]


def get_bridge_history(conn, bridge, window_kys):
    """
    Get bridge win/loss history for the last N periods.
    
    TODO: Adapt to your actual history table structure.
    Expected columns: ky (period), result (1=win, 0=loss)
    
    Returns:
        list of dicts with 'ky' and 'result' keys
    """
    cursor = conn.cursor()
    
    # TODO: Replace with actual history table query
    # For now, use a safe fallback that checks for common table names
    possible_tables = ['bridge_history', 'bridge_results', 'DuLieu_AI', 'results_A_I']
    
    for table_name in possible_tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if cursor.fetchone():
            print(f"  [INFO] Using table: {table_name}")
            # TODO: Implement actual query based on your schema
            # This is a placeholder - adapt to your schema
            break
    else:
        print(f"  [WARNING] No history table found for bridge {bridge.get('name', '?')}")
        return []
    
    # Placeholder - return empty for now
    # TODO: Implement actual history query
    return []


def compute_metrics(bridge, history, config):
    """
    Compute performance metrics for a bridge.
    
    Args:
        bridge: Bridge dict from DB
        history: List of win/loss records
        config: Configuration dict with thresholds
    
    Returns:
        dict with computed metrics
    """
    window_kys = config["window_kys"]
    
    # Compute wins in window
    wins_count = sum(1 for record in history[-window_kys:] if record.get("result") == 1)
    total_count = min(len(history), window_kys)
    
    # Win rate
    win_rate = (wins_count / total_count * 100) if total_count > 0 else 0.0
    
    # Current streak (consecutive wins from most recent)
    current_streak = 0
    for record in reversed(history):
        if record.get("result") == 1:
            current_streak += 1
        else:
            break
    
    # Simple score (can be enhanced)
    score = win_rate / 100.0 * 10.0  # Scale 0-10
    
    return {
        "de_win_count_last30": wins_count,
        "de_win_rate_last30": round(win_rate, 2),
        "de_current_streak": current_streak,
        "de_score": round(score, 2)
    }


def determine_auto_enabled(bridge, metrics, config):
    """
    Determine de_auto_enabled flag using hysteresis.
    
    Args:
        bridge: Bridge dict with current state
        metrics: Computed metrics dict
        config: Configuration dict with thresholds
    
    Returns:
        (new_auto_enabled: int, reason: str)
    """
    enable_threshold = config["enable_threshold"]
    disable_threshold = config["disable_threshold"]
    
    wins_count = metrics["de_win_count_last30"]
    current_auto_enabled = bridge.get("de_auto_enabled", 0)
    
    # Apply hysteresis
    if wins_count >= enable_threshold:
        return 1, f"wins={wins_count} >= enable_threshold={enable_threshold}"
    elif wins_count <= disable_threshold:
        return 0, f"wins={wins_count} <= disable_threshold={disable_threshold}"
    else:
        # In hysteresis zone - maintain current state
        return current_auto_enabled, f"wins={wins_count} in hysteresis zone, maintaining state={current_auto_enabled}"


def update_bridge_metrics(conn, bridge_id, metrics, new_auto_enabled, dry_run=False):
    """Update bridge metrics in database."""
    if dry_run:
        print(f"    [DRY-RUN] Would update bridge {bridge_id} with metrics: {metrics}")
        print(f"    [DRY-RUN] Would set de_auto_enabled={new_auto_enabled}")
        return
    
    cursor = conn.cursor()
    
    # Update metrics
    cursor.execute("""
        UPDATE ManagedBridges
        SET de_win_count_last30 = ?,
            de_win_rate_last30 = ?,
            de_current_streak = ?,
            de_score = ?,
            de_auto_enabled = ?,
            de_last_evaluated = ?
        WHERE id = ?
    """, (
        metrics["de_win_count_last30"],
        metrics["de_win_rate_last30"],
        metrics["de_current_streak"],
        metrics["de_score"],
        new_auto_enabled,
        datetime.now().isoformat(),
        bridge_id
    ))
    
    print(f"    ✓ Updated bridge {bridge_id}")


def create_audit_entry(conn, bridge_id, old_value, new_value, reason, dry_run=False):
    """Create audit entry when de_auto_enabled changes."""
    if old_value == new_value:
        return  # No change
    
    if dry_run:
        print(f"    [DRY-RUN] Would create audit entry: {old_value} -> {new_value}")
        return
    
    cursor = conn.cursor()
    
    # Check if bridge_audit table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bridge_audit'")
    if not cursor.fetchone():
        print("    ⚠ bridge_audit table not found, skipping audit entry")
        return
    
    action = "auto_enable" if new_value == 1 else "auto_disable"
    
    cursor.execute("""
        INSERT INTO bridge_audit (bridge_id, action, old_value, new_value, reason, actor, created_at)
        VALUES (?, ?, ?, ?, ?, 'system', datetime('now'))
    """, (bridge_id, action, str(old_value), str(new_value), reason))
    
    print(f"    ✓ Created audit entry: {action}")


def process_bridge(conn, bridge, config, dry_run=False):
    """Process a single bridge: compute metrics and update DB."""
    bridge_id = bridge.get("id")
    bridge_name = bridge.get("name", "N/A")
    bridge_type = (bridge.get("type", "") or "").upper()
    
    print(f"\n  Processing: {bridge_name} (ID={bridge_id}, Type={bridge_type})")
    
    # Skip non-DE_DYN for now (they don't use auto_enabled logic)
    if bridge_type != "DE_DYN":
        print(f"    ⊙ Skipping non-DE_DYN bridge")
        return
    
    # Get history
    history = get_bridge_history(conn, bridge, config["window_kys"])
    
    if not history:
        print(f"    ⚠ No history data available, using legacy current_streak if available")
        # Fallback: use existing current_streak if available
        current_streak = bridge.get("current_streak", 0)
        if current_streak:
            # Estimate wins from streak (very rough approximation)
            metrics = {
                "de_win_count_last30": current_streak,
                "de_win_rate_last30": round(current_streak / 30 * 100, 2),
                "de_current_streak": current_streak,
                "de_score": round(current_streak / 30 * 10, 2)
            }
        else:
            print(f"    ⚠ No legacy data either, skipping")
            return
    else:
        # Compute metrics from history
        metrics = compute_metrics(bridge, history, config)
    
    # Determine auto_enabled with hysteresis
    old_auto_enabled = bridge.get("de_auto_enabled", 0)
    new_auto_enabled, reason = determine_auto_enabled(bridge, metrics, config)
    
    print(f"    Metrics: wins={metrics['de_win_count_last30']}, rate={metrics['de_win_rate_last30']}%, streak={metrics['de_current_streak']}, score={metrics['de_score']}")
    print(f"    Auto-enabled: {old_auto_enabled} -> {new_auto_enabled} ({reason})")
    
    # Update database
    update_bridge_metrics(conn, bridge_id, metrics, new_auto_enabled, dry_run)
    
    # Create audit entry if changed
    if old_auto_enabled != new_auto_enabled:
        create_audit_entry(conn, bridge_id, old_auto_enabled, new_auto_enabled, reason, dry_run)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update DE bridge performance metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run (safe, no DB writes)
  python scripts/jobs/update_de_bridge_performance.py --dry-run
  
  # Process first 10 bridges (dry-run)
  python scripts/jobs/update_de_bridge_performance.py --dry-run --limit 10
  
  # Actually update database (backup first!)
  python scripts/jobs/update_de_bridge_performance.py
  
  # Custom database path
  python scripts/jobs/update_de_bridge_performance.py --db path/to/db.sqlite
        """
    )
    
    parser.add_argument(
        '--db',
        default='data/xo_so_prizes_all_logic.db',
        help='Path to SQLite database (default: data/xo_so_prizes_all_logic.db)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry-run mode: compute metrics but do not write to DB'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of bridges to process (for testing)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("DE BRIDGE PERFORMANCE UPDATE JOB")
    print("=" * 70)
    
    if args.dry_run:
        print("🔍 MODE: DRY-RUN (no database writes)\n")
    else:
        print("⚠️  MODE: LIVE (will update database)\n")
        print("💡 TIP: Use --dry-run first to preview changes\n")
    
    # Load config
    config = load_config()
    print(f"Configuration:")
    print(f"  - Window: {config['window_kys']} periods")
    print(f"  - Enable threshold: {config['enable_threshold']}")
    print(f"  - Disable threshold: {config['disable_threshold']}")
    
    # Connect to database
    try:
        conn = get_db_connection(args.db)
        print(f"✓ Connected to: {args.db}\n")
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to database: {e}")
        return 1
    
    try:
        # Get DE bridges
        bridges = get_de_bridges(conn, args.limit)
        print(f"Found {len(bridges)} DE_* bridges to process")
        
        if args.limit:
            print(f"(Limited to {args.limit} bridges for testing)")
        
        # Process each bridge
        processed = 0
        for bridge in bridges:
            try:
                process_bridge(conn, bridge, config, args.dry_run)
                processed += 1
            except Exception as e:
                print(f"  ❌ ERROR processing bridge {bridge.get('id')}: {e}")
        
        # Commit if not dry-run
        if not args.dry_run:
            conn.commit()
            print(f"\n✓ Committed changes to database")
        
        print(f"\n{'=' * 70}")
        print(f"SUMMARY: Processed {processed}/{len(bridges)} bridges")
        if args.dry_run:
            print("No database changes (dry-run mode)")
        else:
            print("Database updated successfully")
        print(f"{'=' * 70}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: Job failed: {e}")
        conn.rollback()
        return 1
        
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
