# Tên file: tests/debug_de_system.py
import sys
import os

# --- CẤU HÌNH ĐƯỜNG DẪN TỰ ĐỘNG ---
# Lấy đường dẫn thư mục chứa file này (thư mục tests)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Lấy thư mục cha của nó (thư mục git1 - root project)
project_root = os.path.abspath(os.path.join(current_dir, '..'))

# Thêm project root vào sys.path để Python tìm thấy folder 'logic'
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"--- BẮT ĐẦU DEBUG HỆ THỐNG DE ---")
print(f"📍 Project Root: {project_root}")

# 1. KIỂM TRA IMPORT BO_SO_DE
try:
    from logic.de_utils import BO_SO_DE
    print(f"✅ Import BO_SO_DE thành công.")
    print(f"   > Số lượng bộ: {len(BO_SO_DE)}")
    # In thử vài key để xem định dạng thực tế
    print(f"   > 5 Key đầu tiên: {list(BO_SO_DE.keys())[:5]}")
    
    if len(BO_SO_DE) == 0:
        print("❌ CẢNH BÁO: BO_SO_DE ĐANG RỖNG! -> Nguyên nhân Bộ Đẹp không chạy.")
except ImportError as e:
    print(f"❌ LỖI IMPORT logic.de_utils: {e}")
    BO_SO_DE = {}

# 2. KIỂM TRA SCANNER & DATA TYPE
try:
    from logic.bridges.de_bridge_scanner import run_de_scanner
    print("✅ Import Scanner thành công.")
    
    # Mock data giả lập (cần ít nhất 2 kỳ)
    mock_data = [
        ['2023-01-01', '...', '12345'], 
        ['2023-01-02', '...', '67890']
    ]
    
    print("\n--- Chạy thử Scanner (Mock Data) ---")
    # Gọi hàm quét
    scan_result = run_de_scanner(mock_data)
    
    # Xử lý kết quả trả về (đôi khi là tuple, đôi khi là list)
    if isinstance(scan_result, tuple):
        count, bridges = scan_result
    else:
        bridges = scan_result
    
    print(f"   > Kiểu dữ liệu 'bridges': {type(bridges)}")
    
    # Kiểm tra Generator (nguyên nhân tiềm ẩn)
    import types
    if isinstance(bridges, types.GeneratorType):
        print("⚠️ CẢNH BÁO CHÍ MẠNG: 'bridges' là GENERATOR! Cần convert sang list.")
        bridges = list(bridges)
    
    print(f"   > Số lượng cầu tìm thấy: {len(bridges)}")
    
    # 3. KIỂM TRA CẤU TRÚC CẦU & LOGIC TÍNH ĐIỂM
    if len(bridges) > 0:
        b = bridges[0]
        print(f"   > Mẫu cầu đầu tiên: Type='{b.get('type')}', Val='{b.get('predicted_value')}'")
    else:
        # Tạo cầu giả để test logic nếu mock data không ra cầu
        print("   > (Scanner trả về rỗng, tạo cầu giả để test...)")
        bridges = [
            {'type': 'BO_TEST', 'predicted_value': '00', 'streak': 5},
            {'type': 'BO_TEST', 'predicted_value': 'Bo 12', 'streak': 3} # Test định dạng chuẩn
        ]
        
    # 4. TEST HÀM get_top_strongest_sets THỰC TẾ
    try:
        from logic.de_analytics import get_top_strongest_sets
        print("\n--- Test get_top_strongest_sets ---")
        result = get_top_strongest_sets(bridges)
        print(f"👉 KẾT QUẢ CHỐT BỘ: {result}")
        
        if not result:
            print("❌ LỖI: Hàm trả về rỗng dù có cầu đầu vào.")
        else:
            print("✅ OK: Hàm có trả về kết quả.")
    except ImportError:
        print("❌ LỖI: Không import được de_analytics.")

except Exception as e:
    print(f"❌ LỖI RUNTIME: {e}")
    import traceback
    traceback.print_exc()

print("\n--- KẾT THÚC DEBUG ---")