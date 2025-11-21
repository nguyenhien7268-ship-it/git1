# Tên file: git3/logic/db_manager.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - SỬA W291)
#
import sqlite3

# ĐÃ SỬA: Cập nhật đường dẫn DB mới sau khi di chuyển file sang thư mục 'data/'
DB_NAME = "data/xo_so_prizes_all_logic.db"

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

# --- Import từ file .bridges_v16 (sẽ được tạo) ---
# (Chúng ta cần file này để dịch tên cầu khi thêm cầu)
try:
    from .bridges.bridges_v16 import get_index_from_name_V16  # ĐÃ FIX IMPORT RELATIVE
except ImportError:
    # Fallback cho trường hợp chạy độc lập (nếu có)
    try:
        from logic.bridges.bridges_v16 import get_index_from_name_V16
    except ImportError:
        print("LỖI: db_manager.py không thể import get_index_from_name_V16.")

        def get_index_from_name_V16(name):
            return None


# ===================================================================================
# I. HÀM THIẾT LẬP CSDL (V7.0)
# ===================================================================================


def setup_database(db_name=DB_NAME):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # (GIỮ NGUYÊN) Bảng 1: DuLieu_AI (Dữ liệu gốc A:I cho backtest)
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS DuLieu_AI (
        MaSoKy INTEGER PRIMARY KEY,
        Col_A_Ky TEXT,
        Col_B_GDB TEXT, Col_C_G1 TEXT, Col_D_G2 TEXT, Col_E_G3 TEXT,
        Col_F_G4 TEXT, Col_G_G5 TEXT, Col_H_G6 TEXT, Col_I_G7 TEXT
    )"""
    )

    # (GIỮ NGUYÊN) Bảng 2: results_A_I (Dữ liệu đầy đủ 38 cột cho dò cầu)
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

    # (CẬP NHẬT GĐ 4) Bảng 3: ManagedBridges (Thêm cột max_lose_streak_k2n)
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

    # (CẬP NHẬT GĐ 4) Cập nhật cấu trúc bảng nếu thiếu cột max_lose_streak_k2n
    try:
        cursor.execute(
            "ALTER TABLE ManagedBridges ADD COLUMN max_lose_streak_k2n INTEGER DEFAULT 0"
        )
        print("Đã cập nhật bảng ManagedBridges (thêm cột max_lose_streak_k2n).")
    except sqlite3.OperationalError:
        pass  # Cột đã tồn tại

    # (CẬP NHẬT) Cập nhật cấu trúc bảng nếu thiếu cột recent_win_count_10
    try:
        cursor.execute(
            "ALTER TABLE ManagedBridges ADD COLUMN recent_win_count_10 INTEGER DEFAULT 0"
        )
        print("Đã cập nhật bảng ManagedBridges (thêm cột recent_win_count_10).")
    except sqlite3.OperationalError:
        pass  # Cột đã tồn tại

    # (PERFORMANCE OPTIMIZATION) Tạo indexes để tăng tốc queries 10-100x
    print("Đang tạo database indexes...")
    
    # Index cho results_A_I.ky (tra cứu thường xuyên nhất)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_results_ky ON results_A_I(ky)"
    )
    
    # Index cho DuLieu_AI.MaSoKy (cho range queries)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_dulieu_masoky ON DuLieu_AI(MaSoKy)"
    )
    
    # Index cho ManagedBridges.is_enabled (lọc cầu active)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_bridges_enabled ON ManagedBridges(is_enabled)"
    )
    
    # Composite index cho query kết hợp enabled + win_rate
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_bridges_enabled_rate "
        "ON ManagedBridges(is_enabled, win_rate_text)"
    )
    
    print("✅ Database indexes đã được tạo thành công")

    conn.commit()
    return conn, cursor


# ===================================================================================
# II. HÀM TRUY VẤN (BỊ THIẾU Ở V6.0)
# ===================================================================================


def get_results_by_ky(ky_id, db_name=DB_NAME):
    """(BỔ SUNG) Lấy dữ liệu 1 hàng (38 cột) từ results_A_I bằng KỲ."""
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
        if conn:
            conn.close()


def get_all_kys_from_db(db_name=DB_NAME):
    """(BỔ SUNG) Lấy danh sách KỲ (ky) và NGÀY (date) từ CSDL."""
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        # Sắp xếp theo ky SỐ (CAST)
        cursor.execute(
            "SELECT ky, date FROM results_A_I ORDER BY CAST(ky AS INTEGER) DESC"
        )
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        print(f"Lỗi get_all_kys_from_db: {e}")
        return []
    finally:
        if conn:
            conn.close()


def delete_ky_from_db(ky, db_name=DB_NAME):
    """Delete a lottery result by ky (period number)."""
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Delete from both tables
        cursor.execute("DELETE FROM results_A_I WHERE ky = ?", (ky,))
        cursor.execute("DELETE FROM DuLieu_AI WHERE Col_A_Ky = ?", (ky,))
        
        conn.commit()
        deleted_count = cursor.rowcount
        return True, f"Đã xóa kỳ {ky} ({deleted_count} bản ghi)"
    except Exception as e:
        print(f"Lỗi delete_ky_from_db: {e}")
        return False, f"Lỗi khi xóa: {e}"
    finally:
        if conn:
            conn.close()


# ===================================================================================
# III. HÀM QUẢN LÝ CẦU (CRUD) (BỊ THIẾU Ở V6.0)
# ===================================================================================


def delete_all_managed_bridges(conn):
    """(BỔ SUNG) Xóa sạch bảng ManagedBridges khi nạp lại file."""
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ManagedBridges")
        # conn.commit() # Bỏ commit, để hàm cha (parse) commit
        print("Đã xóa sạch Cầu Đã Lưu (ManagedBridges).")
        return True
    except Exception as e:
        print(f"Lỗi delete_all_managed_bridges: {e}")
        return False


def add_managed_bridge(bridge_name, description, db_name=DB_NAME):
    """(BỔ SUNG) Thêm một cầu mới vào CSDL."""
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Dịch tên cầu V17 (GDB[0]+G1[1]) sang index (0, 7)
        pos1_idx, pos2_idx = None, None
        if "+" in bridge_name:
            try:
                pos1_name, pos2_name = bridge_name.split("+")
                pos1_idx = get_index_from_name_V16(pos1_name.strip())
                pos2_idx = get_index_from_name_V16(pos2_name.strip())
            except Exception as e_parse:
                print(f"Lỗi dịch tên cầu V17: {e_parse}")

        # Cầu Bạc Nhớ (Tổng/Hiệu)
        elif "Tổng(" in bridge_name or "Hiệu(" in bridge_name:
            pos1_idx, pos2_idx = -1, -1  # Đánh dấu là cầu Bạc Nhớ

        cursor.execute(
            """
            INSERT INTO ManagedBridges (name, description, pos1_idx, pos2_idx)
            VALUES (?, ?, ?, ?)
            """,
            (bridge_name, description, pos1_idx, pos2_idx),
        )
        conn.commit()
        return True, f"Đã thêm cầu '{bridge_name}'."
    except sqlite3.IntegrityError:
        return False, f"Lỗi: Cầu '{bridge_name}' đã tồn tại."
    except Exception as e:
        return False, f"Lỗi add_managed_bridge: {e}"
    finally:
        if conn:
            conn.close()


def update_managed_bridge(bridge_id, description, is_enabled, db_name=DB_NAME):
    """(BỔ SUNG) Cập nhật mô tả hoặc trạng thái Bật/Tắt của cầu."""
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE ManagedBridges
            SET description = ?, is_enabled = ?
            WHERE id = ?
            """,
            (description, 1 if is_enabled else 0, bridge_id),
        )
        conn.commit()
        return True, "Cập nhật thành công."
    except Exception as e:
        return False, f"Lỗi update_managed_bridge: {e}"
    finally:
        if conn:
            conn.close()


