
import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

print("--- Testing Imports for dashboard_scorer.py ---")

try:
    print("1. Importing logic.backtester...")
    from logic.backtester import BACKTEST_15_CAU_K2N_V30_AI_V8, BACKTEST_MANAGED_BRIDGES_K2N
    print("   SUCCESS")
except ImportError as e:
    print(f"   FAIL: {e}")

try:
    print("2. Importing logic.backtester_core...")
    from logic.backtester_core import parse_k2n_results as _parse_k2n_results
    print("   SUCCESS")
except ImportError as e:
    print(f"   FAIL: {e}")

try:
    print("3. Importing logic.bridges.bridges_classic...")
    from logic.bridges.bridges_classic import ALL_15_BRIDGE_FUNCTIONS_V5, checkHitSet_V30_K2N, getAllLoto_V30
    print("   SUCCESS")
except ImportError as e:
    print(f"   FAIL: {e}")

try:
    print("4. Importing logic.bridges.bridges_memory...")
    from logic.bridges.bridges_memory import calculate_bridge_stl, get_27_loto_names, get_27_loto_positions
    print("   SUCCESS")
except ImportError as e:
    print(f"   FAIL: {e}")

try:
    print("5. Importing logic.bridges.bridges_v16...")
    from logic.bridges.bridges_v16 import getAllPositions_V17_Shadow, taoSTL_V30_Bong
    print("   SUCCESS")
except ImportError as e:
    print(f"   FAIL: {e}")

try:
    print("6. Importing logic.data_repository...")
    from logic.data_repository import get_all_managed_bridges
    print("   SUCCESS")
except ImportError as e:
    print(f"   FAIL: {e}")

try:
    print("7. Importing logic.db_manager...")
    from logic.db_manager import DB_NAME
    print("   SUCCESS")
except ImportError as e:
    print(f"   FAIL: {e}")

try:
    print("8. Importing logic.backtester_scoring...")
    from logic.backtester_scoring import LoScorer
    print("   SUCCESS")
except ImportError as e:
    print(f"   FAIL: {e}")

print("\n--- Testing dashboard_scorer import itself ---")
try:
    from logic.analytics import dashboard_scorer
    print("   SUCCESS: logic.analytics.dashboard_scorer imported")
    print(f"   dashboard_scorer.getAllLoto_V30: {dashboard_scorer.getAllLoto_V30}")
except ImportError as e:
    print(f"   FAIL: {e}")
except Exception as e:
    print(f"   FAIL (Exception): {e}")
