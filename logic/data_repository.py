# Tên file: du-an-backup/logic/data_repository.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - SỬA LỖI PARSE NGÀY)
#
import sqlite3
import os
# (BỔ SUNG) Thêm datetime để xử lý ngày tháng
from datetime import datetime 

# ĐÃ SỬA: Cập nhật đường dẫn DB mới sau khi di chuyển file sang thư mục 'data/'
DB_NAME = 'data/xo_so_prizes_all_logic.db' 

def load_data_ai_from_db(db_name=DB_NAME):
    """Tải toàn bộ dữ liệu A:I từ DB (10 cột)."""
    import os
    if not os.path.exists(db_name):
         return None, f"Lỗi: Không tìm thấy database '{db_name}'. Vui lòng chạy 'Nạp File' trước."
    
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT MaSoKy, Col_A_Ky, Col_B_GDB, Col_C_G1, Col_D_G2, Col_E_G3, Col_F_G4, Col_G_G5, Col_H_G6, Col_I_G7
        FROM DuLieu_AI
        ORDER BY MaSoKy ASC 
        ''')
        rows_of_tuples = cursor.fetchall()
        rows_of_lists = [list(row) for row in rows_of_tuples] 
        conn.close()
        return rows_of_lists, f"Đã tải {len(rows_of_lists)} hàng A:I từ DB."
    except Exception as e:
        return None, f"Lỗi khi tải dữ liệu A:I: {e}"

def get_all_managed_bridges(db_name=DB_NAME, only_enabled=False):
    """
    Lấy tất cả các cầu đã lưu (ManagedBridges).
    """
    try:
        conn = sqlite3.connect(db_name)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        query = 'SELECT * FROM ManagedBridges' 
        if only_enabled:
            query += ' WHERE is_enabled = 1'
        query += ' ORDER BY id DESC'
            
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        # Đảm bảo trả về List of Dictionary
        return [dict(row) for row in rows] 
    except Exception as e:
        # Nếu DB chưa tồn tại/bị lỗi, trả về list rỗng
        return []

# ==========================================================
# (SỬA LỖI) CẬP NHẬT HÀM ĐỂ XỬ LÝ NGÀY THIẾU NĂM (VÍ DỤ: 13-11)
# ==========================================================
def get_latest_ky_date(cursor):
    """Lấy KỲ và NGÀY mới nhất từ DB (dùng chung cursor)."""
    try:
        cursor.execute("""
            SELECT T1.MaSoKy, T2.NgayThang 
            FROM DuLieu_AI AS T1
            LEFT JOIN KyQuay AS T2 ON T1.MaSoKy = T2.MaSoKy
            ORDER BY T1.MaSoKy DESC 
            LIMIT 1
        """)
        latest = cursor.fetchone()
        
        if latest:
            latest_ky_str = str(latest[0])
            date_str = str(latest[1])
            
            if not date_str or date_str == 'N/A':
                 print("Cảnh báo get_latest_ky_date: Không tìm thấy ngày, trả về ngày mặc định.")
                 return latest_ky_str, datetime.min

            # Thử 1: Định dạng chuẩn dd/mm/YYYY
            try:
                latest_date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                return latest_ky_str, latest_date_obj
            except ValueError:
                pass
            
            # Thử 2: Định dạng chuẩn YYYY-mm-dd
            try:
                latest_date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                return latest_ky_str, latest_date_obj
            except ValueError:
                pass

            # (SỬA) Thử 3: Định dạng thiếu năm dd-mm (VD: 13-11)
            try:
                # Thêm năm hiện tại vào
                date_str_with_year = f"{date_str}-{datetime.now().year}"
                latest_date_obj = datetime.strptime(date_str_with_year, '%d-%m-%Y')
                return latest_ky_str, latest_date_obj
            except ValueError:
                pass

            # (SỬA) Thử 4: Định dạng thiếu năm dd/mm (VD: 13/11)
            try:
                # Thêm năm hiện tại vào
                date_str_with_year = f"{date_str}/{datetime.now().year}"
                latest_date_obj = datetime.strptime(date_str_with_year, '%d/%m/%Y')
                return latest_ky_str, latest_date_obj
            except ValueError:
                pass

            # Nếu tất cả thất bại
            print(f"Cảnh báo: Không thể phân tích ngày '{date_str}'.")
            return latest_ky_str, datetime.min
            
        else:
            return None, None # DB rỗng
            
    except Exception as e:
        print(f"Lỗi get_latest_ky_date: {e}. Giả định DB rỗng.")
        return None, None