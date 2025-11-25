# Tên file: git1/logic/data_repository.py
#
# (PHIÊN BẢN V7.9 - FIX PATH DB TUYỆT ĐỐI)
#
import sqlite3
import os
from datetime import datetime

# --- CẤU HÌNH ĐƯỜNG DẪN DB TUYỆT ĐỐI ---
# Lấy thư mục hiện tại của file này (thư mục logic)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Lấy thư mục gốc dự án (cha của logic)
project_root = os.path.dirname(current_dir)
# Đường dẫn thư mục data
data_dir = os.path.join(project_root, "data")
# Đường dẫn DB tuyệt đối
DB_NAME = os.path.join(data_dir, "xo_so_prizes_all_logic.db")
# ----------------------------------------

def load_data_ai_from_db(db_name=DB_NAME):
    """Tải toàn bộ dữ liệu A:I từ DB (10 cột)."""
    # Không cần import os ở đây nữa vì đã import ở trên
    
    if not os.path.exists(db_name):
        return (
            None,
            f"Lỗi: Không tìm thấy database '{db_name}'. Vui lòng chạy 'Nạp File' trước.",
        )

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
            return (
                None,
                f"Lỗi: Database '{db_name}' rỗng. Vui lòng chạy 'Nạp File' trước.",
            )

        return rows, f"Đã tải {len(rows)} hàng A:I từ CSDL."
    except Exception as e:
        return None, f"Lỗi SQL khi tải dữ liệu A:I: {e}"


def get_all_managed_bridges(db_name=DB_NAME, only_enabled=False):
    """
    (V7.1) Lấy danh sách Cầu Đã Lưu (từ bảng ManagedBridges).
    Hàm này trả về dict (thay vì list) để dễ tra cứu.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        # Thiết lập row_factory để trả về dict
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql_query = "SELECT * FROM ManagedBridges"
        if only_enabled:
            sql_query += " WHERE is_enabled = 1"
        sql_query += " ORDER BY name ASC"

        cursor.execute(sql_query)
        rows = cursor.fetchall()

        # Chuyển đổi [sqlite3.Row] thành [dict]
        dict_rows = [dict(row) for row in rows]

        return dict_rows

    except Exception:
        # Nếu bảng không tồn tại hoặc lỗi, trả về danh sách rỗng
        return []
    finally:
        if conn:
            conn.close()


def get_latest_ky_date(conn):
    """
    (V7.0) Lấy KỲ và NGÀY mới nhất từ CSDL A:I để kiểm tra trùng lặp.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT ky, date FROM results_A_I ORDER BY ky DESC LIMIT 1")
        latest = cursor.fetchone()

        if latest:
            latest_ky_str = str(latest[0]).strip()
            date_str = str(latest[1]).strip()

            # Thử 1: Định dạng chuẩn dd/mm/YYYY
            try:
                latest_date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                return latest_ky_str, latest_date_obj
            except ValueError:
                pass

            # Thử 2: Định dạng chuẩn YYYY-mm-dd
            try:
                latest_date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                return latest_ky_str, latest_date_obj
            except ValueError:
                pass

            # Thử 3: Định dạng thiếu năm dd-mm (VD: 13-11)
            try:
                # Thêm năm hiện tại vào
                date_str_with_year = f"{date_str}-{datetime.now().year}"
                latest_date_obj = datetime.strptime(date_str_with_year, "%d-%m-%Y")
                return latest_ky_str, latest_date_obj
            except ValueError:
                pass

            # Thử 4: Định dạng thiếu năm dd/mm (VD: 13/11)
            try:
                # Thêm năm hiện tại vào
                date_str_with_year = f"{date_str}/{datetime.now().year}"
                latest_date_obj = datetime.strptime(date_str_with_year, "%d/%m/%Y")
                return latest_ky_str, latest_date_obj
            except ValueError:
                pass

            # Nếu tất cả thất bại
            print(f"Cảnh báo: Không thể phân tích ngày '{date_str}' từ CSDL.")

    except Exception as e:
        print(f"Lỗi get_latest_ky_date: {e}")

    return None, None