def delete_managed_bridge(bridge_id, db_name=DB_NAME):
    """(BỔ SUNG) Xóa một cầu khỏi CSDL."""
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
        if conn:
            conn.close()


def upsert_managed_bridge(
    bridge_name, description, win_rate, db_name=DB_NAME, pos1_idx=None, pos2_idx=None
):
    """
    (BỔ SUNG) Thêm cầu nếu chưa có, hoặc cập nhật nếu đã có.
    (CẬP NHẬT GĐ 3) Bổ sung pos1_idx, pos2_idx.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Bước 1: Dịch tên cầu (nếu index chưa được cung cấp)
        if pos1_idx is None or pos2_idx is None:
            if "+" in bridge_name:
                try:
                    pos1_name, pos2_name = bridge_name.split("+")
                    pos1_idx = get_index_from_name_V16(pos1_name.strip())
                    pos2_idx = get_index_from_name_V16(pos2_name.strip())
                except Exception:
                    pos1_idx, pos2_idx = None, None
            elif "Tổng(" in bridge_name or "Hiệu(" in bridge_name:
                pos1_idx, pos2_idx = -1, -1

        # Bước 2: Thử UPDATE (Nếu cầu đã tồn tại)
        cursor.execute(
            """
            UPDATE ManagedBridges
            SET description = ?, win_rate_text = ?,
                pos1_idx = ?, pos2_idx = ?,
                is_enabled = 1
            WHERE name = ?
            """,
            (description, win_rate, pos1_idx, pos2_idx, bridge_name),
        )

        # Bước 3: Nếu không có gì được UPDATE (rowcount=0), INSERT cầu mới
        if cursor.rowcount == 0:
            cursor.execute(
                """
                INSERT INTO ManagedBridges
                (name, description, win_rate_text, pos1_idx, pos2_idx, is_enabled)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (bridge_name, description, win_rate, pos1_idx, pos2_idx),
            )
            conn.commit()
            return True, f"Đã THÊM cầu '{bridge_name}'."

        conn.commit()
        return True, f"Đã CẬP NHẬT cầu '{bridge_name}'."

    except Exception as e:
        if conn:
            conn.close()
        return False, f"Lỗi upsert_managed_bridge: {e}"


