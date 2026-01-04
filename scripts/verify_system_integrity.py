
import os
import sys
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock logic.config_manager to avoid UnicodeEncodeError
mock_config = MagicMock()
mock_config.SETTINGS = MagicMock()
sys.modules['logic.config_manager'] = mock_config
sys.modules['config_manager'] = mock_config

# Mock other potential trouble modules if they print on import
# (We only want to verify they exist and parse correctly)

def check_file_exists(path):
    full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', path))
    exists = os.path.exists(full_path)
    print(f"Checking {path}... {'[OK]' if exists else '[MISSING]'}")
    return exists

def check_imports():
    print("\nChecking Imports...")
    try:
        import logic.backtester_scoring
        print("  import logic.backtester_scoring [OK]")
        
        # Dashboard scorer imports DB manager and others, might fail if dependencies missing
        # We try to mock db_manager too
        mock_db = MagicMock()
        mock_db.DB_NAME = "mock.db"
        sys.modules['logic.db_manager'] = mock_db
        
        import logic.analytics.dashboard_scorer
        print("  import logic.analytics.dashboard_scorer [OK]")
        
        # UI module usually requires Tkinter, skipping if headless?
        # Just check file existence is usually enough for UI in this context, 
        # but let's try import to catch SyntaxErrors
        try:
            import ui.ui_dashboard
            print("  import ui.ui_dashboard [OK]")
        except ImportError as e:
            print(f"  [WARN] UI import skipped (likely headless): {e}")
            
        return True
    
    except ImportError as e:
        print(f"  [ERROR] Import failed: {e}")
        return False
    except Exception as e:
        print(f"  [ERROR] Unexpected error during import: {e}")
        return False

def verify_archive():
    print("\nChecking Archive...")
    archive_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'archive'))
    if not os.path.exists(archive_path):
        print("  [ERROR] Archive directory missing!")
        return False
    
    files = os.listdir(archive_path)
    print(f"  Archive contains {len(files)} files.")
    return len(files) > 0

def main():
    print("=== SYSTEM INTEGRITY CHECK (MOCKED) ===\n")
    
    # 1. Critical Files
    files_ok = True
    files_ok &= check_file_exists("main_app.py")
    files_ok &= check_file_exists("ui/ui_dashboard.py")
    files_ok &= check_file_exists("logic/backtester_scoring.py")
    files_ok &= check_file_exists("logic/analytics/dashboard_scorer.py")
    
    # 2. Imports
    imports_ok = check_imports()
    
    # 3. Archive
    archive_ok = verify_archive()
    
    print("\n==============================")
    if files_ok and imports_ok and archive_ok:
        print("SUCCESS: System integrity verified.")
        sys.exit(0)
    else:
        print("FAILURE: System integrity check failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
