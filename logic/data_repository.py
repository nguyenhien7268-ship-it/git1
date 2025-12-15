# Tên file: code6/logic/data_repository.py
# (PHIÊN BẢN V10.2 - FIX: THÊM get_bridge_by_name ĐỂ CHẠY BACKTEST POPUP)

import sqlite3
import os
from datetime import datetime
import re

# --- CẤU HÌNH ĐƯỜNG DẪN DB TUYỆT ĐỐI ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
data_dir = os.path.join(project_root, "data")
DB_NAME = os.path.join(data_dir, "xo_so_prizes_all_logic.db")
# ----------------------------------------

# Import các hàm xử lý cầu V17
try:
    from logic.bridges.bridges_v16 import getAllPositions_V17_Shadow, taoSTL_V30_Bong, get_index_from_name_V16
except ImportError:
    # Fallback dummy
    def getAllPositions_V17_Shadow(row): return []
    def taoSTL_V30_Bong(p1, p2): return ["00", "00"]
    def get_index_from_name_V16(name): return None

# Import các hàm xử lý Memory Bridge (Bạc Nhớ)
try:
    from logic.bridges.bridges_memory import calculate_bridge_stl, get_27_loto_positions
except ImportError:
    def calculate_bridge_stl(loto1, loto2, algorithm_type): return ["00", "00"]
    def get_27_loto_positions(row): return ["00"] * 27

# Import logic phụ trợ cho Cầu Đề (Mới bổ sung)
try:
    from logic.de_utils import get_touches_by_offset
except ImportError:
    def get_touches_by_offset(b, k): return []

