import sqlite3
import os
import sys

# Setup đường dẫn
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logic.db_manager import DB_NAME

def clean_legacy():
    print(f"🧹 ĐANG DỌN DẸP DATABASE: {DB_NAME}")
    if not os.path.exists(DB_NAME):
        print("❌ Lỗi: Không tìm thấy DB.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Xóa các cầu không bắt đầu bằng DE_ hoặc LO_
    print("   -> Đang xóa các cầu sai quy chuẩn (UNKNOWN/OTHER)...")
    cursor.execute("DELETE FROM ManagedBridges WHERE name NOT LIKE 'DE_%' AND name NOT LIKE 'LO_%'")
    deleted = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    if deleted > 0:
        print(f"✅ ĐÃ XÓA THÀNH CÔNG: {deleted} cầu rác/cũ.")
        print("   (Database giờ chỉ còn lại các cầu chuẩn DE_ và LO_)")
    else:
        print("✨ Database đã sạch (Không có cầu rác).")

if __name__ == "__main__":
    clean_legacy()