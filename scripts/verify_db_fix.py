# Tên file: code6/scripts/verify_db_fix.py
import sqlite3
import os
import sys

# Setup đường dẫn
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import trực tiếp hàm cần test
from logic.db_manager import update_bridge_k2n_cache_batch, DB_NAME

def verify_fix():
    print(f"📡 Đang test trên DB: {DB_NAME}")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. SETUP: Tạo cầu giả với K1N cố định
    TEST_NAME = "TEST_DB_FIX_BATCH"
    # Xóa cũ nếu có
    cursor.execute("DELETE FROM ManagedBridges WHERE name=?", (TEST_NAME,))
    conn.commit()
    
    print("🛠️ Tạo cầu giả với K1N = 'ORIGINAL_K1N' (Giá trị cần bảo vệ)...")
    cursor.execute("""
        INSERT INTO ManagedBridges (name, win_rate_text, search_rate_text, is_enabled)
        VALUES (?, ?, ?, 1)
    """, (TEST_NAME, "ORIGINAL_K1N", "0.00%"))
    conn.commit()
    
    # 2. ACTION: Gọi hàm update batch (Giả lập hành động của Controller khi chạy bảng quyết định)
    # Cấu trúc tuple đầu vào theo code mới: (rate, streak, pred, max_lose, ignored, name)
    # Hàm sẽ lấy index 0, 1, 2, 3, 5
    batch_data = [
        ("NEW_K2N_RATE", 10, "11,22", 5, "IGNORED_VAL", TEST_NAME)
    ]
    
    print("🔄 Gọi hàm update_bridge_k2n_cache_batch...")
    try:
        success, msg = update_bridge_k2n_cache_batch(batch_data, DB_NAME)
        print(f"   Kết quả gọi hàm: {msg}")
    except Exception as e:
        print(f"❌ Lỗi gọi hàm: {e}")
        return

    # 3. VERIFY: Kiểm tra xem K1N có bị đổi không
    print("🔍 Kiểm tra dữ liệu trong DB...")
    cursor.execute("SELECT win_rate_text, search_rate_text FROM ManagedBridges WHERE name=?", (TEST_NAME,))
    row = cursor.fetchone()
    
    if not row:
        print("❌ Lỗi: Không tìm thấy cầu test!")
        return

    k1n_result = row[0]
    k2n_result = row[1]
    
    print(f"   K1N (Kỳ vọng 'ORIGINAL_K1N'): {k1n_result}")
    print(f"   K2N (Kỳ vọng 'NEW_K2N_RATE'): {k2n_result}")
    
    if k1n_result == "ORIGINAL_K1N" and k2n_result == "NEW_K2N_RATE":
        print("\n✅ PASS: Hàm Update Batch hoạt động chuẩn xác!")
        print("   - K1N được bảo toàn.")
        print("   - K2N (Search Rate) được cập nhật đúng cột.")
    else:
        print("\n❌ FAIL: Dữ liệu vẫn bị ghi đè hoặc không cập nhật!")

    # Cleanup
    cursor.execute("DELETE FROM ManagedBridges WHERE name=?", (TEST_NAME,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    verify_fix()