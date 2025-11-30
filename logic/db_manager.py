# Tên file: git1/logic/db_manager.py
#
# (PHIÊN BẢN V7.9 - FIX PATH DB TUYỆT ĐỐI & UPDATE V78 SCHEMA)
#
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

PRIZE_TO_COL_MAP = {
    "Đặc Biệt": "Col_B_GDB",
    "Nhất": "Col_C_G1",
    "Nhì": "Col_D_G2",
    "Ba": "Col_E_G3",
    "Bốn": "Col_F_G4",
    "Năm": "Col_G_G5",
    "Sáu": "Col_H_G6",
    "Bảy": "Col_I_G7",
}

try:
    from .bridges.bridges_v16 import get_index_from_name_V16
except ImportError:
    try:
        from logic.bridges.bridges_v16 import get_index_from_name_V16
    except ImportError:
        def get_index_from_name_V16(name):
            return None


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

    # Bảng 3: ManagedBridges (Update V78)
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
        search_period INTEGER DEFAULT 0
    )"""
    )

    # Cập nhật cấu trúc bảng nếu thiếu cột (Migration)
    try:
        cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN max_lose_streak_k2n INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass

    # [MỚI - V78] Thêm cột Phong Độ (Win trong 10 kỳ) cho Cầu Đề
    try:
        cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN recent_win_count_10 INTEGER DEFAULT 0")
        print(">>> [DB] Đã thêm cột 'recent_win_count_10' (V78).")
    except sqlite3.OperationalError: pass
    
    # [MỚI - PHASE 4] Thêm cột is_pinned (Ghim cầu) để bảo vệ cầu quan trọng
    try:
        cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN is_pinned INTEGER DEFAULT 0")
        print(">>> [DB] Đã thêm cột 'is_pinned' (Phase 4 - Pinning).")
    except sqlite3.OperationalError: pass

    # ⚡ THÊM LOGIC CỘT MỚI CHO SCHEMA EVOLUTION (Tỷ lệ tốt nhất từng tìm thấy)
    try:
        cursor.execute("SELECT search_rate_text FROM ManagedBridges LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN search_rate_text TEXT DEFAULT '0.00%'")
        print(">>> [DB] Đã thêm cột 'search_rate_text' (Tỷ lệ tốt nhất từng tìm thấy).")

    try:
        cursor.execute("SELECT search_period FROM ManagedBridges LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN search_period INTEGER DEFAULT 0")
        print(">>> [DB] Đã thêm cột 'search_period' (Số kỳ cho tỷ lệ tốt nhất).")

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_ky ON results_A_I(ky)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dulieu_masoky ON DuLieu_AI(MaSoKy)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bridges_enabled ON ManagedBridges(is_enabled)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bridges_enabled_rate ON ManagedBridges(is_enabled, win_rate_text)")

    conn.commit()
    return conn, cursor


# ===================================================================================
# II. HÀM TRUY VẤN
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
# III. HÀM QUẢN LÝ CẦU (CRUD)
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
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        pos1_idx, pos2_idx = None, None
        if "+" in bridge_name:
            try:
                p1, p2 = bridge_name.split("+")
                pos1_idx = get_index_from_name_V16(p1.strip())
                pos2_idx = get_index_from_name_V16(p2.strip())
            except: pass
        elif "Tổng(" in bridge_name or "Hiệu(" in bridge_name:
            pos1_idx, pos2_idx = -1, -1

        cursor.execute(
            "INSERT INTO ManagedBridges (name, description, pos1_idx, pos2_idx) VALUES (?, ?, ?, ?)",
            (bridge_name, description, pos1_idx, pos2_idx),
        )
        conn.commit()
        return True, f"Đã thêm cầu '{bridge_name}'."
    except sqlite3.IntegrityError:
        return False, f"Lỗi: Cầu '{bridge_name}' đã tồn tại."
    except Exception as e:
        return False, f"Lỗi add_managed_bridge: {e}"
    finally:
        if conn: conn.close()


def update_managed_bridge(bridge_id, description=None, is_enabled=None, db_name=DB_NAME, updates=None):
    """
    Cập nhật cầu trong database với hỗ trợ cập nhật động.
    
    Args:
        bridge_id: ID của cầu cần cập nhật
        description: Mô tả (tùy chọn, có thể trong updates)
        is_enabled: Trạng thái bật/tắt (tùy chọn, có thể trong updates)
        db_name: Đường dẫn database
        updates: Dictionary chứa các trường cần cập nhật (ưu tiên hơn các tham số riêng lẻ)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Ưu tiên updates dictionary nếu có, nếu không dùng các tham số riêng lẻ
        if updates is None:
            updates = {}
        if description is not None:
            updates['description'] = description
        if is_enabled is not None:
            updates['is_enabled'] = 1 if is_enabled else 0
        
        set_parts = []
        values = []

        allowed_fields = [
            'description', 'is_enabled', 'win_rate_text', 'max_lose_streak', 'recent_win_count_10',
            'pos1_idx', 'pos2_idx', 'search_rate_text', 'search_period'  # << THÊM CỘT MỚI >>
        ]
        
        # Map max_lose_streak to database column name max_lose_streak_k2n
        field_mapping = {
            'max_lose_streak': 'max_lose_streak_k2n'
        }
        
        for field in allowed_fields:
            if field in updates:
                # Use mapped field name if exists, otherwise use original field name
                db_field = field_mapping.get(field, field)
                set_parts.append(f"{db_field}=?")
                values.append(updates[field])

        if not set_parts:
            return True, "Không có trường nào để cập nhật."
        
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
    """
    Đảo ngược trạng thái ghim của cầu (Phase 4 - Pinning).
    
    Args:
        bridge_name: Tên cầu
        db_name: Đường dẫn database
    
    Returns:
        tuple: (success: bool, message: str, new_pin_state: bool or None)
    """
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Lấy trạng thái hiện tại
        cursor.execute("SELECT is_pinned FROM ManagedBridges WHERE name = ?", (bridge_name,))
        row = cursor.fetchone()
        
        if not row:
            return False, f"Không tìm thấy cầu '{bridge_name}' trong database.", None
        
        current_pin = row[0] if row[0] is not None else 0
        new_pin = 1 if current_pin == 0 else 0
        
        # Cập nhật trạng thái ghim
        cursor.execute(
            "UPDATE ManagedBridges SET is_pinned = ? WHERE name = ?",
            (new_pin, bridge_name)
        )
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
    
    Args:
        bridge_name: Tên cầu (bắt buộc)
        description: Mô tả (tùy chọn, có thể trong bridge_data)
        win_rate: Tỷ lệ thắng (tùy chọn, có thể trong bridge_data)
        db_name: Đường dẫn database
        pos1_idx, pos2_idx: Chỉ số vị trí (tùy chọn, có thể trong bridge_data)
        bridge_data: Dictionary chứa dữ liệu cầu (ưu tiên hơn các tham số riêng lẻ)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Ưu tiên bridge_data nếu có, nếu không dùng các tham số riêng lẻ
        if bridge_data is None:
            bridge_data = {}
        if description is not None:
            bridge_data['description'] = description
        if win_rate is not None:
            bridge_data['win_rate_text'] = win_rate
        if pos1_idx is not None:
            bridge_data['pos1_idx'] = pos1_idx
        if pos2_idx is not None:
            bridge_data['pos2_idx'] = pos2_idx

        # Xác định pos1_idx, pos2_idx nếu chưa có
        if bridge_data.get('pos1_idx') is None or bridge_data.get('pos2_idx') is None:
            if "+" in bridge_name:
                try:
                    p1, p2 = bridge_name.split("+")
                    bridge_data['pos1_idx'] = get_index_from_name_V16(p1.strip())
                    bridge_data['pos2_idx'] = get_index_from_name_V16(p2.strip())
                except: 
                    bridge_data['pos1_idx'] = None
                    bridge_data['pos2_idx'] = None
            elif "Tổng(" in bridge_name or "Hiệu(" in bridge_name:
                bridge_data['pos1_idx'] = -1
                bridge_data['pos2_idx'] = -1

        # Lấy các giá trị từ bridge_data
        name = bridge_name
        description = bridge_data.get('description', '')
        win_rate_text = bridge_data.get('win_rate_text', 'N/A')
        is_enabled = bridge_data.get('is_enabled', 1)
        # Hỗ trợ cả max_lose_streak và max_lose_streak_k2n
        max_lose_streak = bridge_data.get('max_lose_streak', bridge_data.get('max_lose_streak_k2n', 0))
        recent_win_count_10 = bridge_data.get('recent_win_count_10', 0)

        # Kiểm tra xem cầu đã tồn tại chưa
        cursor.execute("SELECT * FROM ManagedBridges WHERE name = ?", (name,))
        existing_row = cursor.fetchone()
        
        if existing_row:
            # Lấy tên cột để tạo dictionary
            cursor.execute("PRAGMA table_info(ManagedBridges)")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]
            
            existing_bridge = dict(zip(column_names, existing_row))
        else:
            existing_bridge = None

        if not existing_bridge:
            # Nếu chưa tồn tại, INSERT
            sql_insert = """
            INSERT INTO ManagedBridges (
                name, pos1_idx, pos2_idx, is_enabled, win_rate_text, max_lose_streak_k2n, recent_win_count_10, 
                search_rate_text, search_period, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            values = (
                name,
                bridge_data.get('pos1_idx'),
                bridge_data.get('pos2_idx'),
                is_enabled,
                win_rate_text,
                max_lose_streak,
                recent_win_count_10,
                # Ghi giá trị mới vào cột search_rate/search_period
                bridge_data.get('search_rate_text', win_rate_text), # Khi INSERT, gán search_rate = win_rate ban đầu
                bridge_data.get('search_period', 0),
                description
            )
            cursor.execute(sql_insert, values)
            bridge_id = cursor.lastrowid
            success_msg = f"Đã thêm cầu mới '{name}' (ID: {bridge_id})."
        else:
            # Nếu đã tồn tại, UPDATE
            
            # ⚡ LÔGIC KHẮC PHỤC LỖI GHI ĐÈ:
            # Lấy giá trị hiện tại của search_rate/search_period để KHÔNG bị mất bởi update chuẩn hóa.
            current_search_rate = existing_bridge.get('search_rate_text', '0.00%')
            current_search_period = existing_bridge.get('search_period', 0)
            
            # Giá trị mới từ input: Ưu tiên giá trị mới từ input nếu có, nếu không thì giữ lại giá trị cũ.
            new_search_rate = bridge_data.get('search_rate_text', current_search_rate)
            new_search_period = bridge_data.get('search_period', current_search_period)

            # Lôgic UPDATE
            sql_update = """
            UPDATE ManagedBridges SET 
                pos1_idx=?, 
                pos2_idx=?, 
                is_enabled=?, 
                win_rate_text=?, 
                max_lose_streak_k2n=?, 
                recent_win_count_10=?,
                description=?,
                search_rate_text=?,  -- << CHỈ GHI ĐÈ NẾU CÓ TRONG INPUT DÒ TÌM >>
                search_period=?      -- << CHỈ GHI ĐÈ NẾU CÓ TRONG INPUT DÒ TÌM >>
            WHERE name=?
            """
            values_update = (
                bridge_data.get('pos1_idx'),
                bridge_data.get('pos2_idx'),
                is_enabled,
                win_rate_text,
                max_lose_streak,
                recent_win_count_10,
                description,
                new_search_rate,  # Giá trị đã được bảo vệ/cập nhật
                new_search_period,
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
    Cập nhật Cache K2N cho Cầu Đã Lưu.
    LƯU Ý: KHÔNG cập nhật recent_win_count_10 ở đây - trường này chỉ được cập nhật từ K1N.
    """
    updated_count = 0
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        # [FIX] Loại bỏ recent_win_count_10 khỏi cập nhật K2N - chỉ cập nhật từ K1N
        sql_update = """
        UPDATE ManagedBridges
        SET win_rate_text = ?, current_streak = ?, next_prediction_stl = ?, max_lose_streak_k2n = ?
        WHERE name = ?
        """
        # Chỉ lấy 5 phần tử đầu (bỏ recent_win_count_10 ở vị trí thứ 5)
        cache_data_list_fixed = [(row[0], row[1], row[2], row[3], row[5]) for row in cache_data_list]
        cursor.executemany(sql_update, cache_data_list_fixed)
        updated_count = cursor.rowcount
        conn.commit()
        return True, f"Đã cập nhật cache K2N cho {updated_count} cầu."
    except Exception as e:
        return False, f"Lỗi SQL cache K2N: {e}"
    finally:
        if conn: conn.close()


