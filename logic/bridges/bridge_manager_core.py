# Tên file: git3/logic/bridges/bridge_manager_core.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - SỬA W503)
#

import os
import sqlite3

# =========================================================================
# PATH FIX: Tự động thêm thư mục gốc (git1 - Sao chép/) vào sys.path
import sys

try:
    # Lấy đường dẫn thư mục hiện tại (logic/bridges)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Đi lên 2 cấp để lấy thư mục gốc (git1 - Sao chép/)
    project_root = os.path.dirname(os.path.dirname(current_dir))

    # Thêm thư mục gốc vào sys.path NẾU nó chưa có
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"[PATH FIX] Đã thêm {project_root} vào sys.path")
    else:
        print(f"[PATH FIX] {project_root} đã có trong sys.path")
except Exception as e_path:
    print(f"[PATH FIX] LỖI: Không thể thêm đường dẫn gốc: {e_path}")
# =========================================================================


# Import SETTINGS
try:
    # Dùng import tuyệt đối (từ gốc logic)
    from logic.config_manager import SETTINGS

    print("[IMPORT V4] Đã import thành công: SETTINGS")
except ImportError as e:
    print(f"[IMPORT V4] LỖI IMPORT SETTINGS: {e}")
    try:
        from config_manager import SETTINGS
    except ImportError:
        print(
            "LỖI: bridge_manager_core.py không thể import SETTINGS. Sử dụng fallback."
        )
        SETTINGS = type(
            "obj", (object,), {"AUTO_ADD_MIN_RATE": 50.0, "AUTO_PRUNE_MIN_RATE": 40.0}
        )

# Import DB functions (CRUD và Management)
try:
    # Dùng import tuyệt đối (từ gốc logic)
    from logic.data_repository import get_all_managed_bridges
    from logic.db_manager import DB_NAME, update_managed_bridge, upsert_managed_bridge

    print("[IMPORT V4] Đã import thành công: data_repository, db_manager")
except ImportError as e:
    # Fallback cho DB/Repo
    print(f"[IMPORT V4] LỖI IMPORT DB/REPO: {e}")
    DB_NAME = "data/xo_so_prizes_all_logic.db"

    def upsert_managed_bridge(n, d, r, db, i1=None, i2=None):
        return False, "Lỗi Import"

    def update_managed_bridge(id, d, e, db):
        return False, "Lỗi Import"

    def get_all_managed_bridges(db, o):
        return {}


# Import các hàm cầu (V17 và Bạc Nhớ)
try:
    # Dùng import tuyệt đối (từ gốc logic.bridges)
    from logic.bridges.bridges_classic import checkHitSet_V30_K2N, getAllLoto_V30
    from logic.bridges.bridges_memory import (
        calculate_bridge_stl,
        get_27_loto_names,
        get_27_loto_positions,
    )
    from logic.bridges.bridges_v16 import (
        getAllPositions_V17_Shadow,
        getPositionName_V17_Shadow,
        taoSTL_V30_Bong,
    )

    print(
        "[IMPORT V4] Đã import thành công: các hàm cầu (bridges_v16, memory, classic)"
    )
except ImportError as e:
    print(f"[IMPORT V4] LỖI IMPORT HÀM CẦU: {e}")

    def getAllPositions_V17_Shadow(r):
        return []

    def getPositionName_V17_Shadow(i):
        return "Lỗi"

    def taoSTL_V30_Bong(a, b):
        return ["00", "00"]

    def calculate_bridge_stl(l1, l2, t):
        return ["00", "00"]

    def get_27_loto_names():
        return []

    def get_27_loto_positions(r):
        return []

    def checkHitSet_V30_K2N(p, loto_set):
        return "Lỗi"

    def getAllLoto_V30(r):
        return []


# ===================================================================================
# I. HÀM DÒ CẦU (ĐÃ DI CHUYỂN TỪ BACKTESTER V7.0)
# ===================================================================================


