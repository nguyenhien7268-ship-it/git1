import sys
import os
import traceback

# Add project root to path
sys.path.insert(0, os.path.abspath("."))

print("Testing Imports...")

try:
    import lottery_service
    print("[OK] lottery_service imported successfully")
except Exception:
    print("[FAIL] Failed to import lottery_service:")
    traceback.print_exc()
    sys.exit(1)

try:
    import app_controller
    print("[OK] app_controller imported successfully")
except Exception:
    print("[FAIL] Failed to import app_controller:")
    traceback.print_exc()
    sys.exit(1)

try:
    import ui.styles
    print("[OK] ui.styles imported successfully")
except Exception:
    print("[FAIL] Failed to import ui.styles:")
    traceback.print_exc()
    sys.exit(1)

try:
    import ui.ui_main_window
    print("[OK] ui.ui_main_window imported successfully")
except SystemExit:
    print("[FAIL] ui.ui_main_window exited (caught ImportError internally)")
except Exception:
    print("[FAIL] Failed to import ui.ui_main_window:")
    traceback.print_exc()

try:
    import ui.ui_dashboard
    print("[OK] ui.ui_dashboard imported successfully")
except SystemExit:
     print("[FAIL] ui.ui_dashboard exited (caught ImportError internally)")
except Exception:
    print("[FAIL] Failed to import ui.ui_dashboard:")
    traceback.print_exc()