def update_bridge_win_rate_batch(rate_data_list, db_name=DB_NAME):
    updated_count = 0
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        sql_update = "UPDATE ManagedBridges SET win_rate_text = ?, is_enabled = 1 WHERE name = ?"
        cursor.executemany(sql_update, rate_data_list)
        updated_count = cursor.rowcount
        conn.commit()
        return True, f"Đã cập nhật Tỷ Lệ N1 cho {updated_count} cầu (BN)."
    except Exception as e:
        return False, f"Lỗi SQL cập nhật Tỷ Lệ N1: {e}"
    finally:
        if conn: conn.close()


def update_bridge_recent_win_count_batch(recent_win_data_list, db_name=DB_NAME):
    """Cập nhật recent_win_count_10 cho Cầu Đã Lưu từ kết quả K1N"""
    updated_count = 0
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        sql_update = "UPDATE ManagedBridges SET recent_win_count_10 = ? WHERE name = ?"
        cursor.executemany(sql_update, recent_win_data_list)
        updated_count = cursor.rowcount
        conn.commit()
        return True, f"Đã cập nhật Phong Độ 10 Kỳ (K1N) cho {updated_count} cầu."
    except Exception as e:
        return False, f"Lỗi SQL cập nhật Phong Độ 10 Kỳ: {e}"
    finally:
        if conn: conn.close()


# ===================================================================================
# IV. LỚP DBManager (Placeholder để khắc phục lỗi Import)
# ===================================================================================

class DBManager:
    """
    Lớp Placeholder để khắc phục lỗi Import.
    
    Các Service sẽ gọi các hàm cấp module của db_manager thông qua lớp này.
    Tất cả các hàm cấp module (setup_database, update_managed_bridge, v.v.) 
    vẫn giữ nguyên để đảm bảo tương thích ngược.
    
    Lớp này có thể được mở rộng trong tương lai để cung cấp interface hướng đối tượng
    cho các thao tác database, nhưng hiện tại chỉ là placeholder.
    """
    pass