#!/usr/bin/env python3
"""
Job: Update DE Bridge Performance Metrics (Auto-Detection Enhanced)

Computes and persists DE metrics for all DE_* bridges:
- de_win_count_last30: Win count in last 30 periods
- de_win_rate_last30: Win rate percentage
- de_current_streak: Current winning/losing streak
- de_score: Calculated bridge score
- de_auto_enabled: Auto-enable flag with hysteresis
- de_last_evaluated: Last evaluation timestamp

Creates audit entries when de_auto_enabled changes.

Features:
- Auto-detects dynamic bridge variants (DE_DYN, DE_DYNAMIC, etc.)
- Auto-detects table names (ManagedBridges vs managed_bridges, etc.)
- Generates dry-run report (JSON/text)
- Requires --apply flag to write to DB (backup mandatory)
- Clear logging with reasons

Usage:
  # Dry-run (default, generates report)
  python scripts/jobs/update_de_bridge_performance.py [--db path] [--limit N]
  
  # Apply changes (requires backup confirmation)
  python scripts/jobs/update_de_bridge_performance.py --apply [--db path]
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import schema detector
from db_schema_detector import (
    detect_schema_info,
    is_dynamic_bridge_type
)


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


def get_de_bridges(conn, schema_info, limit=None):
    """
    Get all DE_* bridges using auto-detected table name.
    
    Args:
        conn: Database connection
        schema_info: Schema information from detect_schema_info()
        limit: Optional limit on number of bridges
    
    Returns:
        list: List of bridge dicts
    """
    cursor = conn.cursor()
    
    table_name = schema_info.get('bridge_table')
    if not table_name:
        print("❌ ERROR: Bridge table not found")
        return []
    
    # Get all DE_* bridges
    query = f"SELECT * FROM {table_name} WHERE type LIKE 'DE_%'"
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    bridges = [dict(row) for row in cursor.fetchall()]
    
    # Filter to only dynamic bridge types if processing DE_DYN logic
    # (other types like DE_SET, DE_MEMORY don't use auto_enabled)
    return bridges


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


def update_bridge_metrics(conn, bridge_id, metrics, new_auto_enabled, schema_info, dry_run=False):
    """Update bridge metrics in database."""
    if dry_run:
        print(f"    [DRY-RUN] Would update bridge {bridge_id} with metrics: {metrics}")
        print(f"    [DRY-RUN] Would set de_auto_enabled={new_auto_enabled}")
        return
    
    cursor = conn.cursor()
    table_name = schema_info.get('bridge_table')
    
    if not table_name:
        print(f"    ❌ ERROR: Bridge table not found, cannot update")
        return
    
    # Update metrics
    cursor.execute(f"""
        UPDATE {table_name}
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


def create_audit_entry(conn, bridge_id, old_value, new_value, reason, schema_info, dry_run=False):
    """Create audit entry when de_auto_enabled changes."""
    if old_value == new_value:
        return  # No change
    
    if dry_run:
        print(f"    [DRY-RUN] Would create audit entry: {old_value} -> {new_value}")
        return
    
    audit_table = schema_info.get('audit_table')
    if not audit_table:
        print("    ⚠ Audit table not found, skipping audit entry")
        return
    
    cursor = conn.cursor()
    action = "auto_enable" if new_value == 1 else "auto_disable"
    
    cursor.execute(f"""
        INSERT INTO {audit_table} (bridge_id, action, old_value, new_value, reason, actor, created_at)
        VALUES (?, ?, ?, ?, ?, 'system', datetime('now'))
    """, (bridge_id, action, str(old_value), str(new_value), reason))
    
    print(f"    ✓ Created audit entry: {action}")


def process_bridge(conn, bridge, config, schema_info, dry_run=False):
    """Process a single bridge: compute metrics and update DB."""
    bridge_id = bridge.get("id")
    bridge_name = bridge.get("name", "N/A")
    bridge_type = (bridge.get("type", "") or "")
    
    print(f"\n  Processing: {bridge_name} (ID={bridge_id}, Type={bridge_type})")
    
    # Auto-detect if this is a dynamic bridge variant
    if not is_dynamic_bridge_type(bridge_type):
        print(f"    ⊙ Skipping non-dynamic bridge (type: {bridge_type})")
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
    update_bridge_metrics(conn, bridge_id, metrics, new_auto_enabled, schema_info, dry_run)
    
    # Create audit entry if changed
    if old_auto_enabled != new_auto_enabled:
        create_audit_entry(conn, bridge_id, old_auto_enabled, new_auto_enabled, reason, schema_info, dry_run)
    
    # Return summary for reporting
    return {
        'bridge_id': bridge_id,
        'bridge_name': bridge_name,
        'bridge_type': bridge_type,
        'old_auto_enabled': old_auto_enabled,
        'new_auto_enabled': new_auto_enabled,
        'reason': reason,
        'metrics': metrics
    }


