# Tên file: scripts/verify_phase_c.py
import sys
import os
import sqlite3

# Thêm thư mục gốc vào path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

try:
    from logic.data_repository import get_all_data_ai
    # Import file core vừa sửa
    from logic.bridges.bridge_manager_core import find_and_auto_manage_bridges
    from logic.db_manager import DB_NAME
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    sys.exit(1)

def run_verification_phase_c():
    print("=== KIỂM TRA GIAI ĐOẠN C (CẦU LÔ FIX & HỒI QUY) ===")
    
    # 1. Tải dữ liệu
    print("\n[1] Đang tải dữ liệu xổ số...")
    data = get_all_data_ai()
    if not data or len(data) < 50:
        print("❌ Dữ liệu quá ít hoặc lỗi tải.")
        return
    print(f"✅ Đã tải {len(data)} dòng dữ liệu.")

    # 2. Chạy Hàm Quản Lý (Core)
    print("\n[2] Đang chạy 'find_and_auto_manage_bridges'...")
    try:
        # Hàm này bây giờ sẽ chạy cả 3 logic: V17, Bạc Nhớ, và Fixed
        result_msg = find_and_auto_manage_bridges(data)
        print(f"ℹ️  Kết quả trả về: {result_msg}")
    except Exception as e:
        print(f"❌ Core Manager bị lỗi Crash: {e}")
        return

    # 3. Kiểm tra Database
    print("\n[3] Kiểm tra Database (ManagedBridges)...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # A. Kiểm tra Cầu Lô Fixed (Mới)
    print("   > Kiểm tra 15 Cầu Lô Cố Định (New Feature)...")
    cursor.execute("SELECT count(*) FROM ManagedBridges WHERE name LIKE 'LO_STL_FIXED_%'")
    count_fixed = cursor.fetchone()[0]
    
    if count_fixed >= 15:
        print(f"     ✅ TÌM THẤY {count_fixed} cầu Lô Fixed (Đạt yêu cầu >= 15).")
    else:
        print(f"     ❌ CHƯA ĐẠT. Chỉ tìm thấy {count_fixed}/15 cầu Lô Fixed.")

    # B. Kiểm tra Cầu V17 Shadow (Logic Cũ)
    print("   > Kiểm tra Cầu V17 Shadow (Regression Test)...")
    # Cầu V17 thường có tên dạng "GDB[0]+G1[1]" hoặc không có prefix đặc biệt, nhưng type thường NULL hoặc check tên
    cursor.execute("SELECT count(*) FROM ManagedBridges WHERE name LIKE '%+%' AND name NOT LIKE 'LO_%' AND name NOT LIKE 'DE_%' AND name NOT LIKE 'Tổng%'")
    count_v17 = cursor.fetchone()[0]
    
    if count_v17 > 0:
        print(f"     ✅ Logic Cũ V17 vẫn hoạt động (Tìm thấy {count_v17} cầu).")
    else:
        print("     ⚠️ Cảnh báo: Không thấy cầu V17 cũ. Có thể do dữ liệu hoặc logic bị tắt.")

    # C. Kiểm tra Cầu Bạc Nhớ (Logic Cũ)
    print("   > Kiểm tra Cầu Bạc Nhớ (Regression Test)...")
    cursor.execute("SELECT count(*) FROM ManagedBridges WHERE name LIKE 'Tổng(%' OR name LIKE 'Hiệu(%'")
    count_bn = cursor.fetchone()[0]
    
    if count_bn > 0:
        print(f"     ✅ Logic Cũ Bạc Nhớ vẫn hoạt động (Tìm thấy {count_bn} cầu).")
    else:
        print("     ⚠️ Cảnh báo: Không thấy cầu Bạc Nhớ.")

    # 4. Kiểm tra mẫu dữ liệu chi tiết
    print("\n[4] Kiểm tra mẫu dữ liệu Cầu Lô Fixed...")
    cursor.execute("SELECT name, description, win_rate_text, type FROM ManagedBridges WHERE name = 'LO_STL_FIXED_01'")
    sample = cursor.fetchone()
    if sample:
        print(f"   - Name: {sample[0]}")
        print(f"   - Desc: {sample[1]}")
        print(f"   - Rate: {sample[2]}")
        print(f"   - Type: {sample[3]}")
        if sample[0] == 'LO_STL_FIXED_01' and 'GĐB+5' in sample[1]:
            print("     ✅ Dữ liệu mẫu Chính Xác!")
        else:
            print("     ❌ Dữ liệu mẫu Sai lệch.")
    else:
        print("     ❌ Không tìm thấy cầu mẫu LO_STL_FIXED_01.")

    conn.close()
    print("\n=== KẾT THÚC KIỂM TRA ===")

if __name__ == "__main__":
    run_verification_phase_c()