def TIM_CAU_TOT_NHAT_V16(
    toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME
):
    """
    (V7.0) Hàm dò cầu V17 (Shadow)
    """
    print("Bắt đầu Dò Cầu Tốt Nhất V17 (Shadow)...")

    allData, finalEndRow, startCheckRow, offset = (
        toan_bo_A_I,
        ky_ket_thuc_kiem_tra,
        ky_bat_dau_kiem_tra + 1,
        ky_bat_dau_kiem_tra,
    )

    headers = ["STT", "Cầu (V17 Shadow)", "Vị Trí", "Tỷ Lệ %", "Chuỗi"]
    results = [headers]

    positions_shadow = getAllPositions_V17_Shadow(allData[0])
    num_positions_shadow = len(positions_shadow)

    if num_positions_shadow == 0:
        return [["LỖI:", "Không thể lấy Vị Trí V17 Shadow."]]

    algorithms = []
    for i in range(num_positions_shadow):
        for j in range(i, num_positions_shadow):
            algorithms.append((i, j))

    num_algorithms = len(algorithms)
    print(
        f"Đã tạo {num_algorithms} thuật toán V17. Bắt đầu tiền xử lý {len(allData)} hàng..."
    )

    processedData = []
    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0:
            continue
        prevRow, actualRow = allData[prevRow_idx], allData[actualRow_idx]
        if (
            not prevRow
            or not actualRow
            or not actualRow[0]
            or str(actualRow[0]).strip() == ""
            or len(actualRow) < 10
            or not actualRow[9]
        ):
            continue

        processedData.append(
            {
                "prevPositions": getAllPositions_V17_Shadow(prevRow),
                "actualLotoSet": set(getAllLoto_V30(actualRow)),
            }
        )

    print("Tiền xử lý hoàn tất. Bắt đầu dò cầu...")

    totalTestDays = len(processedData)
    if totalTestDays == 0:
        return [["LỖI:", "Không có dữ liệu hợp lệ để backtest."]]

    AUTO_ADD_MIN_RATE = SETTINGS.AUTO_ADD_MIN_RATE
    bridges_to_add = []

    for j in range(num_algorithms):
        alg = algorithms[j]
        idx1, idx2 = alg[0], alg[1]
        win_count, current_streak, max_streak = 0, 0, 0

        for dayData in processedData:
            prevPositions = dayData["prevPositions"]
            actualLotoSet = dayData["actualLotoSet"]
            a, b = prevPositions[idx1], prevPositions[idx2]
            if a is None or b is None:
                current_streak = 0
                continue

            pred_stl = taoSTL_V30_Bong(a, b)
            check_result = checkHitSet_V30_K2N(pred_stl, actualLotoSet)

            if "✅" in check_result:
                win_count += 1
                current_streak += 1
            else:
                current_streak = 0
            max_streak = max(max_streak, current_streak)

        if totalTestDays > 0:
            rate = (win_count / totalTestDays) * 100
            if rate >= AUTO_ADD_MIN_RATE:
                pos1_name = getPositionName_V17_Shadow(idx1)
                pos2_name = getPositionName_V17_Shadow(idx2)
                bridge_name = f"{pos1_name}+{pos2_name}"
                rate_str = f"{rate:.2f}%"

                results.append(
                    [
                        len(results),
                        bridge_name,
                        f"{pos1_name} + {pos2_name}",
                        rate_str,
                        f"{current_streak} (Max {max_streak})",
                    ]
                )
                bridges_to_add.append(
                    (bridge_name, bridge_name, rate_str, db_name, idx1, idx2)
                )

    if bridges_to_add:
        print(f"Dò cầu V17: Tự động thêm/cập nhật {len(bridges_to_add)} cầu...")
        try:
            # Dùng list comprehension
            [
                upsert_managed_bridge(n, d, r, db, i1, i2)
                for n, d, r, db, i1, i2 in bridges_to_add
            ]
        except Exception as e_db:
            print(f"Lỗi khi batch update cầu V17: {e_db}")

    print("Hoàn tất Dò Cầu Tốt Nhất V17.")
    return results


# ===================================================================================
# II. HÀM DÒ CẦU BẠC NHỚ (ĐÃ DI CHUYỂN TỪ BACKTESTER V7.0)
# ===================================================================================