# ===================================================================================
# (MỚI) GIAI ĐOẠN 1 / BƯỚC 3a: HÀM CẬP NHẬT CACHE K2N
# ===================================================================================


def update_bridge_k2n_cache_batch(cache_data_list, db_name=DB_NAME):
    """
    (CẬP NHẬT) Cập nhật hàng loạt dữ liệu cache K2N (Thêm max_lose_streak và recent_win_count_10).
    cache_data_list: list các tuple:
    [(win_rate, streak, prediction, max_lose_streak, recent_win_count_10, bridge_name), ...]
    """
    updated_count = 0
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # (SỬA) Thêm cột max_lose_streak_k2n và recent_win_count_10
        sql_update = """
        UPDATE ManagedBridges
        SET win_rate_text = ?,
            current_streak = ?,
            next_prediction_stl = ?,
            max_lose_streak_k2n = ?,
            recent_win_count_10 = ?
        WHERE name = ?
        """

        # Thực thi hàng loạt
        cursor.executemany(sql_update, cache_data_list)
        updated_count = cursor.rowcount
        conn.commit()

        return (
            True,
            f"Đã cập nhật cache K2N cho {updated_count} cầu (V17 + CĐ + BN) vào CSDL.",
        )
    except Exception as e:
        return False, f"Lỗi SQL khi cập nhật cache K2N: {e}"
    finally:
        if conn:
            conn.close()


# ===================================================================================
# (MỚI) GIAI ĐOẠN 1 / BƯỚC 3b: HÀM CẬP NHẬT TỶ LỆ (CHO CẦU BẠC NHỚ)
# ===================================================================================


def update_bridge_win_rate_batch(rate_data_list, db_name=DB_NAME):
    """
    (CẬP NHẬT GĐ 3) CHỈ cập nhật TỶ LỆ (dùng cho Cầu Bạc Nhớ / N1)
    """
    updated_count = 0
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Chỉ cập nhật win_rate_text và BẬT cầu lên
        sql_update = """
        UPDATE ManagedBridges
        SET win_rate_text = ?,
            is_enabled = 1
        WHERE name = ?
        """
        cursor.executemany(sql_update, rate_data_list)
        updated_count = cursor.rowcount
        conn.commit()
        return True, f"Đã cập nhật Tỷ Lệ N1 cho {updated_count} cầu (BN)."

    except Exception as e:
        return False, f"Lỗi SQL khi cập nhật Tỷ Lệ N1 (BN): {e}"
    finally:
        if conn:
            conn.close()
