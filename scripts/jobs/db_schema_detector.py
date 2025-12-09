"""
Database Schema Auto-Detection Utilities

Automatically detects table and column names in SQLite databases
to handle different naming conventions (ManagedBridges vs managed_bridges, etc.)
"""

import sqlite3
import re


def detect_bridge_table(conn):
    """
    Auto-detect the bridge management table name.
    
    Tries common variants:
    - ManagedBridges
    - managed_bridges
    - bridge_management
    - bridges
    
    Returns:
        str or None: Table name if found, None otherwise
    """
    cursor = conn.cursor()
    
    # Possible table names (ordered by likelihood)
    possible_names = [
        'ManagedBridges',
        'managed_bridges',
        'bridge_management',
        'bridges',
        'Bridge',
        'BRIDGES'
    ]
    
    for table_name in possible_names:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=? COLLATE NOCASE",
            (table_name,)
        )
        if cursor.fetchone():
            return table_name
    
    return None


def detect_history_table(conn):
    """
    Auto-detect the bridge history/results table name.
    
    Tries common variants:
    - bridge_history
    - bridge_results  
    - DuLieu_AI
    - results_A_I
    - history
    
    Returns:
        str or None: Table name if found, None otherwise
    """
    cursor = conn.cursor()
    
    possible_names = [
        'bridge_history',
        'bridge_results',
        'DuLieu_AI',
        'results_A_I',
        'history',
        'results'
    ]
    
    for table_name in possible_names:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=? COLLATE NOCASE",
            (table_name,)
        )
        if cursor.fetchone():
            return table_name
    
    return None


def detect_audit_table(conn):
    """
    Auto-detect the audit table name.
    
    Returns:
        str or None: Table name if found, None otherwise
    """
    cursor = conn.cursor()
    
    possible_names = [
        'bridge_audit',
        'audit',
        'audit_log',
        'bridge_audit_log'
    ]
    
    for table_name in possible_names:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=? COLLATE NOCASE",
            (table_name,)
        )
        if cursor.fetchone():
            return table_name
    
    return None


def is_dynamic_bridge_type(bridge_type):
    """
    Check if a bridge type is a dynamic variant.
    
    Matches patterns like:
    - DE_DYN
    - DE_DYNAMIC
    - DE_DYNAMIC_K
    - DE_DYNAMIC-*
    - etc.
    
    Args:
        bridge_type: String bridge type (case-insensitive)
    
    Returns:
        bool: True if dynamic type, False otherwise
    """
    if not bridge_type:
        return False
    
    bridge_type_upper = bridge_type.upper()
    
    # Match DE_DYN* or DE_DYNAMIC*
    return (
        bridge_type_upper.startswith('DE_DYN') or
        bridge_type_upper.startswith('DE_DYNAMIC')
    )


def get_table_schema(conn, table_name):
    """
    Get schema information for a table.
    
    Returns:
        list: List of column info dicts with 'name', 'type', etc.
    """
    if not table_name:
        return []
    
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    
    columns = []
    for row in cursor.fetchall():
        columns.append({
            'cid': row[0],
            'name': row[1],
            'type': row[2],
            'notnull': row[3],
            'dflt_value': row[4],
            'pk': row[5]
        })
    
    return columns


def detect_schema_info(conn):
    """
    Detect all relevant schema information from the database.
    
    Returns:
        dict: Schema information including table names and columns
    """
    schema_info = {
        'bridge_table': None,
        'history_table': None,
        'audit_table': None,
        'warnings': [],
        'bridge_columns': [],
        'has_de_metrics': False
    }
    
    # Detect tables
    schema_info['bridge_table'] = detect_bridge_table(conn)
    schema_info['history_table'] = detect_history_table(conn)
    schema_info['audit_table'] = detect_audit_table(conn)
    
    # Add warnings for missing tables
    if not schema_info['bridge_table']:
        schema_info['warnings'].append("⚠ Bridge management table not found (tried: ManagedBridges, managed_bridges, etc.)")
    
    if not schema_info['history_table']:
        schema_info['warnings'].append("⚠ Bridge history table not found (tried: bridge_history, DuLieu_AI, etc.)")
    
    if not schema_info['audit_table']:
        schema_info['warnings'].append("⚠ Audit table not found (tried: bridge_audit, audit, etc.)")
    
    # Get column info for bridge table
    if schema_info['bridge_table']:
        schema_info['bridge_columns'] = get_table_schema(conn, schema_info['bridge_table'])
        
        # Check for DE metrics columns
        column_names = [col['name'] for col in schema_info['bridge_columns']]
        de_metric_columns = [
            'de_win_count_last30',
            'de_win_rate_last30',
            'de_current_streak',
            'de_score',
            'de_auto_enabled'
        ]
        
        has_all = all(col in column_names for col in de_metric_columns)
        schema_info['has_de_metrics'] = has_all
        
        if not has_all:
            missing = [col for col in de_metric_columns if col not in column_names]
            schema_info['warnings'].append(f"⚠ Missing DE metric columns: {', '.join(missing)}")
    
    return schema_info


__all__ = [
    'detect_bridge_table',
    'detect_history_table',
    'detect_audit_table',
    'is_dynamic_bridge_type',
    'get_table_schema',
    'detect_schema_info'
]