def TIM_CAU_BAC_NHO_TOT_NHAT(
    toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME
):
    """
    (V7.0) Hàm dò cầu Bạc Nhớ
    """
    print("Bắt đầu Dò Cầu Bạc Nhớ Tốt Nhất (756 cầu)...")

    allData, finalEndRow, startCheckRow, offset = (
        toan_bo_A_I,
        ky_ket_thuc_kiem_tra,
        ky_bat_dau_kiem_tra + 1,
        ky_bat_dau_kiem_tra,
    )

    loto_names = get_27_loto_names()
    num_positions = len(loto_names)

    algorithms = []
    headers = ["STT", "Cầu (Bạc Nhớ)", "Vị Trí", "Tỷ Lệ %", "Chuỗi"]

    for i in range(num_positions):
        for j in range(i, num_positions):
            name_sum = f"Tổng({loto_names[i]} + {loto_names[j]})"
            algorithms.append((i, j, "sum", name_sum))
            name_diff = f"Hiệu(|{loto_names[i]} - {loto_names[j]}|)"
            algorithms.append((i, j, "diff", name_diff))

    num_algorithms = len(algorithms)
    results = [headers]
    print(
        f"Đã tạo {num_algorithms} thuật toán Bạc Nhớ. Bắt đầu tiền xử lý {len(allData)} hàng..."
    )

    processedData = []
    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0:
            continue
        prevRow, actualRow = allData[prevRow_idx], allData[actualRow_idx]
        if (
            not prevRow
            or not actualRow
            or not actualRow[0]
            or str(actualRow[0]).strip() == ""
            or len(actualRow) < 10
            or not actualRow[9]
        ):
            continue

        processedData.append(
            {
                "prevLotos": get_27_loto_positions(prevRow),
                "actualLotoSet": set(getAllLoto_V30(actualRow)),
            }
        )

    print("Tiền xử lý hoàn tất. Bắt đầu dò cầu...")

    totalTestDays = len(processedData)
    if totalTestDays == 0:
        return [["LỖI:", "Không có dữ liệu hợp lệ để backtest."]]

    AUTO_ADD_MIN_RATE = SETTINGS.AUTO_ADD_MIN_RATE
    bridges_to_add = []

    for j in range(num_algorithms):
        alg = algorithms[j]
        idx1, idx2, alg_type, alg_name = alg[0], alg[1], alg[2], alg[3]
        win_count, current_streak, max_streak = 0, 0, 0

        for dayData in processedData:
            prevLotos = dayData["prevLotos"]
            actualLotoSet = dayData["actualLotoSet"]
            loto1, loto2 = prevLotos[idx1], prevLotos[idx2]
            pred_stl = calculate_bridge_stl(loto1, loto2, alg_type)
            check_result = checkHitSet_V30_K2N(pred_stl, actualLotoSet)

            if "✅" in check_result:
                win_count += 1
                current_streak += 1
            else:
                current_streak = 0
            max_streak = max(max_streak, current_streak)

        if totalTestDays > 0:
            rate = (win_count / totalTestDays) * 100
            if rate >= AUTO_ADD_MIN_RATE:
                rate_str = f"{rate:.2f}%"
                results.append(
                    [
                        len(results),
                        alg_name,
                        f"{loto_names[idx1]} + {loto_names[idx2]}",
                        rate_str,
                        f"{current_streak} (Max {max_streak})",
                    ]
                )
                # Bạc nhớ (V17) có pos1_idx = -1
                bridges_to_add.append((alg_name, alg_name, rate_str, db_name, -1, -1))

    if bridges_to_add:
        print(f"Dò cầu Bạc Nhớ: Tự động thêm/cập nhật {len(bridges_to_add)} cầu...")
        try:
            # Dùng list comprehension
            [
                upsert_managed_bridge(n, d, r, db, i1, i2)
                for n, d, r, db, i1, i2 in bridges_to_add
            ]
        except Exception as e_db:
            print(f"Lỗi khi batch update cầu Bạc Nhớ: {e_db}")

    print("Hoàn tất Dò Cầu Bạc Nhớ.")
    return results


