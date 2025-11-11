import sqlite3
import re

# ĐÃ SỬA: Cập nhật đường dẫn DB mới sau khi di chuyển file sang thư mục 'data/'
DB_NAME = 'data/xo_so_prizes_all_logic.db' 

PRIZE_TO_COL_MAP = {
    "Đặc Biệt": "Col_B_GDB", "Nhất": "Col_C_G1", "Nhì": "Col_D_G2",
    "Ba": "Col_E_G3", "Bốn": "Col_F_G4", "Năm": "Col_G_G5",
    "Sáu": "Col_H_G6", "Bảy": "Col_I_G7",
}

# --- Import từ file .bridges_v16 (sẽ được tạo) ---
# (Chúng ta cần file này để dịch tên cầu khi thêm cầu)
try:
    from .bridges.bridges_v16 import get_index_from_name_V16 # ĐÃ FIX IMPORT RELATIVE
except ImportError:
    # Fallback cho trường hợp chạy độc lập (nếu có)
    try:
        from logic.bridges.bridges_v16 import get_index_from_name_V16 # ĐÃ FIX IMPORT FALLBACK
    except ImportError:
        print("Lỗi: Không thể import get_index_from_name_V16 trong db_manager.py")
        # Định nghĩa hàm giả để tránh lỗi
        def get_index_from_name_V16(name): return None


