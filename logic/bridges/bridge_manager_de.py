import os
import sys
import sqlite3

# Import các tài nguyên chung
try:
    from logic.config_manager import SETTINGS
    from logic.db_manager import DB_NAME, upsert_managed_bridge
    # Lấy thuật toán V17 từ thư viện cầu
    from logic.bridges.bridges_v16 import (
        getAllPositions_V17_Shadow,
        getPositionName_V17_Shadow,
        taoSTL_V30_Bong,
    )
except ImportError as e:
    print(f"Lỗi Import trong bridge_manager_de: {e}")
    SETTINGS = None
    DB_NAME = "data/xo_so_prizes_all_logic.db"

# ===================================================================================
# HELPER FUNCTIONS (Dành riêng cho Đề)
# ===================================================================================
BONG_DUONG_MAP = {0: 5, 1: 6, 2: 7, 3: 8, 4: 9, 5: 0, 6: 1, 7: 2, 8: 3, 9: 4}

def get_4_touches(stl_pair):
    """Từ STL ['XY', 'YX'] suy ra 4 chạm (X, Y, Bóng X, Bóng Y)."""
    touches = set()
    for s in stl_pair:
        if s and s.isdigit():
            d1, d2 = int(s[0]), int(s[1])
            touches.update([d1, d2, BONG_DUONG_MAP.get(d1, d1), BONG_DUONG_MAP.get(d2, d2)])
    return touches

def check_hit_de_4_touches(stl_pair, gdb_str):
    """Kiểm tra xem GĐB có nằm trong 4 chạm của cầu không."""
    if not gdb_str or len(gdb_str) < 2: return False
    touches = get_4_touches(stl_pair)
    try:
        gdb_vals = {int(gdb_str[-2]), int(gdb_str[-1])}
        return not touches.isdisjoint(gdb_vals)
    except:
        return False

# ===================================================================================
# LOGIC DÒ CẦU & QUẢN LÝ (CORE DE)
# ===================================================================================
def TIM_CAU_DE_TOT_NHAT(
    toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME
):
    """
    Dò tìm Cầu Đề V17 (4 Chạm) tốt nhất.
    Backtest đồng thời K1N (ăn ngay) và K2N (nuôi 2 ngày).
    """
    print(">>> [DE SYSTEM] Bắt đầu Dò Cầu Đề V17 (4 Chạm)...")
    allData = toan_bo_A_I
    if not allData or len(allData) < 10:
        return []
    # Map vị trí V17 (Lấy mẫu từ dòng đầu)
    positions_shadow = getAllPositions_V17_Shadow(allData[0])
    num_positions = len(positions_shadow)
    if num_positions == 0: return []
    # Tạo danh sách thuật toán (Cặp vị trí)
    algorithms = []
    for i in range(num_positions):
        for j in range(i, num_positions):
            algorithms.append((i, j))
    num_algorithms = len(algorithms)
    print(f">>> [DE SYSTEM] Đã tạo {num_algorithms} cặp vị trí. Đang xử lý dữ liệu...")
    # Pre-process Data (Cache Positions & GDB)
    start_idx = 2
    end_idx = len(allData) - 1
    cache_history = []
    for k in range(len(allData)):
        row = allData[k]
        gdb = str(row[2]) if len(row) > 2 else "00"
        if not gdb or gdb == 'nan': gdb = "00"
        cache_history.append({
            "positions": getAllPositions_V17_Shadow(row),
            "gdb": gdb.strip()
        })
    results = [["STT", "Cầu Đề (V17)", "Vị Trí", "Tỷ Lệ N1", "Tỷ Lệ K2N", "Chuỗi N1"]]
    bridges_to_add = []
    min_rate = 40.0
    try:
        if SETTINGS:
            min_rate = SETTINGS.AUTO_ADD_MIN_RATE - 10.0 # Giảm ngưỡng cho Đề
    except: pass
    # Quét thuật toán
    for j in range(num_algorithms):
        idx1, idx2 = algorithms[j]
        wins_n1 = 0
        wins_k2n = 0
        current_streak = 0
        total_days = 0
        for k in range(start_idx, end_idx + 1):
            prev_data = cache_history[k-1]
            actual_data_k = cache_history[k]
            # 1. Tạo dự đoán
            p1, p2 = prev_data["positions"][idx1], prev_data["positions"][idx2]
            if p1 is None or p2 is None:
                current_streak = 0
                continue
            pred_stl = taoSTL_V30_Bong(p1, p2)
            # 2. Check N1
            is_win_n1 = check_hit_de_4_touches(pred_stl, actual_data_k["gdb"])
            # 3. Check N2
            is_win_n2 = False
            if not is_win_n1 and k + 1 < len(cache_history):
                actual_data_k1 = cache_history[k+1]
                is_win_n2 = check_hit_de_4_touches(pred_stl, actual_data_k1["gdb"])
            # Thống kê
            total_days += 1
            if is_win_n1:
                wins_n1 += 1
                wins_k2n += 1
                current_streak += 1
            else:
                current_streak = 0
                if is_win_n2:
                    wins_k2n += 1
        if total_days > 10:
            rate_n1 = (wins_n1 / total_days) * 100
            rate_k2n = (wins_k2n / total_days) * 100
            if rate_k2n >= min_rate:
                pos1_name = getPositionName_V17_Shadow(idx1)
                pos2_name = getPositionName_V17_Shadow(idx2)
                bridge_name = f"Đề {pos1_name}+{pos2_name}"
                results.append([
                    len(results),
                    bridge_name,
                    f"{idx1}+{idx2}",
                    f"{rate_n1:.1f}%",
                    f"{rate_k2n:.1f}%",
                    str(current_streak)
                ])
                # Lưu cầu: Prefix "Đề " để phân biệt
                desc = f"Cầu Đề V17. N1: {rate_n1:.1f}%, K2N: {rate_k2n:.1f}%"
                bridges_to_add.append((bridge_name, desc, f"{rate_k2n:.1f}%", db_name, idx1, idx2))
    # Batch update DB
    count = 0
    if bridges_to_add:
        # Sort by K2N rate
        bridges_to_add.sort(key=lambda x: float(x[2].replace("%", "")), reverse=True)
        top_bridges = bridges_to_add[:50] # Lấy top 50 cầu tốt nhất
        print(f">>> [DE SYSTEM] Tìm thấy {len(bridges_to_add)} cầu. Đang lưu Top {len(top_bridges)}...")
        for b in top_bridges:
            try:
                upsert_managed_bridge(b[0], b[1], b[2], b[3], b[4], b[5])
                count += 1
            except Exception as e:
                print(f"Lỗi lưu cầu đề {b[0]}: {e}")
    print(f">>> [DE SYSTEM] Hoàn tất. Đã lưu {count} cầu Đề.")
    return count

def find_and_auto_manage_bridges_de(all_data_ai, db_name=DB_NAME):
    """Wrapper function để gọi từ Controller."""
    try:
        if not all_data_ai:
            return "Lỗi: Không có dữ liệu."
        # Gọi hàm dò cầu
        count = TIM_CAU_DE_TOT_NHAT(all_data_ai, 0, 0, db_name)
        return f"Đã cập nhật {count} cầu Đề (V17 4 Chạm)."
    except Exception as e:
        return f"Lỗi Dò Cầu Đề: {e}"
