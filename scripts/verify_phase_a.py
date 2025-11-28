# Tên file: scripts/verify_phase_a.py
import sys
import os
import sqlite3

# Thêm thư mục gốc vào path để import được logic
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

try:
    from logic.data_repository import get_all_data_ai
    from logic.bridges.de_bridge_scanner import run_de_scanner
    from logic.bridges.bridge_manager_de import de_manager
    from logic.db_manager import DB_NAME
except ImportError as e:
    print(f"Lỗi Import: {e}")
    sys.exit(1)

def run_verification():
    print("=== KIỂM TRA GIAI ĐOẠN A (CẦU ĐỀ V2.1) ===")
    
    # 1. Kiểm tra dữ liệu đầu vào
    print("\n[1] Đang tải dữ liệu xổ số...")
    data = get_all_data_ai()
    if not data or len(data) < 50:
        print("❌ Dữ liệu quá ít hoặc lỗi tải.")
        return
    print(f"✅ Đã tải {len(data)} dòng dữ liệu.")

    # 2. Chạy Scanner (Test Sinh Cầu)
    print("\n[2] Đang chạy Scanner (run_de_scanner)...")
    try:
        count, bridges = run_de_scanner(data)
        print(f"✅ Scanner chạy xong. Tìm thấy {count} cầu.")
    except Exception as e:
        print(f"❌ Scanner bị lỗi: {e}")
        return

    # 3. Kiểm tra Format Tên trong DB
    print("\n[3] Kiểm tra định dạng tên trong Database...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, type, description FROM ManagedBridges WHERE type IN ('DE_POS_SUM', 'DE_DYNAMIC_K') ORDER BY current_streak DESC LIMIT 5")
    rows = cursor.fetchall()
    
    if not rows:
        print("❌ Không tìm thấy cầu nào trong DB sau khi quét!")
    else:
        all_format_ok = True
        for r in rows:
            name, b_type, desc = r
            print(f"   - Name: {name:<25} | Type: {b_type:<15} | Desc: {desc[:30]}...")
            
            # Logic check định dạng
            if not (name.startswith("DE_POS_") or name.startswith("DE_DYN_")):
                print(f"     ⚠️ CẢNH BÁO: Tên '{name}' không đúng chuẩn DE_...!")
                all_format_ok = False
        
        if all_format_ok:
            print("✅ Tất cả 5 cầu mẫu đều đúng định dạng tên V2.1.")
        else:
            print("❌ Có cầu sai định dạng tên.")

    # 4. Chạy Parser (Test Đọc & Tính toán lại)
    print("\n[4] Kiểm tra Parser (de_manager.update_daily_stats)...")
    try:
        updated_count, active_list = de_manager.update_daily_stats(data)
        print(f"   - Số cầu được cập nhật phong độ: {updated_count}")
        
        if updated_count > 0:
            sample = active_list[0]
            print(f"   - Mẫu kết quả Parser: {sample['name']} -> Dự đoán: {sample['predicted_value']}")
            print("✅ Parser hoạt động tốt! Hệ thống hiểu được tên cầu mới.")
        else:
            print("⚠️ Parser không cập nhật được cầu nào. Có thể do chưa bật (is_enabled=0) hoặc lỗi Parser.")
    
    except Exception as e:
        print(f"❌ Parser bị lỗi Crash: {e}")
    
    conn.close()
    print("\n=== KẾT THÚC KIỂM TRA ===")

if __name__ == "__main__":
    run_verification()