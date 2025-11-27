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
        recent_win_count_10 INTEGER DEFAULT 0
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


def update_managed_bridge(bridge_id, description, is_enabled, db_name=DB_NAME):
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ManagedBridges SET description = ?, is_enabled = ? WHERE id = ?",
            (description, 1 if is_enabled else 0, bridge_id),
        )
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


def upsert_managed_bridge(bridge_name, description, win_rate, db_name=DB_NAME, pos1_idx=None, pos2_idx=None):
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        if pos1_idx is None or pos2_idx is None:
            if "+" in bridge_name:
                try:
                    p1, p2 = bridge_name.split("+")
                    pos1_idx = get_index_from_name_V16(p1.strip())
                    pos2_idx = get_index_from_name_V16(p2.strip())
                except: pos1_idx, pos2_idx = None, None
            elif "Tổng(" in bridge_name or "Hiệu(" in bridge_name:
                pos1_idx, pos2_idx = -1, -1

        cursor.execute(
            """
            UPDATE ManagedBridges
            SET description = ?, win_rate_text = ?, pos1_idx = ?, pos2_idx = ?, is_enabled = 1
            WHERE name = ?
            """,
            (description, win_rate, pos1_idx, pos2_idx, bridge_name),
        )

        if cursor.rowcount == 0:
            cursor.execute(
                """
                INSERT INTO ManagedBridges (name, description, win_rate_text, pos1_idx, pos2_idx, is_enabled)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (bridge_name, description, win_rate, pos1_idx, pos2_idx),
            )
            conn.commit()
            return True, f"Đã THÊM cầu '{bridge_name}'."

        conn.commit()
        return True, f"Đã CẬP NHẬT cầu '{bridge_name}'."

    except Exception as e:
        if conn: conn.close()
        return False, f"Lỗi upsert_managed_bridge: {e}"


def update_bridge_k2n_cache_batch(cache_data_list, db_name=DB_NAME):
    updated_count = 0
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        sql_update = """
        UPDATE ManagedBridges
        SET win_rate_text = ?, current_streak = ?, next_prediction_stl = ?, max_lose_streak_k2n = ?, recent_win_count_10 = ?
        WHERE name = ?
        """
        cursor.executemany(sql_update, cache_data_list)
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