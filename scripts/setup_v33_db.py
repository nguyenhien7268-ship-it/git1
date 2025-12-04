# Tên file: scripts/setup_v33_db.py
import sqlite3
import os
import sys

# Định vị đường dẫn DB
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
db_path = os.path.join(root_dir, "data", "xo_so_prizes_all_logic.db")

print(f"Checking DB at: {db_path}")

try:
    # Tạo thư mục data nếu chưa có
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tạo bảng ManagedBridges
    sql = """
    CREATE TABLE IF NOT EXISTS ManagedBridges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        type TEXT,
        description TEXT,
        win_rate_text TEXT,
        current_streak INTEGER,
        next_prediction_stl TEXT,
        is_enabled INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    cursor.execute(sql)
    
    # Kiểm tra và thêm cột thiếu (Migration)
    cursor.execute("PRAGMA table_info(ManagedBridges)")
    cols = [info[1] for info in cursor.fetchall()]
    print(f"Current columns: {cols}")
    
    required = ['name', 'type', 'description', 'win_rate_text', 'current_streak', 'next_prediction_stl']
    for col in required:
        if col not in cols:
            print(f"Adding missing column: {col}")
            cursor.execute(f"ALTER TABLE ManagedBridges ADD COLUMN {col} TEXT")
            
    conn.commit()
    conn.close()
    print("✅ ĐÃ KHỞI TẠO DATABASE THÀNH CÔNG!")
except Exception as e:
    print(f"❌ LỖI: {e}")