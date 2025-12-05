# Tên file: logic/db_manager.py
# (PHIÊN BẢN V8.5 - FIX CRITICAL: CACHE WRITE & SELF-HEALING N/A)

import sqlite3
import os

# --- CẤU HÌNH ĐƯỜNG DẪN DB TUYỆT ĐỐI ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
data_dir = os.path.join(project_root, "data")

if not os.path.exists(data_dir):
    try:
        os.makedirs(data_dir)
        print(f">>> Đã tự động tạo thư mục: {data_dir}")
    except Exception as e:
        print(f"LỖI: Không thể tạo thư mục data: {e}")

DB_NAME = os.path.join(data_dir, "xo_so_prizes_all_logic.db")
# ----------------------------------------

# ===================================================================================
# I. HÀM THIẾT LẬP CSDL
# ===================================================================================

def setup_database(db_name=DB_NAME):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Bảng 1: DuLieu_AI
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS DuLieu_AI (
        MaSoKy INTEGER PRIMARY KEY,
        Col_A_Ky TEXT,
        Col_B_GDB TEXT, Col_C_G1 TEXT, Col_D_G2 TEXT, Col_E_G3 TEXT,
        Col_F_G4 TEXT, Col_G_G5 TEXT, Col_H_G6 TEXT, Col_I_G7 TEXT
    )"""
    )

    # Bảng 2: results_A_I
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS results_A_I (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ky TEXT UNIQUE,
        date TEXT,
        gdb TEXT, g1 TEXT, g2 TEXT, g3 TEXT, g4 TEXT, g5 TEXT, g6 TEXT, g7 TEXT,
        l0 TEXT, l1 TEXT, l2 TEXT, l3 TEXT, l4 TEXT, l5 TEXT, l6 TEXT, l7 TEXT, l8 TEXT, l9 TEXT,
        l10 TEXT, l11 TEXT, l12 TEXT, l13 TEXT, l14 TEXT, l15 TEXT, l16 TEXT, l17 TEXT, l18 TEXT, l19 TEXT,
        l20 TEXT, l21 TEXT, l22 TEXT, l23 TEXT, l24 TEXT, l25 TEXT, l26 TEXT
    )"""
    )

    # Bảng 3: ManagedBridges (Update V8.5)
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS ManagedBridges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        is_enabled INTEGER DEFAULT 1,
        date_added TEXT DEFAULT (datetime('now', 'localtime')),
        win_rate_text TEXT DEFAULT 'N/A',
        current_streak INTEGER DEFAULT 0,
        next_prediction_stl TEXT DEFAULT 'N/A',
        pos1_idx INTEGER,
        pos2_idx INTEGER,
        max_lose_streak_k2n INTEGER DEFAULT 0,
        recent_win_count_10 INTEGER DEFAULT 0,
        search_rate_text TEXT DEFAULT '0.00%',
        search_period INTEGER DEFAULT 0,
        is_pinned INTEGER DEFAULT 0,
        type TEXT DEFAULT 'UNKNOWN'
    )"""
    )

    # Self-Healing: Thêm cột nếu thiếu (Migration)
    columns_to_add = [
        ("max_lose_streak_k2n", "INTEGER DEFAULT 0"),
        ("recent_win_count_10", "INTEGER DEFAULT 0"),
        ("is_pinned", "INTEGER DEFAULT 0"),
        ("search_rate_text", "TEXT DEFAULT '0.00%'"),
        ("search_period", "INTEGER DEFAULT 0"),
        ("type", "TEXT DEFAULT 'UNKNOWN'")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE ManagedBridges ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_ky ON results_A_I(ky)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dulieu_masoky ON DuLieu_AI(MaSoKy)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bridges_enabled ON ManagedBridges(is_enabled)")

    conn.commit()
    return conn, cursor

# ===================================================================================
# II. HÀM TRUY VẤN CƠ BẢN
# ===================================================================================

def get_db_connection(db_name=DB_NAME):
    return sqlite3.connect(db_name)

def get_results_by_ky(ky_id, db_name=DB_NAME):
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM results_A_I WHERE ky = ?", (ky_id,))
        row = cursor.fetchone()
        return row
    except Exception as e:
        print(f"Lỗi get_results_by_ky: {e}")
        return None
    finally:
        if conn: conn.close()

def get_all_kys_from_db(db_name=DB_NAME):
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT ky, date FROM results_A_I ORDER BY CAST(ky AS INTEGER) DESC")
        return cursor.fetchall()
    except Exception as e:
        print(f"Lỗi get_all_kys_from_db: {e}")
        return []
    finally:
        if conn: conn.close()

def delete_ky_from_db(ky, db_name=DB_NAME):
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM results_A_I WHERE ky = ?", (ky,))
        c1 = cursor.rowcount
        cursor.execute("DELETE FROM DuLieu_AI WHERE Col_A_Ky = ?", (ky,))
        c2 = cursor.rowcount
        conn.commit()
        return True, f"Đã xóa kỳ {ky} ({c1+c2} bản ghi)"
    except Exception as e:
        return False, f"Lỗi khi xóa: {e}"
    finally:
        if conn: conn.close()

# ===================================================================================
# III. HÀM QUẢN LÝ CẦU (CRUD - CORE LOGIC)
# ===================================================================================

def delete_all_managed_bridges(conn):
    try:
        conn.cursor().execute("DELETE FROM ManagedBridges")
        print("Đã xóa sạch Cầu Đã Lưu (ManagedBridges).")
        return True
    except Exception as e:
        print(f"Lỗi delete_all_managed_bridges: {e}")
        return False

def add_managed_bridge(bridge_name, description, db_name=DB_NAME):
    # Hàm này giữ lại để tương thích ngược, logic chính nên dùng upsert
    return upsert_managed_bridge(bridge_name, description, db_name=db_name)

def update_managed_bridge(bridge_id, description=None, is_enabled=None, db_name=DB_NAME, updates=None):
    """
    Cập nhật cầu trong database với hỗ trợ cập nhật động.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        if updates is None: updates = {}
        if description is not None: updates['description'] = description
        if is_enabled is not None: updates['is_enabled'] = 1 if is_enabled else 0
        
        set_parts = []
        values = []

        allowed_fields = [
            'description', 'is_enabled', 'win_rate_text', 'max_lose_streak', 'recent_win_count_10',
            'pos1_idx', 'pos2_idx', 'search_rate_text', 'search_period', 'type'
        ]
        
        field_mapping = {'max_lose_streak': 'max_lose_streak_k2n'}
        
        for field in allowed_fields:
            if field in updates:
                db_field = field_mapping.get(field, field)
                set_parts.append(f"{db_field}=?")
                values.append(updates[field])

        if not set_parts: return True, "Không có trường nào để cập nhật."
        
        sql_update = f"UPDATE ManagedBridges SET {', '.join(set_parts)} WHERE id=?"
        values.append(bridge_id)
        
        cursor.execute(sql_update, values)
        conn.commit()
        return True, "Cập nhật thành công."
    except Exception as e:
        return False, f"Lỗi update_managed_bridge: {e}"
    finally:
        if conn: conn.close()

