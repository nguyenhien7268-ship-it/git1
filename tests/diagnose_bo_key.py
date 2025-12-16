# Tên file: debug_de_system.py
import sys
import os

# Setup đường dẫn để import được code trong logic/
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("--- BẮT ĐẦU DEBUG HỆ THỐNG DE ---")

# 1. KIỂM TRA IMPORT BO_SO_DE
try:
    from logic.de_utils import BO_SO_DE
    print(f"✅ Import BO_SO_DE thành công.")
    print(f"   > Số lượng bộ: {len(BO_SO_DE)}")
    print(f"   > 5 Key đầu tiên: {list(BO_SO_DE.keys())[:5]}")
    if len(BO_SO_DE) == 0:
        print("❌ CẢNH BÁO: BO_SO_DE ĐANG RỖNG! -> Nguyên nhân Bộ Đẹp không chạy.")
except ImportError as e:
    print(f"❌ LỖI IMPORT: {e}")
    BO_SO_DE = {}

# 2. KIỂM TRA SCANNER & DATA TYPE
try:
    from logic.bridges.de_bridge_scanner import run_de_scanner
    # Mock data giả lập (cần ít nhất 2 kỳ)
    mock_data = [
        ['2023-01-01', '...', '12345'], 
        ['2023-01-02', '...', '67890']
    ]
    
    print("\n--- Chạy thử Scanner (Mock Data) ---")
    count, bridges = run_de_scanner(mock_data)
    
    print(f"   > Kiểu dữ liệu 'bridges': {type(bridges)}")
    if not isinstance(bridges, list):
        print("⚠️ CẢNH BÁO: 'bridges' không phải là LIST (có thể là generator).")
        # Chuyển thành list để inspect
        bridges = list(bridges)
    
    print(f"   > Số lượng cầu tìm thấy: {len(bridges)}")
    
    # 3. KIỂM TRA CẤU TRÚC CẦU & LOGIC TÍNH ĐIỂM
    if len(bridges) > 0:
        b = bridges[0]
        print(f"   > Mẫu cầu đầu tiên: Type='{b.get('type')}', Val='{b.get('predicted_value')}'")
    else:
        # Tạo cầu giả để test logic
        print("   > (Scanner không trả về cầu nào với mock data, tạo cầu giả để test logic...)")
        bridges = [
            {'type': 'BO_TEST', 'predicted_value': '00', 'streak': 5},
            {'type': 'BO_TEST', 'predicted_value': 'Bo 12', 'streak': 3}
        ]
        
    # 4. TEST HÀM get_top_strongest_sets THỰC TẾ
    from logic.de_analytics import get_top_strongest_sets
    
    print("\n--- Test get_top_strongest_sets ---")
    result = get_top_strongest_sets(bridges)
    print(f"👉 KẾT QUẢ CHỐT BỘ: {result}")
    
    if not result:
        print("❌ LỖI: Hàm trả về rỗng dù có cầu đầu vào.")
    else:
        print("✅ OK: Hàm có trả về kết quả.")

except Exception as e:
    print(f"❌ LỖI RUNTIME: {e}")
    import traceback
    traceback.print_exc()

print("\n--- KẾT THÚC DEBUG ---")