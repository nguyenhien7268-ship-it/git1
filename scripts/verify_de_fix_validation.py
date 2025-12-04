# Tên file: code6/scripts/verify_de_fix_validation.py
import sys
import os
import random

# Thêm đường dẫn project để import được module logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.bridges.de_bridge_scanner import DeBridgeScanner

def mock_row(index):
    # Tạo dữ liệu giả lập 10 cột (Compact Mode)
    # [Date, Code, GDB, G1, ..., G7]
    row = [f"Day{index}", "SomeCode"]
    # GDB (index 2) -> G7 (index 9)
    for i in range(8):
        val = random.randint(0, 99)
        row.append(f"{val:02d}")
    return row

def verify_fix():
    print("=== TEST KIỂM TRA LOGIC V2.4 (CỨU CẦU & BỘ CHUẨN) ===")
    
    # 1. Tạo dữ liệu giả lập (60 ngày để đủ scan_depth + validation)
    print("1. Đang tạo dữ liệu giả lập (60 kỳ)...")
    mock_data = [mock_row(i) for i in range(60)]
    
    # 2. Khởi tạo Scanner
    scanner = DeBridgeScanner()
    print(f"\n[CẤU HÌNH HIỆN TẠI]")
    print(f"   - Scan Depth: {scanner.scan_depth} kỳ")
    print(f"   - Validation: {scanner.validation_len} kỳ (Check quá khứ)")
    print(f"   - Cầu Lô/Vị Trí: Streak >= {scanner.min_streak} HOẶC Wins10 >= {scanner.rescue_wins_10} (Cơ chế Cứu)")
    print(f"   - Cầu Bộ: Streak >= {scanner.min_streak_bo} VÀ Wins10 >= {scanner.min_wins_bo_10} (Cơ chế Chặt)")

    # 3. Chạy thử
    print("\n2. Đang chạy Scanner...")
    try:
        count, bridges = scanner.scan_all(mock_data)
        print(f"   => KẾT QUẢ: Tìm thấy {count} cầu.")
        
        if bridges:
            print(f"\n[PHÂN TÍCH MẪU CẦU TÌM ĐƯỢC]")
            # Lấy mẫu cầu đầu tiên
            top1 = bridges[0]
            print(f"   - Top 1: {top1['name']}")
            print(f"   - Loại: {top1['type']}")
            print(f"   - Streak: {top1['streak']}")
            print(f"   - Win Rate (10 kỳ): {top1['win_rate']:.1f}%")
            print(f"   - Mô tả: {top1['display_desc']}")
            
            # Kiểm tra xem có cầu nào được 'Cứu' không
            rescued = [b for b in bridges if "Cứu" in b['display_desc']]
            if rescued:
                print(f"   ✅ [SUCCESS] Logic Cứu Cầu hoạt động tốt! ({len(rescued)} cầu được cứu).")
            else:
                print("   ℹ️ Chưa tìm thấy cầu được cứu trong lần chạy này (Do ngẫu nhiên).")
        else:
            print("   ℹ️ Không tìm thấy cầu nào (Validation hoạt động chặt chẽ).")
            
    except Exception as e:
        print(f"❌ LỖI NGHIÊM TRỌNG: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_fix()