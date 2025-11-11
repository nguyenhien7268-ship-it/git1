import sqlite3
import os

DB_NAME = 'xo_so_prizes_all_logic.db' 

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
        # Nếu DB chưa tồn tại/bị lỗi, trả về list rỗng (Đây là nơi lỗi thường xảy ra)
        # print(f"Lỗi get_all_managed_bridges: {e}")
        return []