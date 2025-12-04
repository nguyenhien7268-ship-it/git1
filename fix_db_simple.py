import sqlite3
import os

def fix_na_simple():
    print("🛠️ ĐANG CHẠY FIX LỖI N/A (PHIÊN BẢN ĐỘC LẬP)...")
    
    # 1. Xác định vị trí Database
    # Giả định script nằm trong code6/, db nằm trong code6/data/
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "data", "xo_so_prizes_all_logic.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Không tìm thấy file DB tại: {db_path}")
        print("Vui lòng kiểm tra lại đường dẫn.")
        return

    print(f"✅ Đã tìm thấy DB: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 2. Thực hiện lệnh SQL vá lỗi
        # Copy giá trị từ search_rate (đã có) sang win_rate (đang bị N/A)
        print(">> Đang cập nhật dữ liệu...")
        
        cursor.execute("""
            UPDATE ManagedBridges 
            SET win_rate_text = search_rate_text 
            WHERE (type LIKE 'LO_%' OR type = 'classic' OR type = 'LO_STL_FIXED') 
            AND (win_rate_text = 'N/A' OR win_rate_text IS NULL)
            AND search_rate_text != 'N/A' 
            AND search_rate_text != ''
        """)
        
        updated_rows = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"🎉 THÀNH CÔNG! Đã sửa {updated_rows} cầu đang bị lỗi N/A.")
        
    except Exception as e:
        print(f"❌ Lỗi khi thao tác DB: {e}")

if __name__ == "__main__":
    fix_na_simple()