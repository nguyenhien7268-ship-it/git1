import sqlite3
import re
from typing import Optional, List, Tuple, Any

# ĐÃ SỬA: Cập nhật đường dẫn DB mới sau khi di chuyển file sang thư mục 'data/'
DB_NAME = 'data/xo_so_prizes_all_logic.db' 

PRIZE_TO_COL_MAP = {
    "Đặc Biệt": "Col_B_GDB", "Nhất": "Col_C_G1", "Nhì": "Col_D_G2",
    "Ba": "Col_E_G3", "Bốn": "Col_F_G4", "Năm": "Col_G_G5",
    "Sáu": "Col_H_G6", "Bảy": "Col_I_G7",
}

# (ĐÃ XÓA) Xóa bỏ khối import 'get_index_from_name_V16'
# Việc import từ lớp CSDL lên lớp Logic đã vi phạm kiến trúc GĐ 1
# và gây ra lỗi import tuần hoàn.


def setup_database(db_name=DB_NAME) -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
    """
    (CẬP NHẬT GIAI ĐOẠN 4)
    Thêm cột max_lose_streak_k2n cho Quản lý Rủi ro K2N.
    
    (REFRACTOR GĐ 1) Hàm này là nguồn gốc của kết nối.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS KyQuay (
        MaSoKy TEXT PRIMARY KEY,
        NgayThang TEXT,
        ThoiGian TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS DuLieu_AI (
        MaSoKy TEXT PRIMARY KEY,
        Col_A_Ky TEXT,
        Col_B_GDB TEXT,
        Col_C_G1 TEXT,
        Col_D_G2 TEXT,
        Col_E_G3 TEXT,
        Col_F_G4 TEXT,
        Col_G_G5 TEXT,
        Col_H_G6 TEXT,
        Col_I_G7 TEXT,
        FOREIGN KEY (MaSoKy) REFERENCES KyQuay(MaSoKy)
    )
    ''')
    
    # (SỬA ĐỔI GIAI ĐOẠN 4)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ManagedBridges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        pos1_name TEXT,
        pos2_name TEXT,
        pos1_idx INTEGER,
        pos2_idx INTEGER,
        is_enabled INTEGER DEFAULT 1,
        win_rate_text TEXT,
        
        -- Cột cache Giai đoạn 1
        current_streak INTEGER DEFAULT 0,
        next_prediction_stl TEXT,
        
        -- (MỚI GĐ 4) Thêm cột cho Quản lý Rủi ro
        max_lose_streak_k2n INTEGER DEFAULT 0
    )
    ''')
    
    # (MỚI) Kiểm tra và thêm cột nếu bảng đã tồn tại (cho nâng cấp)
    try:
        cursor.execute('ALTER TABLE ManagedBridges ADD COLUMN current_streak INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass # Cột đã tồn tại
    try:
        cursor.execute('ALTER TABLE ManagedBridges ADD COLUMN next_prediction_stl TEXT')
    except sqlite3.OperationalError:
        pass # Cột đã tồn tại
    # (MỚI GĐ 4)
    try:
        cursor.execute('ALTER TABLE ManagedBridges ADD COLUMN max_lose_streak_k2n INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass # Cột đã tồn tại
        
    conn.commit()
    return conn, cursor

def _process_ky_entry(ma_so_ky, prize_table_content, cursor):
    """
    Hàm lõi: Chỉ xử lý và chèn 1 hàng A:I vào DuLieu_AI.
    (REFRACTOR GĐ 1) Hàm này đã chấp nhận cursor, không cần sửa.
    """
    ket_qua_dict = {}
    for row in prize_table_content:
        if isinstance(row, (list, tuple)) and len(row) == 2:
            ket_qua_dict[row[0]] = row[1]
            
    if not ket_qua_dict:
        print(f"Lỗi _process_ky_entry: Không có dữ liệu giải cho kỳ {ma_so_ky}")
        return 0
        
    ai_row = {
        "MaSoKy": ma_so_ky, "Col_A_Ky": ma_so_ky,
        "Col_B_GDB": None, "Col_C_G1": None, "Col_D_G2": None, "Col_E_G3": None,
        "Col_F_G4": None, "Col_G_G5": None, "Col_H_G6": None, "Col_I_G7": None,
    }

    for ten_giai, giai_data in ket_qua_dict.items():
        so_trung_thuong_list = []
        if isinstance(giai_data, str):
            so_trung_thuong_list = [s.strip() for s in giai_data.replace('-', ' ').split() if s.strip()]
        elif isinstance(giai_data, list):
            so_trung_thuong_list = [s.strip() for s in giai_data if s and s.strip()]
        if not so_trung_thuong_list:
            continue
        col_name = PRIZE_TO_COL_MAP.get(ten_giai)
        if col_name:
            ai_row[col_name] = ",".join(so_trung_thuong_list)

    cursor.execute('''
    INSERT INTO DuLieu_AI (MaSoKy, Col_A_Ky, Col_B_GDB, Col_C_G1, Col_D_G2, Col_E_G3, Col_F_G4, Col_G_G5, Col_H_G6, Col_I_G7)
    VALUES (:MaSoKy, :Col_A_Ky, :Col_B_GDB, :Col_C_G1, :Col_D_G2, :Col_E_G3, :Col_F_G4, :Col_G_G5, :Col_H_G6, :Col_I_G7)
    ''', ai_row)
    return 1

# ===================================================================================
# CÁC HÀM TRA CỨU & QUẢN LÝ CẦU
# ===================================================================================

def get_all_kys_from_db(db_name: str = DB_NAME, conn: Optional[sqlite3.Connection] = None) -> List[Tuple]:
    """
    (REFRACTOR GĐ 1) Chấp nhận conn tùy chọn.
    """
    local_conn = conn
    should_close = False
    if local_conn is None:
        local_conn = sqlite3.connect(db_name)
        should_close = True
        
    try:
        cursor = local_conn.cursor()
        cursor.execute('SELECT MaSoKy, NgayThang, ThoiGian FROM KyQuay ORDER BY MaSoKy DESC')
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        print(f"Lỗi get_all_kys_from_db: {e}")
        return []
    finally:
        if should_close and local_conn:
            local_conn.close()

def get_results_by_ky(ma_so_ky: str, db_name: str = DB_NAME, conn: Optional[sqlite3.Connection] = None) -> Optional[Tuple]:
    """
    (REFRACTOR GĐ 1) Chấp nhận conn tùy chọn.
    """
    local_conn = conn
    should_close = False
    if local_conn is None:
        local_conn = sqlite3.connect(db_name)
        should_close = True
        
    try:
        cursor = local_conn.cursor()
        cursor.execute('SELECT * FROM DuLieu_AI WHERE MaSoKy = ?', (ma_so_ky,))
        row = cursor.fetchone()
        return row
    except Exception as e:
        print(f"Lỗi get_results_by_ky: {e}")
        return None
    finally:
        if should_close and local_conn:
            local_conn.close()

# --- CRUD Functions for ManagedBridges ---

def add_managed_bridge(
    bridge_name: str, description: str, win_rate_text: str,
    pos1_name: str, pos2_name: str, pos1_idx: int, pos2_idx: int,
    db_name: str = DB_NAME, conn: Optional[sqlite3.Connection] = None
) -> Tuple[bool, str]:
    """
    (REFRACTOR GĐ 1) Thêm một cầu mới vào DB.
    Hàm này đã được tái cấu trúc để chỉ nhận dữ liệu, không chứa logic
    tính toán 'pos_idx' nữa.
    """
    local_conn = conn
    should_close = False
    if local_conn is None:
        local_conn = sqlite3.connect(db_name)
        should_close = True
        
    try:
        # (ĐÃ XÓA) Toàn bộ logic tính toán pos_idx đã được chuyển
        # lên DataService.
            
        cursor = local_conn.cursor()
        cursor.execute('''
        INSERT INTO ManagedBridges (name, description, pos1_name, pos2_name, pos1_idx, pos2_idx, is_enabled, win_rate_text)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        ''', (bridge_name, description, pos1_name, pos2_name, pos1_idx, pos2_idx, win_rate_text))
        local_conn.commit()
        return True, f"Đã thêm cầu '{bridge_name}' thành công."
        
    except sqlite3.IntegrityError:
        return False, f"Lỗi: Tên cầu '{bridge_name}' đã tồn tại."
    except Exception as e:
        return False, f"Lỗi add_managed_bridge: {e}"
    finally:
        if should_close and local_conn:
            local_conn.close()


def update_managed_bridge(bridge_id: int, description: str, is_enabled: int, db_name: str = DB_NAME, conn: Optional[sqlite3.Connection] = None) -> Tuple[bool, str]:
    """
    Cập nhật mô tả và trạng thái Bật/Tắt của cầu.
    (REFRACTOR GĐ 1) Chấp nhận conn tùy chọn.
    """
    local_conn = conn
    should_close = False
    if local_conn is None:
        local_conn = sqlite3.connect(db_name)
        should_close = True
        
    try:
        cursor = local_conn.cursor()
        cursor.execute('''
        UPDATE ManagedBridges
        SET description = ?, is_enabled = ?
        WHERE id = ?
        ''', (description, is_enabled, bridge_id))
        local_conn.commit()
        return True, "Cập nhật thành công."
    except Exception as e:
        return False, f"Lỗi update_managed_bridge: {e}"
    finally:
        if should_close and local_conn:
            local_conn.close()

def delete_managed_bridge(bridge_id: int, db_name: str = DB_NAME, conn: Optional[sqlite3.Connection] = None) -> Tuple[bool, str]:
    """
    Xóa một cầu khỏi DB.
    (REFRACTOR GĐ 1) Chấp nhận conn tùy chọn.
    """
    local_conn = conn
    should_close = False
    if local_conn is None:
        local_conn = sqlite3.connect(db_name)
        should_close = True
        
    try:
        cursor = local_conn.cursor()
        cursor.execute('DELETE FROM ManagedBridges WHERE id = ?', (bridge_id,))
        local_conn.commit()
        return True, "Đã xóa cầu thành công."
    except Exception as e:
        return False, f"Lỗi delete_managed_bridge: {e}"
    finally:
        if should_close and local_conn:
            local_conn.close()


# ===================================================================================
# (MỚI) HÀM CẬP NHẬT TỶ LỆ HÀNG LOẠT
# ===================================================================================

def update_bridge_win_rate_batch(rate_data_list: List[Tuple[str, str]], db_name: str = DB_NAME, conn: Optional[sqlite3.Connection] = None) -> Tuple[bool, str]:
    """
    (MỚI) Cập nhật tỷ lệ (win_rate_text) cho nhiều cầu cùng lúc.
    (REFRACTOR GĐ 1) Chấp nhận conn tùy chọn.
    """
    local_conn = conn
    should_close = False
    if local_conn is None:
        local_conn = sqlite3.connect(db_name)
        should_close = True
        
    updated_count = 0
    
    try:
        cursor = local_conn.cursor()
        
        # Câu lệnh SQL Update
        sql_update = "UPDATE ManagedBridges SET win_rate_text = ? WHERE name = ?"
        
        # Thực thi hàng loạt
        cursor.executemany(sql_update, rate_data_list)
        local_conn.commit()
        
        updated_count = cursor.rowcount
        return True, f"Đã cập nhật tỷ lệ cho {updated_count} cầu."
        
    except Exception as e:
        if local_conn and should_close == False: # Chỉ rollback nếu conn được truyền vào
             local_conn.rollback()
        return False, f"Lỗi update_bridge_win_rate_batch: {e}"
    finally:
        if should_close and local_conn:
            local_conn.close()

# ===================================================================================
# (SỬA CHỮA LỖI REGEX BẠC NHỚ) HÀM TỰ ĐỘNG HÓA DÒ CẦU (UPSERT)
# ===================================================================================

def upsert_managed_bridge(
    bridge_name: str, description: str, win_rate_text: str,
    pos1_name: str, pos2_name: str, pos1_idx: int, pos2_idx: int,
    db_name: str = DB_NAME, conn: Optional[sqlite3.Connection] = None
) -> Tuple[bool, str]:
    """
    (REFRACTOR GĐ 1) Tự động Thêm (nếu chưa có) hoặc Cập nhật (nếu đã có).
    Hàm này đã được tái cấu trúc để chỉ nhận dữ liệu, không chứa logic
    tính toán 'pos_idx' nữa.
    """
    local_conn = conn
    should_close = False
    if local_conn is None:
        local_conn = sqlite3.connect(db_name)
        should_close = True
        
    try:
        # (ĐÃ XÓA) Toàn bộ logic tính toán pos_idx (bao gồm cả import nội bộ)
        # đã được chuyển lên DataService.

        cursor = local_conn.cursor()
        
        cursor.execute('''
        INSERT INTO ManagedBridges (name, description, pos1_name, pos2_name, pos1_idx, pos2_idx, is_enabled, win_rate_text)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        ON CONFLICT(name) DO UPDATE SET
            description = excluded.description,
            win_rate_text = excluded.win_rate_text,
            is_enabled = 1 
        ''', (bridge_name, description, pos1_name, pos2_name, pos1_idx, pos2_idx, win_rate_text))
        
        local_conn.commit()
        return True, f"Đã cập nhật/thêm cầu '{bridge_name}'."
        
    except Exception as e:
        if local_conn and should_close == False:
            local_conn.rollback()
        return False, f"Lỗi upsert_managed_bridge: {e}"
    finally:
        if should_close and local_conn:
            local_conn.close()


# ===================================================================================
# (MỚI) GIAI ĐOẠN 1 / BƯỚC 3a: HÀM CẬP NHẬT CACHE K2N
# ===================================================================================

def update_bridge_k2n_cache_batch(cache_data_list: List[Tuple[Any]], db_name: str = DB_NAME, conn: Optional[sqlite3.Connection] = None) -> Tuple[bool, str]:
    """
    (CẬP NHẬT GĐ 4) Cập nhật hàng loạt dữ liệu cache K2N.
    (REFRACTOR GĐ 1) Chấp nhận conn tùy chọn.
    """
    local_conn = conn
    should_close = False
    if local_conn is None:
        local_conn = sqlite3.connect(db_name)
        should_close = True
        
    updated_count = 0
    
    try:
        cursor = local_conn.cursor()
        
        sql_update = """
        UPDATE ManagedBridges 
        SET win_rate_text = ?, 
            current_streak = ?, 
            next_prediction_stl = ?,
            max_lose_streak_k2n = ?
        WHERE name = ?
        """
        
        cursor.executemany(sql_update, cache_data_list)
        local_conn.commit()
        
        updated_count = cursor.rowcount
        return True, f"Đã cập nhật K2N cache cho {updated_count} cầu."
        
    except Exception as e:
        if local_conn and should_close == False:
            local_conn.rollback()
        return False, f"Lỗi update_bridge_k2n_cache_batch: {e}"
    finally:
        if should_close and local_conn:
            local_conn.close()