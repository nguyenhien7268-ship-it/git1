import sys
import os
import sqlite3

# Thêm đường dẫn project vào sys.path để import được các module logic
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

try:
    from logic.data_repository import get_all_data_ai
    from logic.bridges.bridge_manager_core import _update_fixed_lo_bridges, find_and_auto_manage_bridges
    from logic.db_manager import DB_NAME
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    print("👉 Hãy đảm bảo bạn lưu script này vào thư mục 'code6/scripts/'")
    sys.exit(1)

def force_update():
    print("🚀 BẮT ĐẦU CẬP NHẬT DỮ LIỆU DỰ ĐOÁN (FORCE UPDATE)...")
    
    # 1. Kiểm tra Database
    if not os.path.exists(DB_NAME):
        print(f"❌ Không tìm thấy Database tại: {DB_NAME}")
        return

    # 2. Lấy dữ liệu kết quả xổ số
    print("⏳ Đang tải dữ liệu xổ số...")
    all_data = get_all_data_ai(DB_NAME)
    if not all_data or len(all_data) < 10:
        print("❌ Dữ liệu xổ số quá ít hoặc rỗng. Vui lòng nạp file dữ liệu trước.")
        return
    print(f"✅ Đã tải {len(all_data)} kỳ dữ liệu.")

    # 3. Chạy cập nhật 15 Cầu Cố Định (Đây là nơi sinh ra lỗi N/A cho bảng Top 10)
    print("\n------------------------------------------------")
    print("🔄 Đang tính toán lại 15 Cầu Cố Định (Fixed Bridges)...")
    try:
        count = _update_fixed_lo_bridges(all_data, DB_NAME)
        print(f"✅ Đã cập nhật thành công {count} cầu cố định.")
    except Exception as e:
        print(f"❌ Lỗi khi cập nhật Fixed Bridges: {e}")
        import traceback
        traceback.print_exc()

    # 4. (Tùy chọn) Chạy cập nhật các cầu khác
    print("\n------------------------------------------------")
    print("🔄 Đang rà soát lại các cầu V17 & Bạc Nhớ (Auto Manage)...")
    try:
        msg = find_and_auto_manage_bridges(all_data, DB_NAME)
        print(f"✅ Kết quả: {msg}")
    except Exception as e:
        print(f"⚠️ Có lỗi nhỏ khi rà soát cầu động (có thể bỏ qua): {e}")

    # 5. Kiểm tra lại kết quả trong DB
    print("\n------------------------------------------------")
    print("📊 KIỂM TRA DỮ LIỆU SAU CẬP NHẬT:")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Lấy thử 5 cầu có điểm cao nhất
    cursor.execute("""
        SELECT name, win_rate_text, next_prediction_stl 
        FROM ManagedBridges 
        WHERE is_enabled=1 
        ORDER BY recent_win_count_10 DESC 
        LIMIT 5
    """)
    rows = cursor.fetchall()
    
    print(f"{'TÊN CẦU':<25} | {'WIN RATE':<10} | {'DỰ ĐOÁN (PRED)'}")
    print("-" * 60)
    has_na = False
    for row in rows:
        name, rate, pred = row
        print(f"{name:<25} | {rate:<10} | {pred}")
        if pred == 'N/A' or pred is None:
            has_na = True
            
    conn.close()
    
    print("-" * 60)
    if not has_na and len(rows) > 0:
        print("🎉 THÀNH CÔNG! Hết lỗi N/A. Bạn có thể mở App ngay.")
    else:
        print("⚠️ Vẫn còn N/A. Hãy kiểm tra lại log lỗi phía trên.")

if __name__ == "__main__":
    force_update()