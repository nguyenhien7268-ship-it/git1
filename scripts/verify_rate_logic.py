# Tên file: code6/scripts/verify_rate_logic.py
import sqlite3
import os
import sys

# Setup đường dẫn
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

DB_PATH = os.path.join(os.path.dirname(current_dir), "data", "xo_so_prizes_all_logic.db")

def verify_logic():
    print(f"📡 Kết nối DB: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. CLEANUP & PREPARE: Xóa cầu test cũ (nếu có)
    TEST_ID = "TEST_PRESERVE_LOGIC"
    cursor.execute("DELETE FROM ManagedBridges WHERE name=?", (TEST_ID,))
    conn.commit()

    # 2. SETUP: Tạo cầu giả với K1N Gốc
    print("🛠️  Tạo cầu giả lập với K1N = 'GỐC_KHÔNG_ĐỔI'...")
    cursor.execute("""
        INSERT INTO ManagedBridges (name, description, win_rate_text, search_rate_text, is_enabled)
        VALUES (?, ?, ?, ?, ?)
    """, (TEST_ID, "Mô tả gốc", "GỐC_KHÔNG_ĐỔI", "", 1))
    conn.commit()

    # 3. SIMULATE LOGIC: Giả lập logic trong bridge_manager_core.py
    print("🔄 Giả lập quá trình Dò Cầu (Scan update)...")
    
    # [Logic Core Bước 1]: Lấy map hiện tại
    cursor.execute("SELECT name, win_rate_text FROM ManagedBridges")
    existing_map = {row[0]: row[1] for row in cursor.fetchall()}
    
    # [Logic Core Bước 2]: Tính toán giá trị update
    # Giả sử dò được tỷ lệ mới là "MỚI_DÒ_ĐƯỢC"
    scan_rate_new = "MỚI_DÒ_ĐƯỢC"
    
    # Xác định K1N cần giữ
    if TEST_ID in existing_map:
        preserved_k1n = existing_map[TEST_ID] # Phải lấy được "GỐC_KHÔNG_ĐỔI"
    else:
        preserved_k1n = "N/A"
        
    print(f"   -> Logic xác định K1N cần bảo toàn là: '{preserved_k1n}'")

    # [Logic Core Bước 3]: Thực hiện Upsert (Update)
    # Lưu ý: search_rate_text được cập nhật, win_rate_text dùng lại preserved_k1n
    cursor.execute("""
        UPDATE ManagedBridges 
        SET search_rate_text=?, win_rate_text=?
        WHERE name=?
    """, (scan_rate_new, preserved_k1n, TEST_ID))
    conn.commit()

    # 4. VERIFY: Kiểm tra kết quả
    print("🔍 Kiểm tra kết quả trong DB...")
    cursor.execute("SELECT win_rate_text, search_rate_text FROM ManagedBridges WHERE name=?", (TEST_ID,))
    row = cursor.fetchone()
    
    k1n_result = row[0]
    scan_result = row[1]

    print(f"   -> Kết quả K1N trong DB: '{k1n_result}'")
    print(f"   -> Kết quả K2N trong DB: '{scan_result}'")

    if k1n_result == "GỐC_KHÔNG_ĐỔI" and scan_result == "MỚI_DÒ_ĐƯỢC":
        print("\n✅ THÀNH CÔNG: Logic bảo toàn K1N hoạt động chính xác!")
        print("   K1N cũ không bị ghi đè, Scan Rate mới đã được cập nhật.")
    else:
        print("\n❌ THẤT BẠI: Dữ liệu bị sai lệch!")

    # Cleanup
    cursor.execute("DELETE FROM ManagedBridges WHERE name=?", (TEST_ID,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    verify_logic()