def setup_database(db_name=DB_NAME):
    """
    (CẬP NHẬT GIAI ĐOẠN 4)
    Thêm cột max_lose_streak_k2n cho Quản lý Rủi ro K2N.
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
    """Hàm lõi: Chỉ xử lý và chèn 1 hàng A:I vào DuLieu_AI."""
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

def get_all_kys_from_db(db_name=DB_NAME):
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT MaSoKy, NgayThang, ThoiGian FROM KyQuay ORDER BY MaSoKy DESC')
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"Lỗi get_all_kys_from_db: {e}")
        return []

def get_results_by_ky(ma_so_ky, db_name=DB_NAME):
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM DuLieu_AI WHERE MaSoKy = ?', (ma_so_ky,))
        row = cursor.fetchone()
        conn.close()
        return row
    except Exception as e:
        print(f"Lỗi get_results_by_ky: {e}")
        return None

# --- CRUD Functions for ManagedBridges ---

def add_managed_bridge(bridge_name, description, win_rate_text, db_name=DB_NAME):
    """(CẬP NHẬT) Thêm một cầu mới vào DB. Lưu cả tỷ lệ."""
    try:
        parts = bridge_name.split('+')
        if len(parts) != 2:
            return False, "Tên cầu không hợp lệ. Phải có dạng 'Vị trí 1 + Vị trí 2'."
        
        pos1_name = parts[0].strip()
        pos2_name = parts[1].strip()
        pos1_idx = get_index_from_name_V16(pos1_name)
        pos2_idx = get_index_from_name_V16(pos2_name)
        
        if pos1_idx is None or pos2_idx is None:
            return False, f"Không thể dịch tên vị trí: '{pos1_name}' hoặc '{pos2_name}'."
            
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO ManagedBridges (name, description, pos1_name, pos2_name, pos1_idx, pos2_idx, is_enabled, win_rate_text)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        ''', (bridge_name, description, pos1_name, pos2_name, pos1_idx, pos2_idx, win_rate_text))
        conn.commit()
        conn.close()
        return True, f"Đã thêm cầu '{bridge_name}' thành công."
        
    except sqlite3.IntegrityError:
        conn.close()
        return False, f"Lỗi: Tên cầu '{bridge_name}' đã tồn tại."
    except Exception as e:
        conn.close()
        return False, f"Lỗi add_managed_bridge: {e}"


def update_managed_bridge(bridge_id, description, is_enabled, db_name=DB_NAME):
    """Cập nhật mô tả và trạng thái Bật/Tắt của cầu."""
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE ManagedBridges
        SET description = ?, is_enabled = ?
        WHERE id = ?
        ''', (description, is_enabled, bridge_id))
        conn.commit()
        conn.close()
        return True, "Cập nhật thành công."
    except Exception as e:
        conn.close()
        return False, f"Lỗi update_managed_bridge: {e}"

def delete_managed_bridge(bridge_id, db_name=DB_NAME):
    """Xóa một cầu khỏi DB."""
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM ManagedBridges WHERE id = ?', (bridge_id,))
        conn.commit()
        conn.close()
        return True, "Đã xóa cầu thành công."
    except Exception as e:
        conn.close()
        return False, f"Lỗi delete_managed_bridge: {e}"


# ===================================================================================
# (MỚI) HÀM CẬP NHẬT TỶ LỆ HÀNG LOẠT
# ===================================================================================

def update_bridge_win_rate_batch(rate_data_list, db_name=DB_NAME):
    """
    (MỚI) Cập nhật tỷ lệ (win_rate_text) cho nhiều cầu cùng lúc.
    rate_data_list: một list các tuple, ví dụ: [('55.10%', 'GDB[0] + G1[4]'), ('48.20%', 'G2.1[1] + G7.4[0]')]
    """
    updated_count = 0
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Câu lệnh SQL Update
        sql_update = "UPDATE ManagedBridges SET win_rate_text = ? WHERE name = ?"
        
        # Thực thi hàng loạt
        cursor.execututemany(sql_update, rate_data_list)
        conn.commit()
        
        updated_count = cursor.rowcount
        return True, f"Đã cập nhật tỷ lệ cho {updated_count} cầu."
        
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"Lỗi update_bridge_win_rate_batch: {e}"
    finally:
        if conn:
            conn.close()

# ===================================================================================
# (SỬA CHỮA LỖI REGEX BẠC NHỚ) HÀM TỰ ĐỘNG HÓA DÒ CẦU (UPSERT)
# ===================================================================================

def upsert_managed_bridge(bridge_name, description, win_rate_text, db_name=DB_NAME):
    """
    (SỬA LỖI REGEX BN) Tự động Thêm (nếu chưa có) hoặc Cập nhật (nếu đã có).
    Sử dụng tên cầu (name) làm khóa chính.
    """
    # Import nội bộ để đảm bảo an toàn
    import sqlite3
    try:
        from .bridges.bridges_v16 import get_index_from_name_V16
    except ImportError:
        from bridges_v16 import get_index_from_name_V16

    conn = None
    try:
        # Tách tên cầu và lấy chỉ số
        
        # BƯỚC 1: KIỂM TRA CẦU BẠC NHỚ (ƯU TIÊN 1 - Tránh lỗi Regex V17)
        if "Tổng(" in bridge_name or "Hiệu(" in bridge_name:
             # Đây là cầu Bạc Nhớ
             pos1_name = "BAC_NHO"
             pos2_name = "BAC_NHO"
             pos1_idx = -1 # Đánh dấu là cầu BN
             pos2_idx = -1
             
        # BƯỚC 2: KIỂM TRA CẦU V17/V16 (Ưu tiên 2 - Tách bằng '+')
        elif len(bridge_name.split('+')) == 2:
            parts = bridge_name.split('+')
            pos1_name = parts[0].strip()
            pos2_name = parts[1].strip()
            pos1_idx = get_index_from_name_V16(pos1_name)
            pos2_idx = get_index_from_name_V16(pos2_name)
        else:
             return False, "Tên cầu không hợp lệ."
        
        # (SỬA GĐ 2) Cầu Bạc Nhớ không thể dịch chỉ số, nhưng vẫn hợp lệ
        if (pos1_idx is None or pos2_idx is None) and (pos1_idx != -1):
            return False, f"Không thể dịch tên vị trí: '{pos1_name}' hoặc '{pos2_name}'."

        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Câu lệnh INSERT... ON CONFLICT DO UPDATE (yêu cầu CSDL SQLite 3.24+)
        cursor.execute('''
        INSERT INTO ManagedBridges (name, description, pos1_name, pos2_name, pos1_idx, pos2_idx, is_enabled, win_rate_text)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        ON CONFLICT(name) DO UPDATE SET
            description = excluded.description,
            win_rate_text = excluded.win_rate_text,
            is_enabled = 1 
        ''', (bridge_name, description, pos1_name, pos2_name, pos1_idx, pos2_idx, win_rate_text))
        
        conn.commit()
        conn.close()
        return True, f"Đã cập nhật/thêm cầu '{bridge_name}'."
        
    except Exception as e:
        if conn: conn.close()
        return False, f"Lỗi upsert_managed_bridge: {e}"


# ===================================================================================
# (MỚI) GIAI ĐOẠN 1 / BƯỚC 3a: HÀM CẬP NHẬT CACHE K2N
# ===================================================================================

def update_bridge_k2n_cache_batch(cache_data_list, db_name=DB_NAME):
    """
    (CẬP NHẬT GĐ 4) Cập nhật hàng loạt dữ liệu cache K2N (Thêm max_lose_streak).
    cache_data_list: list các tuple: 
    [(win_rate, streak, prediction, max_lose_streak, bridge_name), ...]
    """
    updated_count = 0
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # (SỬA GĐ 4) Thêm cột max_lose_streak_k2n
        sql_update = """
        UPDATE ManagedBridges 
        SET win_rate_text = ?, 
            current_streak = ?, 
            next_prediction_stl = ?,
            max_lose_streak_k2n = ?
        WHERE name = ?
        """
        
        # Thực thi hàng loạt
        cursor.executemany(sql_update, cache_data_list)
        conn.commit()
        
        updated_count = cursor.rowcount
        return True, f"Đã cập nhật K2N cache cho {updated_count} cầu."
        
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"Lỗi update_bridge_k2n_cache_batch: {e}"
    finally:
        if conn:
            conn.close()