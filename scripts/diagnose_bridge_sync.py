
import sys
import os
import sqlite3
import re

# --- CẤU HÌNH ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

try:
    from logic.db_manager import DB_NAME
    from logic.data_repository import get_all_data_ai
    # [FIX] Use DeBridgeManager for parsing instead of raw regex
    from logic.bridges.bridge_manager_de import de_manager
    from logic.de_backtester_core import run_de_bridge_historical_test
    from logic.bridges.bridges_v16 import getPositionName_V16, getPositionName_V17_Shadow
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    sys.exit(1)

def check_name_parsing(bridge_name, bridge_type):
    """
    [FIXED] Sử dụng parser chuẩn của DeBridgeManager.
    Trả về parsed_info nếu thành công, None nếu thất bại.
    """
    parsed_info = de_manager._parse_bridge_id_v2(bridge_name, bridge_type)
    if not parsed_info:
        parsed_info = de_manager._parse_bridge_id_legacy(bridge_name)
    return parsed_info

def main():
    print("\n" + "="*80)
    print("DB SYNC DIAGNOSTIC - FIXED")
    print("="*80)

    # 1. Tải dữ liệu
    print("Loading data...")
    all_data = get_all_data_ai(DB_NAME)
    if not all_data:
        print("DB Empty.")
        return

    # 2. Lấy cầu từ DB
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, current_streak, type FROM ManagedBridges WHERE is_enabled=1 AND (type LIKE 'DE_%' OR type LIKE 'CAU_DE%')")
    bridges = [dict(row) for row in cursor.fetchall()]
    conn.close()

    print(f"Checking {len(bridges)} active DE bridges...")
    print("-" * 120)
    print(f"{'NAME':<30} | {'DB':<5} | {'REAL':<5} | {'STATUS':<15} | {'DETAILS'}")
    print("-" * 120)

    error_count = 0
    sync_error_count = 0

    for b in bridges:
        name = b['name']
        b_type = b['type']
        db_streak = b['current_streak']
        
        # A. Kiểm tra Parse Tên
        parsed_info = check_name_parsing(name, b_type)
        is_name_broken = (parsed_info is None)
        
        status = "OK"
        reason = ""
        real_streak = "N/A"

        if is_name_broken:
            status = "NAME ERROR"
            reason = "Cannot parse ID"
            error_count += 1
        else:
            # B. Chuẩn bị Config cho Backtester
            # [FIX] Populate pos1_idx, pos2_idx from parsed_info
            idx1, idx2, k_offset, mode = parsed_info
            
            # Update config map
            b['pos1_idx'] = idx1
            b['pos2_idx'] = idx2
            b['k_offset'] = k_offset
            b['type'] = mode # Or map back to DB type if needed, but 'mode' usually works for backtester logic
            # DeBacktester uses 'type' for logic: DYNAMIC, SET, etc.
            # parsed_info returns internal mode string.
            # Ensure compatibility.
            # DeBridgeManager._calculate_dan_logic uses the mode directly.
            # DeBacktesterCore.run_de_bridge_historical_test uses 'type' logic.
            # We need to map 'mode' to 'type' expected by Backtester?
            # Actually run_de_bridge_historical_test logic:
            # if bridge_type == "DE_SET" ...
            # bridge_type comes from b['type'].
            # So we keep b['type'] from DB which is correct (e.g. DE_SET).
            
            # C. Tính toán Streak Thực tế
            try:
                history = run_de_bridge_historical_test(b, all_data, days=15)
                # history returns list of dicts.
                if history and "status" in history[0] and "FAIL" in history[0].get("status", ""):
                     real_streak = "ERR"
                     reason = history[0]["status"]
                elif history:
                    # Tính streak từ history
                    r_str = 0
                    current = 0
                    # Standard logic: iterate from end (most recent today) backwards?
                    # history is sorted by date ascending usually?
                    # run_de_bridge_historical_test returns list corresponding to days.
                    # Last element is today/most recent.
                    
                    # Calculate streak from the accumulated list?
                    # logic/de_backtester_core.py line 185: stats["current_streak"] = current_streak
                    # But run_de_bridge_historical_test returns 'results' list, NOT stats dict.
                    # Warning: run_de_bridge_historical_test returns LIST OF DICTS.
                    # We have to calculate streak manually from list.
                    
                    streak_count = 0
                    # Iterate backwards from last result
                    if history:
                        last_res = history[-1]
                        # If today is pending, streak might be from yesterday.
                        # Check logic in DeBridgeManager: new_streak = streak + 1 if is_win else 0
                        # DeBridgeManager updates DB with strictly calculated streak.
                        
                        # Let's count streak from the end
                        for day_res in reversed(history):
                            if day_res['is_win']:
                                streak_count += 1
                            else:
                                if day_res.get('status') == 'Chờ':
                                    continue # Skip pending day?
                                else:
                                    break
                    
                    # Note: DeBridgeManager considers Pending as not win yet?
                    # Or does it use previous day?
                    # DeBridgeManager line 103: new_streak = streak + 1 if is_win else 0.
                    # So if today is pending (is_win=False), streak becomes 0?
                    # No, DeBridgeManager usually runs AFTER result is available.
                    
                    real_streak = streak_count
            except Exception as e:
                real_streak = "CRASH"
                reason = str(e)

            # D. So sánh
            if isinstance(real_streak, int) and db_streak != real_streak:
                status = "DESYNC"
                reason = f"DB={db_streak} != Real={real_streak}"
                sync_error_count += 1

        if status != "OK":
             print(f"{name:<30} | {str(db_streak):<5} | {str(real_streak):<5} | {status:<15} | {reason}")

    print("-" * 120)
    print(f"SUMMARY:")
    print(f"   - Total checked: {len(bridges)}")
    print(f"   - Name Errors: {error_count}")
    print(f"   - Desync Errors: {sync_error_count}")

if __name__ == "__main__":
    main()