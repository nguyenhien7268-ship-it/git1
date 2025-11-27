import sys
import os
import sqlite3

# Thêm đường dẫn để import được module logic
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def fix_database():
    try:
        from logic.db_manager import DB_NAME
        print(f">>> Đang kiểm tra Database tại: {DB_NAME}")
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # 1. Tạo bảng ManagedBridges nếu chưa có
        cursor.execute("""
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
            type TEXT DEFAULT 'UNKNOWN'
        )""")

        # 2. Kiểm tra và thêm cột thiếu
        cursor.execute("PRAGMA table_info(ManagedBridges)")
        columns = [info[1] for info in cursor.fetchall()]
        print(f"   -> Các cột hiện tại: {columns}")

        if "type" not in columns:
            print("   -> Đang thêm cột 'type'...")
            cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN type TEXT DEFAULT 'UNKNOWN'")
        
        if "recent_win_count_10" not in columns:
            print("   -> Đang thêm cột 'recent_win_count_10'...")
            cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN recent_win_count_10 INTEGER DEFAULT 0")

        # 3. Đồng bộ dữ liệu cũ
        print("   -> Đang phân loại lại dữ liệu cũ...")
        cursor.execute("UPDATE ManagedBridges SET type='DE_V17' WHERE name LIKE 'Đề %'")
        cursor.execute("UPDATE ManagedBridges SET type='CAU_BAC_NHO' WHERE name LIKE 'Tổng(%' OR name LIKE 'Hiệu(%'")
        cursor.execute("UPDATE ManagedBridges SET type='CAU_LO' WHERE type='UNKNOWN'")
        
        conn.commit()
        conn.close()
        print("✅ ĐÃ SỬA LỖI DATABASE THÀNH CÔNG!")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    fix_database()