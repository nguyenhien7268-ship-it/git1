# scripts/check_real_db.py
import sqlite3
import os
import sys

# Thêm đường dẫn gốc để import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logic.db_manager import DB_NAME

def check_db():
    print(f"\n📡 ĐANG KẾT NỐI TỚI DB: {DB_NAME}")
    if not os.path.exists(DB_NAME):
        print("❌ LỖI: Không tìm thấy file Database!")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Thống kê các loại cầu
    print("\n📊 THỐNG KÊ CÁC LOẠI CẦU ĐANG CÓ:")
    try:
        cursor.execute("SELECT type, COUNT(*) FROM ManagedBridges GROUP BY type")
        rows = cursor.fetchall()
        
        has_de_set = False
        if not rows:
            print("   (Database đang trống hoặc không có cầu nào)")
        
        for r in rows:
            print(f"   - Loại {r[0]:<15}: {r[1]} cầu")
            if r[0] == 'DE_SET': has_de_set = True
    except Exception as e:
        print(f"❌ Lỗi query: {e}")
        conn.close()
        return

    # 2. Kiểm tra chi tiết
    if has_de_set:
        print("\n✅ ĐÃ TÌM THẤY CẦU 'DE_SET'. (Hệ thống đã cập nhật)")
        cursor.execute("SELECT name, description, next_prediction_stl FROM ManagedBridges WHERE type='DE_SET' LIMIT 3")
        samples = cursor.fetchall()
        print("\n🔍 MẪU 3 CẦU ĐẦU TIÊN:")
        for s in samples:
            print(f"   Ref:  {s[0]}")
            print(f"   Desc: {s[1]}")
            print(f"   Pred: {s[2]}")
            print("   ---")
    else:
        print("\n⚠️ CẢNH BÁO: CHƯA THẤY CẦU 'DE_SET'!")
        print("👉 KHUYẾN NGHỊ: Bạn cần chạy script 'run_scan_migration.py' để quét cầu ngay.")

    # 3. Kiểm tra rác (Cầu cũ)
    cursor.execute("SELECT COUNT(*) FROM ManagedBridges WHERE name LIKE 'G%' AND type='BO'")
    rac_count = cursor.fetchone()[0]
    if rac_count > 0:
        print(f"\n❌ CẢNH BÁO: Vẫn còn {rac_count} cầu cũ (dạng G...) cần xóa.")
    else:
        print("\n✨ Database sạch sẽ: Không còn cầu rác cũ.")

    conn.close()

if __name__ == "__main__":
    check_db()