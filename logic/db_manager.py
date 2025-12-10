# Tên file: logic/db_manager.py
# (PHIÊN BẢN V8.5 - FIX CRITICAL: CACHE WRITE & SELF-HEALING N/A)

import sqlite3
import os
import time
from typing import List, Dict, Set, Optional, Tuple, Any

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
    # V11.2: K1N-primary detection flow - add rate columns
    columns_to_add = [
        ("max_lose_streak_k2n", "INTEGER DEFAULT 0"),
        ("recent_win_count_10", "INTEGER DEFAULT 0"),
        ("is_pinned", "INTEGER DEFAULT 0"),
        ("search_rate_text", "TEXT DEFAULT '0.00%'"),
        ("search_period", "INTEGER DEFAULT 0"),
        ("type", "TEXT DEFAULT 'UNKNOWN'"),
        # K1N/K2N rate columns (V11.2)
        ("k1n_rate_lo", "REAL DEFAULT 0.0"),
        ("k1n_rate_de", "REAL DEFAULT 0.0"),
        ("k2n_rate_lo", "REAL DEFAULT 0.0"),
        ("k2n_rate_de", "REAL DEFAULT 0.0"),
        ("is_pending", "INTEGER DEFAULT 1"),
        ("imported_at", "TEXT DEFAULT (datetime('now','localtime'))")
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


def delete_managed_bridges(ids_list, db_name=DB_NAME):
    """
    Xóa nhiều cầu cùng lúc theo danh sách IDs.
    V11.1: Bulk delete operation with logging.
    
    Args:
        ids_list: List of bridge IDs to delete
        db_name: Database name
    
    Returns:
        Tuple (success: bool, message: str, deleted_count: int)
    """
    conn = None
    try:
        if not ids_list:
            return True, "Không có cầu nào để xóa.", 0
        
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Build placeholders for IN clause
        placeholders = ','.join('?' * len(ids_list))
        sql_delete = f"DELETE FROM ManagedBridges WHERE id IN ({placeholders})"
        
        cursor.execute(sql_delete, ids_list)
        deleted_count = cursor.rowcount
        conn.commit()
        
        return True, f"Đã xóa {deleted_count} cầu thành công.", deleted_count
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"Lỗi delete_managed_bridges: {e}", 0
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

def _upsert_managed_bridge_impl(conn, bridge_dict, db_name=DB_NAME):
    """
    Implementation của upsert_managed_bridge.
    Internal function - nên gọi qua wrapper upsert_managed_bridge().
    """
    cursor = conn.cursor()
    
    # Normalize key names
    name = bridge_dict.get('name') or bridge_dict.get('ten') or bridge_dict.get('bridge_name')
    if not name:
        raise ValueError("Bridge name is required")
    
    description = bridge_dict.get('description') or bridge_dict.get('mo_ta', '')
    win_rate_text = bridge_dict.get('win_rate_text') or bridge_dict.get('win_rate') or bridge_dict.get('ty_le', 'N/A')
    pos1_idx = bridge_dict.get('pos1_idx')
    pos2_idx = bridge_dict.get('pos2_idx')
    bridge_type = bridge_dict.get('type') or bridge_dict.get('loai', 'UNKNOWN')
    is_enabled = bridge_dict.get('is_enabled', 1)
    search_rate_text = bridge_dict.get('search_rate_text', '0.00%')
    search_period = bridge_dict.get('search_period', 0)
    max_lose_streak = bridge_dict.get('max_lose_streak', 0)
    recent_win_count_10 = bridge_dict.get('recent_win_count_10', 0)
    
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
        if win_rate_text == 'N/A' and search_rate_text != '0.00%':
            win_rate_text = search_rate_text

        sql_insert = """
        INSERT INTO ManagedBridges (
            name, pos1_idx, pos2_idx, is_enabled, win_rate_text, max_lose_streak_k2n, recent_win_count_10, 
            search_rate_text, search_period, description, type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            name, pos1_idx, pos2_idx, is_enabled,
            win_rate_text, max_lose_streak, recent_win_count_10,
            search_rate_text, search_period, description, bridge_type
        )
        cursor.execute(sql_insert, values)
        success_msg = f"Đã thêm cầu mới '{name}'."
    else:
        # UPDATE
        # Logic: Chỉ cập nhật search_rate nếu có input mới
        # Giữ nguyên các trường nếu input không có
        new_search_rate = search_rate_text if search_rate_text != '0.00%' else existing_data.get('search_rate_text')
        new_win_rate = win_rate_text if win_rate_text != 'N/A' else existing_data.get('win_rate_text')
        
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
            pos1_idx if pos1_idx is not None else existing_data.get('pos1_idx'),
            pos2_idx if pos2_idx is not None else existing_data.get('pos2_idx'),
            is_enabled,
            new_win_rate,
            max_lose_streak if max_lose_streak > 0 else existing_data.get('max_lose_streak_k2n'),
            recent_win_count_10 if recent_win_count_10 > 0 else existing_data.get('recent_win_count_10'),
            description,
            new_search_rate,
            search_period if search_period > 0 else existing_data.get('search_period'),
            bridge_type,
            name
        )
        cursor.execute(sql_update, values_update)
        success_msg = f"Đã CẬP NHẬT cầu '{name}'."

    return True, success_msg


def upsert_managed_bridge(bridge_name=None, description=None, win_rate=None, db_name=DB_NAME, pos1_idx=None, pos2_idx=None, bridge_data=None, **kwargs):
    """
    Chèn hoặc cập nhật cầu trong database.
    (V8.5: Logic bảo vệ Search Rate và Win Rate)
    (V11.1: Shim wrapper hỗ trợ dict hoặc kwargs)
    
    Accepts:
      - upsert_managed_bridge(name="...", description="...", ...)  # kwargs
      - upsert_managed_bridge(bridge_dict={"name": "...", ...})    # dict via kwargs
      - upsert_managed_bridge("name", "desc", ...)                  # positional
    """
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        
        # Determine if we're using dict or individual params
        if bridge_data is not None:
            # Legacy mode: bridge_data dict provided
            bridge_dict = bridge_data.copy()
            if bridge_name: bridge_dict['name'] = bridge_name
            if description: bridge_dict['description'] = description
            if win_rate: bridge_dict['win_rate_text'] = win_rate
            if pos1_idx is not None: bridge_dict['pos1_idx'] = pos1_idx
            if pos2_idx is not None: bridge_dict['pos2_idx'] = pos2_idx
        elif kwargs.get('bridge_dict'):
            # New mode: bridge_dict passed as kwarg
            bridge_dict = kwargs['bridge_dict'].copy()
        elif bridge_name or kwargs:
            # Build dict from individual params
            bridge_dict = kwargs.copy()
            if bridge_name: bridge_dict['name'] = bridge_name
            if description: bridge_dict['description'] = description
            if win_rate: bridge_dict['win_rate_text'] = win_rate
            if pos1_idx is not None: bridge_dict['pos1_idx'] = pos1_idx
            if pos2_idx is not None: bridge_dict['pos2_idx'] = pos2_idx
        else:
            raise ValueError("No bridge data provided")
        
        success, msg = _upsert_managed_bridge_impl(conn, bridge_dict, db_name)
        conn.commit()
        return success, msg

    except Exception as e:
        if conn:
            conn.rollback()
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


# ===================================================================================
# IV. K1N-PRIMARY BULK IMPORT APIs (V11.2)
# ===================================================================================

def get_all_managed_bridge_names(db_name: str = DB_NAME) -> Set[str]:
    """
    Get all managed bridge names from database.
    
    Returns normalized bridge names for efficient duplicate checking.
    Used by scanner to exclude existing bridges.
    
    Args:
        db_name: Database file path
        
    Returns:
        Set of normalized bridge names (lowercase, no special chars)
        
    Example:
        >>> names = get_all_managed_bridge_names()
        >>> 'cau-de-01' in names  # Fast O(1) lookup
        True
    """
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM ManagedBridges")
        rows = cursor.fetchall()
        
        # Import normalize function
        try:
            from logic.common_utils import normalize_bridge_name
        except ImportError:
            # Fallback: simple normalization
            def normalize_bridge_name(name):
                return str(name).strip().lower()
        
        return {normalize_bridge_name(row[0]) for row in rows if row[0]}
    except Exception as e:
        print(f"[ERROR] get_all_managed_bridge_names: {e}")
        return set()
    finally:
        if conn:
            conn.close()


def bulk_upsert_managed_bridges(
    bridges: List[Dict[str, Any]], 
    db_name: str = DB_NAME,
    transactional: bool = True
) -> Dict[str, int]:
    """
    Bulk upsert managed bridges with atomic transaction support.
    
    Performs efficient INSERT/UPDATE operations using executemany.
    Includes retry logic for sqlite3.OperationalError (database locked).
    
    Args:
        bridges: List of bridge dictionaries with keys:
            - name (required): Bridge name
            - description: Bridge description
            - type: Bridge type (LO_*, DE_*)
            - k1n_rate_lo: K1N rate for LO
            - k1n_rate_de: K1N rate for DE
            - k2n_rate_lo: K2N rate for LO
            - k2n_rate_de: K2N rate for DE
            - is_pending: Whether bridge is pending approval (0 or 1)
            - is_enabled: Whether bridge is enabled (0 or 1)
            - pos1_idx, pos2_idx: Position indices
            - Other optional fields...
            
        db_name: Database file path
        transactional: If True, all operations in single transaction (rollback on error)
        
    Returns:
        Dict with keys: 'added', 'updated', 'skipped', 'errors'
        
    Example:
        >>> bridges = [
        ...     {'name': 'Bridge-01', 'type': 'DE_DYN', 'k1n_rate_de': 95.5},
        ...     {'name': 'Bridge-02', 'type': 'LO_V16', 'k1n_rate_lo': 87.3}
        ... ]
        >>> result = bulk_upsert_managed_bridges(bridges)
        >>> print(f"Added: {result['added']}, Updated: {result['updated']}")
    """
    stats = {'added': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
    
    if not bridges:
        return stats
    
    conn = None
    max_retries = 3
    retry_delay = 0.1  # Start with 100ms
    
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(db_name, timeout=10.0)
            cursor = conn.cursor()
            
            # Get existing bridges for duplicate check
            cursor.execute("SELECT name FROM ManagedBridges")
            existing_names = {row[0].strip().lower() for row in cursor.fetchall()}
            
            # Prepare batch operations
            to_insert = []
            to_update = []
            
            for bridge in bridges:
                name = bridge.get('name')
                if not name:
                    stats['skipped'] += 1
                    continue
                
                # Check if exists
                is_existing = name.strip().lower() in existing_names
                
                # Prepare values (with defaults)
                description = bridge.get('description', '')
                bridge_type = bridge.get('type', 'UNKNOWN')
                k1n_rate_lo = bridge.get('k1n_rate_lo', 0.0)
                k1n_rate_de = bridge.get('k1n_rate_de', 0.0)
                k2n_rate_lo = bridge.get('k2n_rate_lo', 0.0)
                k2n_rate_de = bridge.get('k2n_rate_de', 0.0)
                is_pending = bridge.get('is_pending', 1)
                is_enabled = bridge.get('is_enabled', 0)  # Default disabled for new bridges
                pos1_idx = bridge.get('pos1_idx')
                pos2_idx = bridge.get('pos2_idx')
                win_rate_text = bridge.get('win_rate_text', 'N/A')
                search_rate_text = bridge.get('search_rate_text', '0.00%')
                current_streak = bridge.get('current_streak', 0)
                next_prediction_stl = bridge.get('next_prediction_stl', 'N/A')
                
                if is_existing:
                    # UPDATE
                    to_update.append((
                        description, bridge_type, k1n_rate_lo, k1n_rate_de,
                        k2n_rate_lo, k2n_rate_de, is_pending, is_enabled,
                        pos1_idx, pos2_idx, win_rate_text, search_rate_text,
                        current_streak, next_prediction_stl,
                        name  # WHERE clause
                    ))
                else:
                    # INSERT
                    to_insert.append((
                        name, description, bridge_type, k1n_rate_lo, k1n_rate_de,
                        k2n_rate_lo, k2n_rate_de, is_pending, is_enabled,
                        pos1_idx, pos2_idx, win_rate_text, search_rate_text,
                        current_streak, next_prediction_stl
                    ))
            
            # Execute batch INSERT
            if to_insert:
                sql_insert = """
                INSERT INTO ManagedBridges (
                    name, description, type, k1n_rate_lo, k1n_rate_de,
                    k2n_rate_lo, k2n_rate_de, is_pending, is_enabled,
                    pos1_idx, pos2_idx, win_rate_text, search_rate_text,
                    current_streak, next_prediction_stl
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.executemany(sql_insert, to_insert)
                # Note: cursor.rowcount with executemany is unreliable in SQLite
                # Use actual count from prepared list
                stats['added'] = len(to_insert)
            
            # Execute batch UPDATE
            if to_update:
                sql_update = """
                UPDATE ManagedBridges SET
                    description=?, type=?, k1n_rate_lo=?, k1n_rate_de=?,
                    k2n_rate_lo=?, k2n_rate_de=?, is_pending=?, is_enabled=?,
                    pos1_idx=?, pos2_idx=?, win_rate_text=?, search_rate_text=?,
                    current_streak=?, next_prediction_stl=?
                WHERE name=?
                """
                cursor.executemany(sql_update, to_update)
                # Note: cursor.rowcount with executemany is unreliable in SQLite
                # Use actual count from prepared list
                stats['updated'] = len(to_update)
            
            # Commit transaction
            if transactional:
                conn.commit()
            
            print(f"[INFO] bulk_upsert: Added {stats['added']}, Updated {stats['updated']}, Skipped {stats['skipped']}")
            return stats
            
        except sqlite3.OperationalError as e:
            # Database locked - retry with exponential backoff
            if attempt < max_retries - 1:
                print(f"[WARN] Database locked, retrying in {retry_delay}s... (attempt {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
                continue
            else:
                print(f"[ERROR] bulk_upsert failed after {max_retries} attempts: {e}")
                stats['errors'] = len(bridges) - stats['added'] - stats['updated'] - stats['skipped']
                if conn and transactional:
                    conn.rollback()
                return stats
                
        except Exception as e:
            print(f"[ERROR] bulk_upsert_managed_bridges: {e}")
            stats['errors'] = len(bridges) - stats['added'] - stats['updated'] - stats['skipped']
            if conn and transactional:
                conn.rollback()
            return stats
        finally:
            if conn:
                conn.close()
    
    return stats


def update_managed_bridges_batch(
    updates: List[Dict[str, Any]],
    db_name: str = DB_NAME
) -> Dict[str, int]:
    """
    Update multiple managed bridges in a single transaction.
    
    Args:
        updates: List of update dictionaries with 'name' (required) and fields to update
        db_name: Database file path
        
    Returns:
        Dict with keys: 'updated', 'skipped', 'errors'
        
    Example:
        >>> updates = [
        ...     {'name': 'Bridge-01', 'is_enabled': 1, 'k1n_rate_lo': 92.0},
        ...     {'name': 'Bridge-02', 'is_pending': 0}
        ... ]
        >>> result = update_managed_bridges_batch(updates)
    """
    stats = {'updated': 0, 'skipped': 0, 'errors': 0}
    
    if not updates:
        return stats
    
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        allowed_fields = [
            'description', 'type', 'k1n_rate_lo', 'k1n_rate_de',
            'k2n_rate_lo', 'k2n_rate_de', 'is_pending', 'is_enabled',
            'pos1_idx', 'pos2_idx', 'win_rate_text', 'search_rate_text',
            'current_streak', 'next_prediction_stl', 'max_lose_streak_k2n',
            'recent_win_count_10', 'is_pinned'
        ]
        
        for update_dict in updates:
            name = update_dict.get('name')
            if not name:
                stats['skipped'] += 1
                continue
            
            # Build dynamic UPDATE query
            set_parts = []
            values = []
            
            for field in allowed_fields:
                if field in update_dict:
                    set_parts.append(f"{field}=?")
                    values.append(update_dict[field])
            
            if not set_parts:
                stats['skipped'] += 1
                continue
            
            sql_update = f"UPDATE ManagedBridges SET {', '.join(set_parts)} WHERE name=?"
            values.append(name)
            
            cursor.execute(sql_update, values)
            if cursor.rowcount > 0:
                stats['updated'] += 1
            else:
                stats['skipped'] += 1
        
        conn.commit()
        print(f"[INFO] update_batch: Updated {stats['updated']}, Skipped {stats['skipped']}")
        return stats
        
    except Exception as e:
        print(f"[ERROR] update_managed_bridges_batch: {e}")
        stats['errors'] = len(updates) - stats['updated'] - stats['skipped']
        if conn:
            conn.rollback()
        return stats
    finally:
        if conn:
            conn.close()


def delete_managed_bridges_batch(
    names: List[str],
    db_name: str = DB_NAME
) -> Dict[str, int]:
    """
    Delete multiple managed bridges by names in a single transaction.
    
    Args:
        names: List of bridge names to delete
        db_name: Database file path
        
    Returns:
        Dict with keys: 'deleted', 'errors'
        
    Example:
        >>> result = delete_managed_bridges_batch(['Bridge-01', 'Bridge-02'])
        >>> print(f"Deleted: {result['deleted']}")
    """
    stats = {'deleted': 0, 'errors': 0}
    
    if not names:
        return stats
    
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Use IN clause for efficient batch delete
        placeholders = ','.join('?' * len(names))
        sql_delete = f"DELETE FROM ManagedBridges WHERE name IN ({placeholders})"
        
        cursor.execute(sql_delete, names)
        stats['deleted'] = cursor.rowcount
        
        conn.commit()
        print(f"[INFO] delete_batch: Deleted {stats['deleted']} bridges")
        return stats
        
    except Exception as e:
        print(f"[ERROR] delete_managed_bridges_batch: {e}")
        stats['errors'] = len(names)
        if conn:
            conn.rollback()
        return stats
    finally:
        if conn:
            conn.close()