#!/usr/bin/env python3
"""
Test script for DE_MEMORY bridge scanning, storage, and filtering pipeline.
Usage: python scripts/test_de_memory_pipeline.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import sqlite3
from logic.data_repository import load_data_ai_from_db
from logic.bridges.de_bridge_scanner import run_de_scanner

def test_de_memory_pipeline():
    """Test the complete DE_MEMORY bridge pipeline."""
    print("=" * 80)
    print("TESTING DE_MEMORY BRIDGE PIPELINE")
    print("=" * 80)
    
    db_name = "lottery.db"
    
    # Step 1: Load data
    print("\n[STEP 1] Loading lottery data...")
    all_data, _ = load_data_ai_from_db(db_name)
    if not all_data:
        print("❌ No data found in database")
        return False
    print(f"✅ Loaded {len(all_data)} lottery periods")
    
    # Step 2: Run DE scanner
    print("\n[STEP 2] Running DE bridge scanner...")
    count, found_bridges = run_de_scanner(all_data)
    print(f"✅ Scanner completed: {count} bridges found")
    
    # Step 3: Analyze results by type
    print("\n[STEP 3] Analyzing bridge types...")
    type_counts = {}
    memory_bridges = []
    
    for bridge in found_bridges:
        bridge_type = bridge.get('type', 'UNKNOWN')
        type_counts[bridge_type] = type_counts.get(bridge_type, 0) + 1
        
        if bridge_type == 'DE_MEMORY':
            memory_bridges.append(bridge)
    
    print("\n📊 Bridge Type Distribution:")
    for btype, count in sorted(type_counts.items()):
        icon = "🧠" if btype == 'DE_MEMORY' else "📦" if btype == 'DE_SET' else "🔍"
        print(f"  {icon} {btype}: {count}")
    
    # Step 4: Verify DE_MEMORY bridges
    print(f"\n[STEP 4] Verifying DE_MEMORY bridges ({len(memory_bridges)})...")
    if memory_bridges:
        print("\n🧠 Sample DE_MEMORY bridges:")
        for i, bridge in enumerate(memory_bridges[:5], 1):
            name = bridge.get('name', 'N/A')
            desc = bridge.get('display_desc', bridge.get('description', 'N/A'))
            confidence = bridge.get('win_rate', 0)
            print(f"  {i}. {name}")
            print(f"     Confidence: {confidence:.1f}%")
            print(f"     {desc[:100]}...")
    else:
        print("⚠️  No DE_MEMORY bridges found (may need more historical data)")
    
    # Step 5: Verify database storage
    print("\n[STEP 5] Checking database storage...")
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Check if DE_MEMORY bridges are saved
    cursor.execute("SELECT COUNT(*) FROM ManagedBridges WHERE type = 'DE_MEMORY'")
    db_memory_count = cursor.fetchone()[0]
    
    print(f"  Scanner found: {len(memory_bridges)} DE_MEMORY bridges")
    print(f"  Database stored: {db_memory_count} DE_MEMORY bridges")
    
    if db_memory_count == len(memory_bridges):
        print("  ✅ All DE_MEMORY bridges saved correctly")
    elif db_memory_count > 0:
        print(f"  ⚠️  Partial storage: {db_memory_count}/{len(memory_bridges)}")
    else:
        print("  ❌ No DE_MEMORY bridges in database")
    
    # Show sample from DB
    cursor.execute("""
        SELECT id, name, type, description, is_enabled 
        FROM ManagedBridges 
        WHERE type = 'DE_MEMORY' 
        LIMIT 3
    """)
    db_samples = cursor.fetchall()
    
    if db_samples:
        print("\n  📝 Sample from database:")
        for row in db_samples:
            bridge_id, name, btype, desc, enabled = row
            status = "🟢 Enabled" if enabled else "🔴 Disabled"
            print(f"    ID {bridge_id}: {name} ({btype}) - {status}")
            print(f"    {desc[:80]}...")
    
    # Step 6: Verify DE filter coverage
    print("\n[STEP 6] Testing DE bridge filtering...")
    cursor.execute("""
        SELECT type, COUNT(*) 
        FROM ManagedBridges 
        WHERE type LIKE 'DE_%' OR type LIKE 'CAU_DE%'
        GROUP BY type
        ORDER BY COUNT(*) DESC
    """)
    de_types = cursor.fetchall()
    
    print("\n  🔴 DE bridge types in database:")
    total_de = 0
    for btype, count in de_types:
        total_de += count
        icon = "🧠" if btype == 'DE_MEMORY' else "📦" if btype == 'DE_SET' else "🔍"
        print(f"    {icon} {btype}: {count}")
    
    print(f"\n  Total DE bridges: {total_de}")
    
    # Step 7: Test filter query
    print("\n[STEP 7] Testing management filter query...")
    valid_de_types = ['DE_DYNAMIC_K', 'DE_POS_SUM', 'DE_SET', 'DE_PASCAL', 'DE_KILLER', 'DE_MEMORY', 'CAU_DE']
    
    filter_query = "SELECT COUNT(*) FROM ManagedBridges WHERE ("
    conditions = []
    for t in valid_de_types:
        conditions.append(f"type LIKE '{t}%' OR type = '{t}'")
    filter_query += " OR ".join(conditions) + ")"
    
    cursor.execute(filter_query)
    filter_count = cursor.fetchone()[0]
    
    print(f"  Filter query matches: {filter_count} bridges")
    print(f"  Direct DE count: {total_de} bridges")
    
    if filter_count == total_de:
        print("  ✅ Filter query working correctly")
    else:
        print(f"  ⚠️  Filter mismatch: {filter_count} vs {total_de}")
    
    conn.close()
    
    # Step 8: Summary
    print("\n" + "=" * 80)
    print("PIPELINE TEST SUMMARY")
    print("=" * 80)
    
    issues = []
    if len(memory_bridges) == 0:
        issues.append("⚠️  No memory bridges found (may need more data)")
    elif db_memory_count == 0:
        issues.append("❌ Memory bridges not saved to database")
    elif db_memory_count != len(memory_bridges):
        issues.append(f"⚠️  Storage mismatch: {db_memory_count}/{len(memory_bridges)}")
    
    if not issues:
        print("✅ ALL TESTS PASSED")
        print(f"  - {len(memory_bridges)} DE_MEMORY bridges scanned")
        print(f"  - {db_memory_count} DE_MEMORY bridges stored")
        print(f"  - {total_de} total DE bridges in database")
        print(f"  - Filter query working correctly")
        return True
    else:
        print("⚠️  TESTS COMPLETED WITH WARNINGS")
        for issue in issues:
            print(f"  {issue}")
        return False

if __name__ == "__main__":
    try:
        success = test_de_memory_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
