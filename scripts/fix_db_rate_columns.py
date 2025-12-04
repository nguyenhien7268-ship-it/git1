# Tên file: code6/scripts/fix_db_rate_columns.py
import sqlite3
import os
import sys

# Định nghĩa đường dẫn DB
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "xo_so_prizes_all_logic.db")

def migrate_db():
    print(f"📡 Đang kết nối tới DB: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("❌ Lỗi: Không tìm thấy file Database!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Kiểm tra các cột hiện có
        cursor.execute("PRAGMA table_info(ManagedBridges)")
        columns_info = cursor.fetchall()
        column_names = [info[1] for info in columns_info]
        
        print(f"ℹ️ Các cột hiện tại: {column_names}")
        
        # 2. Thêm cột search_rate_text (Dùng cho K2N/Decision Table) nếu chưa có
        if "search_rate_text" not in column_names:
            print("⚡ Đang thêm cột 'search_rate_text' (Lưu tỉ lệ K2N/Cache)...")
            cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN search_rate_text TEXT DEFAULT ''")
            print("✅ Đã thêm thành công.")
        else:
            print("✅ Cột 'search_rate_text' đã tồn tại.")

        # 3. Thêm cột search_period (Dùng cho số kỳ test) nếu chưa có
        if "search_period" not in column_names:
            print("⚡ Đang thêm cột 'search_period'...")
            cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN search_period INTEGER DEFAULT 0")
            print("✅ Đã thêm thành công.")
        else:
            print("✅ Cột 'search_period' đã tồn tại.")

        conn.commit()
        print("\n🎉 MIGRATION HOÀN TẤT! Database đã sẵn sàng tách biệt K1N và K2N.")
        
    except Exception as e:
        print(f"❌ Lỗi ngoại lệ: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()