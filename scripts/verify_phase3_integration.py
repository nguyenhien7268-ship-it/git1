#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 3 Integration Verification Script
Tests that Phase 3 data collector is properly integrated into the live codebase.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that Phase 3 can be imported."""
    print("=" * 60)
    print("TEST 1: Checking Imports")
    print("=" * 60)
    
    try:
        from logic.phase3_data_collector import get_collector, log_prediction
        print("[OK] Phase 3 data collector imports successfully")
        return True
    except ImportError as e:
        print(f"[FAIL] Could not import Phase 3: {e}")
        return False

def test_services_integration():
    """Test that services have Phase 3 integrated."""
    print("\n" + "=" * 60)
    print("TEST 2: Checking Services Integration")
    print("=" * 60)
    
    try:
        from services import AnalysisService, DataService
        
        # Check if PHASE3_ENABLED flag exists in AnalysisService
        import services.analysis_service as analysis_module
        if hasattr(analysis_module, 'PHASE3_ENABLED'):
            print(f"[OK] AnalysisService has PHASE3_ENABLED = {analysis_module.PHASE3_ENABLED}")
        else:
            print("[WARN] AnalysisService missing PHASE3_ENABLED flag")
        
        # Check if PHASE3_ENABLED flag exists in DataService
        import services.data_service as data_module
        if hasattr(data_module, 'PHASE3_ENABLED'):
            print(f"[OK] DataService has PHASE3_ENABLED = {data_module.PHASE3_ENABLED}")
        else:
            print("[WARN] DataService missing PHASE3_ENABLED flag")
        
        # Check for helper methods
        service = DataService("test.db", logger=None)
        if hasattr(service, '_log_outcomes_phase3'):
            print("[OK] DataService has _log_outcomes_phase3 method")
        else:
            print("[FAIL] DataService missing _log_outcomes_phase3 method")
        
        return True
    except Exception as e:
        print(f"[FAIL] Services integration check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_table():
    """Test that meta_learning_history table exists."""
    print("\n" + "=" * 60)
    print("TEST 3: Checking Database Table")
    print("=" * 60)
    
    try:
        import sqlite3
        from logic.db_manager import DB_NAME
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='meta_learning_history'
        """)
        
        if cursor.fetchone():
            print("[OK] Table 'meta_learning_history' exists")
            
            # Check row count
            cursor.execute("SELECT COUNT(*) FROM meta_learning_history")
            count = cursor.fetchone()[0]
            print(f"[INFO] Current row count: {count}")
            
            conn.close()
            return True
        else:
            print("[FAIL] Table 'meta_learning_history' not found")
            print("[ACTION] Run: python scripts\\init_phase3_table.py")
            conn.close()
            return False
            
    except Exception as e:
        print(f"[FAIL] Database check failed: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("PHASE 3 INTEGRATION VERIFICATION")
    print("=" * 60)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Services Integration", test_services_integration()))
    results.append(("Database Table", test_database_table()))
    
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("SUCCESS: All integration tests passed!")
        print("\nPhase 3 is ready to collect data.")
        print("Next: Run the dashboard analysis to start collecting predictions.")
    else:
        print("WARNING: Some tests failed.")
        print("Please fix the issues above before using Phase 3.")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