# ===================================================================================
# III. HÀM QUẢN LÝ TỰ ĐỘNG (ĐÃ DI CHUYỂN TỪ BACKTESTER V7.0)
# ===================================================================================


def find_and_auto_manage_bridges(all_data_ai, db_name=DB_NAME):
    """
    (V7.0) Wrapper: Chạy cả 2 hàm dò cầu (V17 + Bạc Nhớ) và cập nhật DB.
    """
    try:
        if not all_data_ai:
            return "Lỗi: Không có dữ liệu A:I để dò cầu."

        ky_bat_dau = 2
        ky_ket_thuc = len(all_data_ai) + (ky_bat_dau - 1)

        print("... (Auto Find) Bắt đầu dò Cầu V17 (Shadow)...")
        results_v17 = TIM_CAU_TOT_NHAT_V16(
            all_data_ai, ky_bat_dau, ky_ket_thuc, db_name
        )
        count_v17 = len(results_v17) - 1 if results_v17 and len(results_v17) > 1 else 0

        print("... (Auto Find) Bắt đầu dò Cầu Bạc Nhớ...")
        results_memory = TIM_CAU_BAC_NHO_TOT_NHAT(
            all_data_ai, ky_bat_dau, ky_ket_thuc, db_name
        )
        count_memory = (
            len(results_memory) - 1 if results_memory and len(results_memory) > 1 else 0
        )

        return f"Dò cầu hoàn tất. Tự động thêm/cập nhật {count_v17} cầu V17 và {count_memory} cầu Bạc Nhớ."

    except Exception as e:
        return f"Lỗi nghiêm trọng trong find_and_auto_manage_bridges: {e}"


def prune_bad_bridges(all_data_ai, db_name=DB_NAME):
    """
    (V7.0) Tự động TẮT (disable) các cầu có tỷ lệ K2N thấp (đã cache).
    """
    try:
        # (V7.1) Đã chuyển sang .config_manager
        AUTO_PRUNE_MIN_RATE = SETTINGS.AUTO_PRUNE_MIN_RATE
    except Exception as e_cfg:
        print(f"Lỗi đọc config: {e_cfg}. Dùng AUTO_PRUNE_MIN_RATE=40.0")
        AUTO_PRUNE_MIN_RATE = 40.0

    disabled_count = 0

    # Bước 1: Lấy danh sách các cầu đang Bật (enabled)
    try:
        # (V7.1) Đã chuyển sang .data_repository
        managed_bridges_list = get_all_managed_bridges(db_name, only_enabled=True)
        if not managed_bridges_list:
            return "Lỗi: Không có cầu nào được Bật để lọc."

        # Chuyển sang map/dict để dễ tra cứu
        managed_bridges_map = {b["name"]: b for b in managed_bridges_list}

    except Exception as e_db:
        return f"Lỗi DB khi tải Cầu Đã Lưu: {e_db}"

    if not managed_bridges_map:
        return "Lỗi: Không có cầu nào được Bật để lọc."

    print(f"... (Lọc Cầu Yếu) Đang kiểm tra {len(managed_bridges_map)} cầu đã bật...")

    # Bước 2: Duyệt các cầu đã cache và lọc
    for bridge_name, bridge_data in managed_bridges_map.items():
        try:
            # Đọc tỷ lệ từ cache K2N
            win_rate_str = str(bridge_data.get("win_rate_text", "0%")).replace("%", "")

            if not win_rate_str or win_rate_str == "N/A":
                continue

            win_rate = float(win_rate_str)

            # Nếu cầu còn được bật (enabled) VÀ tỷ lệ thấp
            if win_rate < AUTO_PRUNE_MIN_RATE:

                bridge_id = bridge_data["id"]
                old_desc = bridge_data["description"]

                # Gọi hàm update, set is_enabled = 0
                update_managed_bridge(bridge_id, old_desc, 0, db_name)
                disabled_count += 1

        except Exception as e_row:
            print(f"Lỗi xử lý lọc cầu: {bridge_name}, Lỗi: {e_row}")

    return f"Lọc cầu hoàn tất. Đã TẮT {disabled_count} cầu yếu (Tỷ lệ K2N < {AUTO_PRUNE_MIN_RATE}%)."