def load_data_ai_from_db(db_name=DB_NAME):
    """Tải toàn bộ dữ liệu A:I từ DB (10 cột). Trả về (rows, message)"""
    if not os.path.exists(db_name):
        return None, f"Lỗi: Không tìm thấy database '{db_name}'. Vui lòng chạy 'Nạp File' trước."

    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(
            """
        SELECT MaSoKy, Col_A_Ky, Col_B_GDB, Col_C_G1, Col_D_G2, Col_E_G3, Col_F_G4, Col_G_G5, Col_H_G6, Col_I_G7
        FROM DuLieu_AI
        ORDER BY MaSoKy ASC
        """
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None, f"Lỗi: Database '{db_name}' rỗng."

        return rows, f"Đã tải {len(rows)} hàng A:I từ CSDL."
    except Exception as e:
        return None, f"Lỗi SQL khi tải dữ liệu A:I: {e}"


def get_all_data_ai(db_name=DB_NAME):
    """(V7.9 Extension) Wrapper lấy dữ liệu A:I dạng list."""
    rows, _ = load_data_ai_from_db(db_name)
    return rows if rows else []


def get_all_managed_bridges(db_name=DB_NAME, only_enabled=False):
    """(V7.1) Lấy danh sách Cầu Đã Lưu."""
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql_query = "SELECT * FROM ManagedBridges"
        if only_enabled:
            sql_query += " WHERE is_enabled = 1"
        sql_query += " ORDER BY name ASC"

        cursor.execute(sql_query)
        # Chuyển đổi [sqlite3.Row] thành [dict] để dễ thao tác
        return [dict(row) for row in cursor.fetchall()]

    except Exception:
        return []
    finally:
        if conn: conn.close()


def get_managed_bridges_with_prediction(db_name=DB_NAME, current_data=None, only_enabled=True):
    """
    (V7.9.5 - FIX) Lấy danh sách Cầu và TÍNH TOÁN DỰ ĐOÁN NÓNG (Real-time).
    Hỗ trợ giải mã tên cầu Bạc Nhớ (LO_MEM) và Cầu Đề (DE_DYN).
    """
    # 1. Lấy danh sách cầu thô từ DB
    bridges = get_all_managed_bridges(db_name, only_enabled=only_enabled)
    
    # Nếu không có dữ liệu mới, trả về ngay (không thể tính toán)
    if not current_data or len(current_data) == 0:
        return bridges
    
    # Chuẩn bị dữ liệu kỳ mới nhất
    last_row = current_data[-1]
    positions = getAllPositions_V17_Shadow(last_row) # 214 vị trí (V17)
    lotos_27 = get_27_loto_positions(last_row)       # 27 giải loto (Memory)
    
    for bridge in bridges:
        try:
            # Nếu DB đã lưu sẵn next_prediction_stl thì có thể dùng luôn, 
            # nhưng để đảm bảo tính real-time (khi nạp dữ liệu mới), ta nên tính lại.
            
            b_name = bridge.get("name", "")
            
            # === [CASE 1] CẦU BẠC NHỚ LÔ (LO_MEM) ===
            # Format: LO_MEM_DIFF_Lô G3.5_Lô G6.3
            if b_name.startswith("LO_MEM_"):
                parts = b_name.split("_")
                # parts VD: ['LO', 'MEM', 'DIFF', 'Lô G3.5', 'Lô G6.3']
                if len(parts) >= 5:
                    algo_type = parts[2].lower() # 'diff' hoặc 'sum'
                    pos1_name = parts[3]
                    pos2_name = parts[4]
                    
                    # Map tên vị trí (Lô G3.5) sang index (0-26)
                    idx1 = _map_loto_name_to_index(pos1_name)
                    idx2 = _map_loto_name_to_index(pos2_name)
                    
                    if idx1 is not None and idx2 is not None:
                        # Đảm bảo index nằm trong 27 giải
                        if idx1 < len(lotos_27) and idx2 < len(lotos_27):
                            val1 = lotos_27[idx1]
                            val2 = lotos_27[idx2]
                            
                            # Tính STL dựa trên thuật toán bạc nhớ
                            stl = calculate_bridge_stl(val1, val2, algo_type)
                            if stl and isinstance(stl, list) and len(stl) > 0:
                                bridge["next_prediction_stl"] = ",".join(stl)
                                continue

            # === [CASE 2] CẦU ĐỀ DYNAMIC (DE_DYN) ===
            # Format: DE_DYN_G1_G2_K3
            elif b_name.startswith("DE_DYN_"):
                parts = b_name.split("_")
                if len(parts) >= 5:
                    n1, n2, k_str = parts[2], parts[3], parts[4]
                    k_val = int(k_str.replace("K", ""))
                    
                    # Lấy số cuối từ tên giải (G1, G2...)
                    d1 = _extract_digit_from_col(last_row, n1)
                    d2 = _extract_digit_from_col(last_row, n2)
                    
                    if d1 is not None and d2 is not None:
                        base_sum = (d1 + d2) % 10
                        # Hàm này từ logic.de_utils
                        touches = get_touches_by_offset(base_sum, k_val)
                        bridge["next_prediction_stl"] = ",".join(map(str, touches))
                        continue

            # === [CASE 3] CẦU VỊ TRÍ CỔ ĐIỂN (G1[0]_G2[1]) ===
            # Format có chứa "[...]"
            elif "[" in b_name and "]" in b_name:
                matches = re.findall(r"(?:Bong\()?(?:G\d+|GDB)\.?\d*\[\d+\]\)?", b_name)
                if len(matches) >= 2:
                    idx1 = get_index_from_name_V16(matches[0])
                    idx2 = get_index_from_name_V16(matches[1])
                    
                    if idx1 is not None and idx2 is not None:
                        if idx1 < len(positions) and idx2 < len(positions):
                            v1, v2 = positions[idx1], positions[idx2]
                            if v1 is not None and v2 is not None:
                                if "DE_POS" in b_name:
                                    # Cầu tổng đề
                                    res = (int(v1) + int(v2)) % 10
                                    bridge["next_prediction_stl"] = str(res)
                                else:
                                    # Cầu ghép lô
                                    stl = taoSTL_V30_Bong(int(v1), int(v2))
                                    bridge["next_prediction_stl"] = ",".join(stl)

        except Exception as e:
            # Nếu lỗi tính toán, giữ nguyên giá trị cũ
            # print(f"Calc error: {e}")
            pass
            
    return bridges

# --- HÀM HELPER GIẢI MÃ TÊN ---

def _map_loto_name_to_index(name):
    """
    Chuyển tên vị trí Lô (VD: 'Lô G3.5') sang index (0-26).
    Dùng cho Cầu Bạc Nhớ Lô.
    """
    clean_name = name.replace("Lô ", "").strip()
    
    # Bảng mapping cơ sở (Start index của từng giải trong list 27 số)
    # GDB:0, G1:1, G2:2, G3:4, G4:10, G5:14, G6:20, G7:23
    base_map = {
        "GDB": 0, "G1": 1,
        "G2": 2, "G3": 4, 
        "G4": 10, "G5": 14, 
        "G6": 20, "G7": 23
    }
    
    try:
        if "." in clean_name:
            # Dạng G3.5, G2.1
            parts = clean_name.split(".")
            g_name = parts[0]
            # sub_idx trong tên thường là 1-based (G3.1), cần chuyển về 0-based
            sub_idx = int(parts[1]) - 1 
            
            base = base_map.get(g_name)
            if base is not None:
                return base + sub_idx
        else:
            # Dạng GDB, G1 (chỉ có 1 con hoặc không có chấm)
            return base_map.get(clean_name)
            
    except:
        return None
    return None

def _extract_digit_from_col(row, col_name):
    """
    Helper: Lấy số cuối từ tên cột trong DB (VD: G1 -> row[3]).
    Dùng cho Cầu Đề Dynamic.
    """
    # Mapping tên cột sang index trong all_data_ai (10 cột)
    # 0:Ky, 1:Date, 2:GDB, 3:G1, 4:G2...
    col_map = {
        "GDB": 2, "G1": 3, 
        "G2": 4, "G2.1": 4, "G2.2": 4,
        "G3": 5, "G4": 6, "G5": 7, "G6": 8, "G7": 9
    }
    
    base_name = col_name.split(".")[0]
    idx = col_map.get(base_name)
    
    if idx is None or idx >= len(row): return None
    
    val_str = str(row[idx])
    # Lấy số cuối cùng trong chuỗi giải
    digits = ''.join(filter(str.isdigit, val_str))
    if not digits: return None
    
    return int(digits[-1])

def get_latest_ky_date(conn):
    """
    Lấy kỳ mới nhất và ngày tương ứng từ CSDL để kiểm tra trùng lặp khi nạp thêm.
    Trả về: (latest_ky_str, latest_date_str) hoặc (None, None)
    """
    try:
        cursor = conn.cursor()
        # Ưu tiên lấy từ bảng results_A_I (dữ liệu chính)
        cursor.execute("SELECT ky, date FROM results_A_I ORDER BY CAST(ky AS INTEGER) DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return str(row[0]), str(row[1])
            
        # Nếu không có, thử bảng DuLieu_AI
        cursor.execute("SELECT Col_A_Ky FROM DuLieu_AI ORDER BY MaSoKy DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return str(row[0]), None
            
        return None, None
    except Exception as e:
        print(f"Lỗi get_latest_ky_date: {e}")
        return None, None

def get_bridge_by_name(bridge_name, db_name=DB_NAME):
    """
    [FIXED V10.2] Lấy thông tin chi tiết một cầu theo tên.
    Trả về Dict đầy đủ (bao gồm pos1_idx, pos2_idx) để chạy Backtest Popup.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM ManagedBridges WHERE name = ?", (bridge_name,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    except Exception as e:
        print(f"Lỗi get_bridge_by_name: {e}")
        return None
    finally:
        if conn: conn.close()


def delete_managed_bridges_batch(
    names: list,
    db_name: str = None,
    transactional: bool = False,
    chunk_size: int = 500,
) -> dict:
    """
    Delete bridges by name in batch.

    Args:
        names: list of bridge names (strings)
        db_name: path to sqlite DB
        transactional: if True try to delete all in a single transaction (may lock)
        chunk_size: when not transactional, delete in chunks of this size

    Returns:
        dict: {
            "requested": int,
            "deleted": [names...],
            "missing": [names...],
            "failed": [{"name": name, "error": str}],
        }
    """
    if db_name is None:
        db_name = DB_NAME

    result = {"requested": len(names), "deleted": [], "missing": [], "failed": []}
    if not names:
        return result

    # Normalize unique names preserving order
    unique_names = list(dict.fromkeys(names))

    def _select_existing(cursor, chunk):
        placeholders = ",".join("?" for _ in chunk)
        cursor.execute(f"SELECT name FROM ManagedBridges WHERE name IN ({placeholders})", chunk)
        return {row[0] for row in cursor.fetchall()}

    try:
        conn = sqlite3.connect(db_name, timeout=30)
        cur = conn.cursor()

        if transactional:
            try:
                conn.execute("BEGIN")
                existing = _select_existing(cur, unique_names)
                missing = [n for n in unique_names if n not in existing]
                if existing:
                    placeholders = ",".join("?" for _ in unique_names)
                    cur.execute(f"DELETE FROM ManagedBridges WHERE name IN ({placeholders})", unique_names)
                conn.commit()
                result["deleted"] = list(existing)
                result["missing"] = missing
            except Exception as e:
                conn.rollback()
                result["failed"].append({"error": str(e)})
            finally:
                conn.close()
            return result

        # Best-effort chunked deletes
        existing = set()
        for i in range(0, len(unique_names), chunk_size):
            chunk = unique_names[i : i + chunk_size]
            existing.update(_select_existing(cur, chunk))
        result["missing"] = [n for n in unique_names if n not in existing]

        # Delete existing in chunks
        for i in range(0, len(unique_names), chunk_size):
            chunk = [n for n in unique_names[i : i + chunk_size] if n in existing]
            if not chunk:
                continue
            try:
                placeholders = ",".join("?" for _ in chunk)
                cur.execute(f"DELETE FROM ManagedBridges WHERE name IN ({placeholders})", chunk)
                conn.commit()
                result["deleted"].extend(chunk)
            except Exception as e:
                conn.rollback()
                for n in chunk:
                    result["failed"].append({"name": n, "error": str(e)})
        conn.close()
    except Exception as e_outer:
        result["failed"].append({"error": str(e_outer)})
    return result