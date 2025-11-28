# Tên file: scripts/verify_fix_ui.py
import sys
import os
import sqlite3

# Thêm thư mục gốc vào path để import logic
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

try:
    from logic.data_repository import get_all_data_ai
    from logic.bridges.bridge_manager_de import de_manager
    from logic.db_manager import DB_NAME
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    sys.exit(1)

def run_verification_ui_fix():
    print("=== KIỂM TRA FIX LỖI UI & DỰ ĐOÁN (CẦU ĐỀ) ===")
    
    # 1. Tải dữ liệu
    print("\n[1] Đang tải dữ liệu xổ số...")
    data = get_all_data_ai()
    if not data or len(data) < 50:
        print("❌ Dữ liệu quá ít hoặc lỗi tải.")
        return
    print(f"✅ Đã tải {len(data)} dòng dữ liệu.")

    # 2. Chạy Update Daily Stats (Để kích hoạt logic sửa DB và tính toán)
    print("\n[2] Đang chạy 'de_manager.update_daily_stats'...")
    try:
        updated_count, active_list = de_manager.update_daily_stats(data)
        print(f"✅ Đã cập nhật {updated_count} cầu.")
    except Exception as e:
        print(f"❌ Lỗi Crash khi chạy Manager: {e}")
        return

    # 3. Kiểm tra Dữ liệu trả về cho UI (Quan trọng cho bảng hiển thị)
    print("\n[3] Kiểm tra cấu trúc dữ liệu trả về cho UI...")
    if not active_list:
        print("⚠️ Không có cầu nào được bật (active_list rỗng). Hãy thử Quét lại cầu.")
    else:
        sample = active_list[0]
        # In mẫu ra để soi
        print(f"   🔹 Mẫu dữ liệu (Dictionary):")
        print(f"      - Name: {sample.get('name')}")
        print(f"      - Wins 10 kỳ (recent_win_count_10): {sample.get('recent_win_count_10')}")
        print(f"      - Dự đoán (predicted_value): '{sample.get('predicted_value')}'")
        
        # A. Check lỗi mất dữ liệu 10 kỳ
        if "recent_win_count_10" in sample and sample["recent_win_count_10"] is not None:
            print("   ✅ [OK] Đã có key 'recent_win_count_10' cho UI.")
        else:
            print("   ❌ [FAIL] Vẫn thiếu key 'recent_win_count_10'!")

        # B. Check lỗi hiển thị chữ 'Chạm'
        pred = str(sample.get("predicted_value", ""))
        if "Chạm" in pred:
             print(f"   ⚠️ [FAIL] Dự đoán vẫn còn chữ 'Chạm': '{pred}'.")
        else:
             print(f"   ✅ [OK] Dự đoán đã sạch (Chỉ còn số): '{pred}'")

    # 4. Kiểm tra Cấu trúc Database (Quan trọng cho việc lưu trữ)
    print("\n[4] Kiểm tra Cấu trúc Database (ManagedBridges)...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check xem cột đã được tạo chưa
    cursor.execute("PRAGMA table_info(ManagedBridges)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if "next_prediction_stl" in columns:
        print("   ✅ [OK] Đã tìm thấy cột 'next_prediction_stl' trong DB.")
    else:
        print("   ❌ [FAIL] Chưa có cột 'next_prediction_stl' trong DB!")

    # Check dữ liệu thực tế trong DB
    print("\n[5] Kiểm tra Dữ liệu thực tế trong DB...")
    cursor.execute("SELECT name, recent_win_count_10, next_prediction_stl FROM ManagedBridges WHERE is_enabled=1 LIMIT 1")
    row = cursor.fetchone()
    if row:
        name_db, win10_db, pred_db = row
        print(f"   🔹 Dữ liệu trong DB: Name='{name_db}' | Win10={win10_db} | Pred='{pred_db}'")
        
        if pred_db: 
             print("   ✅ [OK] Database đã lưu được dự đoán.")
        else:
             print("   ⚠️ [WARN] Cột dự đoán trong DB vẫn rỗng.")
    else:
        print("   ⚠️ Không lấy được dòng mẫu nào từ DB.")

    conn.close()
    print("\n=== KẾT THÚC KIỂM TRA ===")

if __name__ == "__main__":
    run_verification_ui_fix()