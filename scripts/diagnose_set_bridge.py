import sys
import os
import sqlite3

# Setup đường dẫn
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from logic.bridges.de_bridge_scanner import DeBridgeScanner
    from logic.de_utils import BO_SO_DE
    print(f"✅ Đã nạp BO_SO_DE: {len(BO_SO_DE)} bộ số.")
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    sys.exit(1)

# Giả lập dữ liệu để test logic Cầu Bộ
def create_dummy_data():
    data = []
    # Tạo 30 ngày dữ liệu
    # Giả sử chúng ta muốn test Bộ 01 (01, 10, 06, 60, 51, 15, 56, 65)
    # GDB luôn là "01" -> Thuộc bộ 01
    # G1 luôn là "56" -> Vị trí tạo cầu (5+6=11 -> 1, 6 -> Ghép ra bộ?)
    # Cách đơn giản nhất:
    # Pos[0] = 0, Pos[1] = 1. Ghép lại thành "01" -> Bộ 01.
    # GDB về "01" -> TRÚNG.
    for i in range(30):
        # [Date, Code, GDB, G1, ... G7]
        # GDB: "00001" (Đề 01)
        # G1: "00001" (Lấy số đầu và cuối: 0, 1)
        row = [f"D{i}", "MB", "00001", "00001", "22222", "33333", "44444", "55555", "66666", "77777"]
        data.append(row)
    return data

def diagnose():
    print("\n--- BẮT ĐẦU CHẨN ĐOÁN CẦU BỘ ---")
    
    # 1. Kiểm tra cấu hình
    scanner = DeBridgeScanner()
    print(f"[*] Cấu hình hiện tại: Streak >= {scanner.min_streak_bo}, Wins10 >= {scanner.min_wins_bo_10}")
    
    # 2. Test với Dữ liệu Giả lập (Dummy Data)
    print("\n[*] Đang chạy test trên dữ liệu giả lập (Lý tưởng)...")
    dummy_data = create_dummy_data()
    bridges = scanner._scan_set_bridges(dummy_data)
    print(f" -> Kết quả giả lập: Tìm thấy {len(bridges)} cầu bộ.")
    
    if len(bridges) > 0:
        print(f"    Ví dụ: {bridges[0]['name']} | Streak: {bridges[0]['streak']}")
    else:
        print("    ❌ LỖI: Logic quét không bắt được ngay cả dữ liệu lý tưởng!")

    # 3. Test với Dữ liệu Thực (Nếu có)
    # Cố gắng load dữ liệu thật từ App
    real_data = []
    try:
        # Cách 1: Load từ file json (nếu app lưu cache)
        import json
        with open("data/kqxs_data.json", "r", encoding="utf-8") as f:
            real_data = json.load(f)
        print(f"\n[*] Đã load {len(real_data)} dòng dữ liệu thực từ file.")
    except:
        print("\n[!] Không tìm thấy file data/kqxs_data.json. Bỏ qua test dữ liệu thực.")

    if real_data:
        print("[*] Đang quét Cầu Bộ trên dữ liệu thực...")
        real_bridges = scanner._scan_set_bridges(real_data)
        print(f" -> Kết quả thực tế: Tìm thấy {len(real_bridges)} cầu bộ.")
        
        if len(real_bridges) == 0:
            print("    ⚠️ CẢNH BÁO: Không tìm thấy cầu bộ nào trên dữ liệu thực.")
            print("    -> Khả năng cao là do điều kiện lọc quá gắt hoặc dữ liệu đang giai đoạn khó.")
            print("    -> Đề xuất: Giảm min_streak_bo xuống 1 hoặc wins_10 xuống 3.")
        else:
            print("    ✅ Logic hoạt động tốt trên dữ liệu thực.")
            # In thử điểm số xếp hạng
            scanner._rank_bridges(real_bridges)
            print(f"    Top 1 Score: {real_bridges[0].get('ranking_score', 'N/A')}")

if __name__ == "__main__":
    diagnose()