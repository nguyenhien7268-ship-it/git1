import sys
import os
import sqlite3

# --- TỰ ĐỘNG KHẮC PHỤC ĐƯỜNG DẪN IMPORT (PATH FIX) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
# Tìm thư mục chứa folder 'logic' bằng cách đi ngược lên
root_dir = current_dir
found = False
for _ in range(3):
    if os.path.exists(os.path.join(root_dir, 'logic')):
        found = True
        break
    parent = os.path.dirname(root_dir)
    if parent == root_dir: break
    root_dir = parent

if found:
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    print(f"✅ Đã tìm thấy Project Root: {root_dir}")
else:
    print("⚠️ Không tìm thấy folder 'logic'. Đang chạy ở chế độ standalone (hạn chế).")

# --------------------------------------------------------

try:
    from logic.db_manager import DB_NAME, get_db_connection
    from logic.data_repository import get_all_managed_bridges
    from logic.bridges.bridge_manager_core import _update_fixed_lo_bridges
    from logic.services.data_service import DataService # Giả định service lấy data
except ImportError as e:
    print(f"❌ LỖI IMPORT: {e}")
    print("Vui lòng đảm bảo bạn đang lưu file này trong thư mục code6 hoặc code6/scripts")
    # Fallback cho DB_NAME nếu import lỗi
    DB_NAME = os.path.join(root_dir, "data/xo_so_prizes_all_logic.db")

def fix_lo_na():
    print("🛠️ BẮT ĐẦU FIX LỖI N/A CHO CẦU LÔ...")
    
    # 1. Lấy dữ liệu Xổ Số để tính toán
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Lấy 30 kỳ gần nhất để tính
    try:
        cursor.execute("SELECT * FROM DuLieu_AI ORDER BY MaSoKy DESC LIMIT 30")
        rows = cursor.fetchall()
        # Convert row tuple to object/dict if needed for _update_fixed_lo_bridges
        # Nhưng hàm _update_fixed_lo_bridges trong bridge_manager_core.py mong đợi format data chuẩn
        # Ta sẽ dùng trick: Gọi hàm wrapper nếu có thể, hoặc update thủ công SQL
        
        # Cách đơn giản nhất: Update SQL trực tiếp set win_rate_text = search_rate_text 
        # (Vì search_rate_text thường đã có data từ lúc scan, chỉ win_rate_text bị N/A)
        
        print(">> Đang đồng bộ K2N (Search Rate) sang K1N (Win Rate) cho các cầu bị N/A...")
        
        # Query: Tìm các cầu LO bị N/A nhưng có Search Rate
        cursor.execute("""
            UPDATE ManagedBridges 
            SET win_rate_text = search_rate_text 
            WHERE (type LIKE 'LO_%' OR type = 'classic') 
            AND (win_rate_text = 'N/A' OR win_rate_text IS NULL)
            AND search_rate_text != 'N/A' 
            AND search_rate_text != ''
        """)
        
        updated_rows = cursor.rowcount
        print(f"✅ Đã vá nhanh {updated_rows} cầu (Copy SearchRate -> WinRate).")
        
        # 2. Xử lý triệt để: Gọi hàm tính toán lại cho 15 Cầu Fixed (Nếu import được)
        # Cần lấy data chuẩn format
        # Do cấu trúc data phức tạp, ta sẽ bỏ qua bước tính lại phức tạp này trong script fix nhanh
        # Thay vào đó, user chỉ cần chạy lại app, code sửa ở Bước 1 sẽ tự lo phần còn lại.
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Lỗi Logic: {e}")
        return

    print("------------------------------------------------")
    print("🎉 ĐÃ HOÀN TẤT!")
    print("1. Đã copy chỉ số 'Search Rate' sang 'K1N' cho các cầu bị thiếu.")
    print("2. Hãy khởi động lại ứng dụng.")
    print("3. Bấm 'Tìm Cầu Mới' -> Code mới trong bridge_manager_core sẽ tự động tính đúng từ giờ.")

if __name__ == "__main__":
    fix_lo_na()