def delete_managed_bridge(bridge_id, db_name=DB_NAME):
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ManagedBridges WHERE id = ?", (bridge_id,))
        conn.commit()
        return True, "Xóa cầu thành công."
    except Exception as e:
        return False, f"Lỗi delete_managed_bridge: {e}"
    finally:
        if conn: conn.close()

def toggle_pin_bridge(bridge_name, db_name=DB_NAME):
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT is_pinned FROM ManagedBridges WHERE name = ?", (bridge_name,))
        row = cursor.fetchone()
        
        if not row: return False, f"Không tìm thấy cầu '{bridge_name}'", None
        
        current_pin = row[0] if row[0] is not None else 0
        new_pin = 1 if current_pin == 0 else 0
        
        cursor.execute("UPDATE ManagedBridges SET is_pinned = ? WHERE name = ?", (new_pin, bridge_name))
        conn.commit()
        
        action = "đã ghim" if new_pin == 1 else "đã bỏ ghim"
        return True, f"Cầu '{bridge_name}' {action}.", bool(new_pin)
    except Exception as e:
        return False, f"Lỗi toggle_pin_bridge: {e}", None
    finally:
        if conn: conn.close()

def upsert_managed_bridge(bridge_name, description=None, win_rate=None, db_name=DB_NAME, pos1_idx=None, pos2_idx=None, bridge_data=None):
    """
    Chèn hoặc cập nhật cầu trong database.
    (V8.5: Logic bảo vệ Search Rate và Win Rate)
    """
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        if bridge_data is None: bridge_data = {}
        # Merge tham số vào bridge_data
        if description: bridge_data['description'] = description
        if win_rate: bridge_data['win_rate_text'] = win_rate
        if pos1_idx is not None: bridge_data['pos1_idx'] = pos1_idx
        if pos2_idx is not None: bridge_data['pos2_idx'] = pos2_idx

        name = bridge_name
        
        # Kiểm tra tồn tại
        cursor.execute("SELECT * FROM ManagedBridges WHERE name = ?", (name,))
        existing_row = cursor.fetchone()
        
        if existing_row:
            cursor.execute("PRAGMA table_info(ManagedBridges)")
            col_names = [c[1] for c in cursor.fetchall()]
            existing_data = dict(zip(col_names, existing_row))
        else:
            existing_data = None

        if not existing_data:
            # INSERT MỚI
            # Mặc định: Nếu có search_rate thì dùng nó cho cả win_rate để tránh N/A ban đầu
            search_rate = bridge_data.get('search_rate_text', '0.00%')
            win_rate_val = bridge_data.get('win_rate_text', 'N/A')
            if win_rate_val == 'N/A' and search_rate != '0.00%':
                win_rate_val = search_rate

            sql_insert = """
            INSERT INTO ManagedBridges (
                name, pos1_idx, pos2_idx, is_enabled, win_rate_text, max_lose_streak_k2n, recent_win_count_10, 
                search_rate_text, search_period, description, type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            values = (
                name, bridge_data.get('pos1_idx'), bridge_data.get('pos2_idx'), bridge_data.get('is_enabled', 1),
                win_rate_val, bridge_data.get('max_lose_streak', 0), bridge_data.get('recent_win_count_10', 0),
                search_rate, bridge_data.get('search_period', 0), bridge_data.get('description', ''), bridge_data.get('type', 'UNKNOWN')
            )
            cursor.execute(sql_insert, values)
            success_msg = f"Đã thêm cầu mới '{name}'."
        else:
            # UPDATE
            # Logic: Chỉ cập nhật search_rate nếu có input mới
            # Giữ nguyên các trường nếu input không có
            new_search_rate = bridge_data.get('search_rate_text', existing_data.get('search_rate_text'))
            new_win_rate = bridge_data.get('win_rate_text', existing_data.get('win_rate_text'))
            
            # Self-Healing: Nếu Win Rate cũ là N/A mà Search Rate mới có dữ liệu -> Update Win Rate luôn
            if (not new_win_rate or new_win_rate == 'N/A') and (new_search_rate and new_search_rate != '0.00%'):
                new_win_rate = new_search_rate

            sql_update = """
            UPDATE ManagedBridges SET 
                pos1_idx=?, pos2_idx=?, is_enabled=?, win_rate_text=?, 
                max_lose_streak_k2n=?, recent_win_count_10=?, description=?,
                search_rate_text=?, search_period=?, type=?
            WHERE name=?
            """
            values_update = (
                bridge_data.get('pos1_idx', existing_data.get('pos1_idx')),
                bridge_data.get('pos2_idx', existing_data.get('pos2_idx')),
                bridge_data.get('is_enabled', existing_data.get('is_enabled')),
                new_win_rate,
                bridge_data.get('max_lose_streak', existing_data.get('max_lose_streak_k2n')),
                bridge_data.get('recent_win_count_10', existing_data.get('recent_win_count_10')),
                bridge_data.get('description', existing_data.get('description')),
                new_search_rate,
                bridge_data.get('search_period', existing_data.get('search_period')),
                bridge_data.get('type', existing_data.get('type')),
                name
            )
            cursor.execute(sql_update, values_update)
            success_msg = f"Đã CẬP NHẬT cầu '{name}'."

        conn.commit()
        return True, success_msg

    except Exception as e:
        return False, f"Lỗi upsert_managed_bridge: {e}"
    finally:
        if conn: conn.close()

def update_bridge_k2n_cache_batch(cache_data_list, db_name=DB_NAME):
    """
    [FIXED V8.5] Cập nhật Cache K2N.
    FEATURE: Tự động "vá" (Self-Heal) win_rate_text nếu nó đang là N/A.
    """
    updated_count = 0
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # 1. Update chuẩn: Search Rate, Streak, Pred...
        sql_update_standard = """
        UPDATE ManagedBridges
        SET search_rate_text = ?, current_streak = ?, next_prediction_stl = ?, max_lose_streak_k2n = ?
        WHERE name = ?
        """
        
        # 2. Update Self-Healing: Copy search_rate vào win_rate nếu win_rate đang N/A
        sql_update_healing = """
        UPDATE ManagedBridges
        SET win_rate_text = search_rate_text
        WHERE name = ? AND (win_rate_text IS NULL OR win_rate_text = 'N/A' OR win_rate_text = '')
        """
        
        cache_data_fixed = []
        names_to_heal = []
        
        for row in cache_data_list:
            # row: (rate, streak, pred, max_lose, recent_win, name) -> từ backtester_core
            # Nhưng hàm gọi truyền vào list tuple: (rate, streak, pred, max_lose, name)
            if len(row) >= 5:
                cache_data_fixed.append((row[0], row[1], row[2], row[3], row[4])) # Dùng index 4 cho name nếu len=5
                names_to_heal.append((row[4],)) # Tuple cho executemany
            elif len(row) == 6: # Format đầy đủ từ backtester
                cache_data_fixed.append((row[0], row[1], row[2], row[3], row[5])) # Dùng index 5 cho name
                names_to_heal.append((row[5],))

        # Thực thi Update chuẩn
        cursor.executemany(sql_update_standard, cache_data_fixed)
        updated_count = cursor.rowcount
        
        # Thực thi Self-Healing
        cursor.executemany(sql_update_healing, names_to_heal)
        healed_count = cursor.rowcount
        
        conn.commit()
        return True, f"Đã cập nhật K2N cho {updated_count} cầu. (Tự vá lỗi N/A cho {healed_count} cầu)"
    except Exception as e:
        return False, f"Lỗi SQL cache K2N: {e}"
    finally:
        if conn: conn.close()

def update_bridge_win_rate_batch(rate_data_list, db_name=DB_NAME):
    """
    Cập nhật K1N (Thực tế).
    """
    updated_count = 0
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        sql_update = "UPDATE ManagedBridges SET win_rate_text = ?, is_enabled = 1 WHERE name = ?"
        cursor.executemany(sql_update, rate_data_list)
        updated_count = cursor.rowcount
        conn.commit()
        return True, f"Đã cập nhật Tỷ Lệ N1 cho {updated_count} cầu."
    except Exception as e:
        return False, f"Lỗi SQL cập nhật Tỷ Lệ N1: {e}"
    finally:
        if conn: conn.close()

def update_bridge_recent_win_count_batch(recent_win_data_list, db_name=DB_NAME):
    updated_count = 0
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        sql_update = "UPDATE ManagedBridges SET recent_win_count_10 = ? WHERE name = ?"
        cursor.executemany(sql_update, recent_win_data_list)
        updated_count = cursor.rowcount
        conn.commit()
        return True, f"Đã cập nhật Phong Độ 10 Kỳ cho {updated_count} cầu."
    except Exception as e:
        return False, f"Lỗi SQL cập nhật Phong Độ 10 Kỳ: {e}"
    finally:
        if conn: conn.close()