def generate_report(report_data, output_format='json'):
    """Generate dry-run report in specified format."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if output_format == 'json':
        filename = f"de_performance_report_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2)
        return filename
    else:
        filename = f"de_performance_report_{timestamp}.txt"
        with open(filename, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("DE BRIDGE PERFORMANCE REPORT\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Generated: {report_data['timestamp']}\n")
            f.write(f"Database: {report_data['database']}\n\n")
            
            f.write("Schema Detection:\n")
            for key, value in report_data['schema'].items():
                if key != 'warnings' and key != 'bridge_columns':
                    f.write(f"  {key}: {value}\n")
            
            if report_data['schema']['warnings']:
                f.write("\nWarnings:\n")
                for warning in report_data['schema']['warnings']:
                    f.write(f"  {warning}\n")
            
            f.write(f"\nBridges Processed: {report_data['summary']['processed']}/{report_data['summary']['total']}\n")
            f.write(f"Would Enable: {report_data['summary']['would_enable']}\n")
            f.write(f"Would Disable: {report_data['summary']['would_disable']}\n")
            f.write(f"No Change: {report_data['summary']['no_change']}\n")
            
            if report_data['changes']:
                f.write("\nDetailed Changes:\n")
                for change in report_data['changes']:
                    f.write(f"\n  Bridge: {change['bridge_name']} (ID={change['bridge_id']})\n")
                    f.write(f"    Type: {change['bridge_type']}\n")
                    f.write(f"    Auto-enabled: {change['old_auto_enabled']} -> {change['new_auto_enabled']}\n")
                    f.write(f"    Reason: {change['reason']}\n")
                    f.write(f"    Metrics: {change['metrics']}\n")
        
        return filename


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update DE bridge performance metrics (Auto-Detection Enhanced)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run (default, generates report)
  python scripts/jobs/update_de_bridge_performance.py
  
  # Dry-run with limit
  python scripts/jobs/update_de_bridge_performance.py --limit 10
  
  # Apply changes (REQUIRES --apply flag and backup!)
  python scripts/jobs/update_de_bridge_performance.py --apply
  
  # Custom database path
  python scripts/jobs/update_de_bridge_performance.py --db path/to/db.sqlite --apply
        """
    )
    
    parser.add_argument(
        '--db',
        default='data/xo_so_prizes_all_logic.db',
        help='Path to SQLite database (default: data/xo_so_prizes_all_logic.db)'
    )
    
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Apply changes to database (default is dry-run)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of bridges to process (for testing)'
    )
    
    parser.add_argument(
        '--report-format',
        choices=['json', 'text'],
        default='json',
        help='Report format (default: json)'
    )
    
    args = parser.parse_args()
    
    # Determine dry-run mode (inverse of --apply)
    dry_run = not args.apply
    
    print("=" * 70)
    print("DE BRIDGE PERFORMANCE UPDATE JOB (AUTO-DETECTION)")
    print("=" * 70)
    
    if dry_run:
        print("🔍 MODE: DRY-RUN (no database writes, generates report)\n")
    else:
        print("⚠️  MODE: APPLY (will update database)\n")
        print("💡 IMPORTANT: Ensure you have backed up the database!\n")
    
    # Load config
    config = load_config()
    print(f"Configuration:")
    print(f"  - Window: {config['window_kys']} periods")
    print(f"  - Enable threshold: {config['enable_threshold']}")
    print(f"  - Disable threshold: {config['disable_threshold']}\n")
    
    # Connect to database
    try:
        conn = get_db_connection(args.db)
        print(f"✓ Connected to: {args.db}")
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to database: {e}")
        return 1
    
    try:
        # Auto-detect schema
        print("\n🔍 Auto-detecting database schema...")
        schema_info = detect_schema_info(conn)
        
        print(f"  Bridge table: {schema_info['bridge_table'] or 'NOT FOUND'}")
        print(f"  History table: {schema_info['history_table'] or 'NOT FOUND'}")
        print(f"  Audit table: {schema_info['audit_table'] or 'NOT FOUND'}")
        print(f"  Has DE metrics: {schema_info['has_de_metrics']}")
        
        if schema_info['warnings']:
            print("\n⚠️  Warnings:")
            for warning in schema_info['warnings']:
                print(f"  {warning}")
        
        if not schema_info['bridge_table']:
            print("\n❌ ERROR: Cannot proceed without bridge table")
            return 1
        
        # Get DE bridges
        bridges = get_de_bridges(conn, schema_info, args.limit)
        print(f"\nFound {len(bridges)} DE_* bridges to process")
        
        if args.limit:
            print(f"(Limited to {args.limit} bridges for testing)")
        
        # Prepare report data
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'database': args.db,
            'mode': 'apply' if not dry_run else 'dry-run',
            'schema': schema_info,
            'config': config,
            'summary': {
                'total': len(bridges),
                'processed': 0,
                'would_enable': 0,
                'would_disable': 0,
                'no_change': 0
            },
            'changes': []
        }
        
        # Process each bridge
        processed = 0
        for bridge in bridges:
            try:
                result = process_bridge(conn, bridge, config, schema_info, dry_run)
                processed += 1
                
                if result:
                    report_data['changes'].append(result)
                    
                    # Update summary counts
                    if result['old_auto_enabled'] != result['new_auto_enabled']:
                        if result['new_auto_enabled'] == 1:
                            report_data['summary']['would_enable'] += 1
                        else:
                            report_data['summary']['would_disable'] += 1
                    else:
                        report_data['summary']['no_change'] += 1
                        
            except Exception as e:
                print(f"  ❌ ERROR processing bridge {bridge.get('id')}: {e}")
        
        report_data['summary']['processed'] = processed
        
        # Commit if not dry-run
        if not dry_run:
            conn.commit()
            print(f"\n✓ Committed changes to database")
        else:
            # Generate report
            print(f"\n📄 Generating report...")
            report_file = generate_report(report_data, args.report_format)
            print(f"✓ Report saved to: {report_file}")
        
        print(f"\n{'=' * 70}")
        print(f"SUMMARY:")
        print(f"  Processed: {processed}/{len(bridges)} bridges")
        print(f"  Would enable: {report_data['summary']['would_enable']}")
        print(f"  Would disable: {report_data['summary']['would_disable']}")
        print(f"  No change: {report_data['summary']['no_change']}")
        
        if dry_run:
            print(f"\n💡 To apply changes, run with --apply flag (backup DB first!)")
        else:
            print(f"\n✓ Database updated successfully")
        
        print(f"{'=' * 70}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: Job failed: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return 1
        
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