# ===================================================================================
# IV. HÀM NẠP 756 CẦU BẠC NHỚ (GIAI ĐOẠN 2)
# ===================================================================================


def init_all_756_memory_bridges_to_db(db_name=DB_NAME, progress_callback=None):
    """
    Sinh 756 cầu Bạc Nhớ và lưu vào database:
    - 378 cầu Tổng: Tổng(00+01), Tổng(00+02), ...
    - 378 cầu Hiệu: Hiệu(00-01), Hiệu(00-02), ...

    Mỗi cầu có:
    - bridge_name: "Tổng(00+01)" hoặc "Hiệu(00-01)" (format với 2 chữ số)
    - pos1_idx: -1 (đánh dấu là Bạc Nhớ)
    - pos2_idx: -1
    - is_enabled: False (mặc định tắt)

    Args:
        db_name: Tên database
        progress_callback: Hàm callback để báo tiến độ, nhận (current, total, message)

    Returns:
        tuple: (success: bool, message: str, added_count: int, skipped_count: int)
    """
    print("Bắt đầu nạp 756 cầu Bạc Nhớ vào database...")

    bridges_to_add = []
    total_bridges = 0

    # Sinh tất cả các cầu Tổng và Hiệu
    for i in range(27):  # 27 vị trí (00-26)
        for j in range(i, 27):  # j >= i để tránh trùng lặp
            # 1. Cầu Tổng
            bridge_name_sum = f"Tổng({i:02d}+{j:02d})"
            bridges_to_add.append(
                (bridge_name_sum, bridge_name_sum, "N/A", db_name, -1, -1)
            )
            total_bridges += 1

            # 2. Cầu Hiệu
            bridge_name_diff = f"Hiệu({i:02d}-{j:02d})"
            bridges_to_add.append(
                (bridge_name_diff, bridge_name_diff, "N/A", db_name, -1, -1)
            )
            total_bridges += 1

    print(f"Đã tạo danh sách {total_bridges} cầu Bạc Nhớ.")

    # Thêm từng cầu vào database
    added_count = 0
    skipped_count = 0

    for idx, (bridge_name, description, win_rate, db, pos1, pos2) in enumerate(bridges_to_add):
        try:
            # Gọi upsert_managed_bridge với is_enabled = 0 (tắt mặc định)
            # Nếu cầu đã tồn tại, sẽ bỏ qua (không cập nhật)
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()

            # Kiểm tra xem cầu đã tồn tại chưa
            cursor.execute("SELECT id FROM ManagedBridges WHERE name = ?", (bridge_name,))
            existing = cursor.fetchone()

            if existing:
                skipped_count += 1
            else:
                # Thêm cầu mới với is_enabled = 0 (tắt)
                cursor.execute(
                    """
                    INSERT INTO ManagedBridges
                    (name, description, win_rate_text, pos1_idx, pos2_idx, is_enabled)
                    VALUES (?, ?, ?, ?, ?, 0)
                    """,
                    (bridge_name, description, win_rate, pos1, pos2)
                )
                conn.commit()
                added_count += 1

            conn.close()

            # Gọi callback để báo tiến độ
            if progress_callback and (idx + 1) % 50 == 0:
                progress_callback(idx + 1, total_bridges, f"Đã xử lý {idx + 1}/{total_bridges} cầu...")

        except Exception as e:
            print(f"Lỗi khi thêm cầu {bridge_name}: {e}")
            skipped_count += 1

    # Báo tiến độ hoàn tất
    if progress_callback:
        progress_callback(total_bridges, total_bridges, "Hoàn tất!")

    success_msg = (
        f"Đã nạp thành công {added_count} cầu Bạc Nhớ mới vào database.\n"
        f"Bỏ qua {skipped_count} cầu đã tồn tại."
    )
    print(success_msg)

    return True, success_msg, added_count, skipped_count
