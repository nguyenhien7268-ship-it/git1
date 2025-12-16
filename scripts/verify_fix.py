# Tên file: scripts/verify_fix.py
import sys
import os

# --- CẤU HÌNH ĐƯỜNG DẪN ---
# Lấy đường dẫn thư mục hiện tại (scripts)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Lấy đường dẫn thư mục gốc dự án (thư mục cha của scripts)
project_root = os.path.dirname(current_dir)
# Thêm thư mục gốc vào sys.path để Python tìm thấy 'logic'
sys.path.append(project_root)
# ---------------------------

try:
    from logic.bridges.de_bridge_scanner import DeBridgeScanner
except ImportError as e:
    print(f"LỖI IMPORT: {e}")
    print("Hãy chắc chắn bạn đang chạy từ thư mục gốc dự án.")
    sys.exit()

def test_logic():
    print(f">>> ĐANG KIỂM TRA TỪ THƯ MỤC: {current_dir}")
    scanner = DeBridgeScanner()
    
    # Mock data: [Thắng, Thắng, Thua, Thắng, Thắng] (Mới -> Cũ)
    mock_results = [True, True, False, True, True]
    print(f"Dữ liệu giả lập (Mới -> Cũ): {mock_results}")
    
    try:
        # Gọi hàm tính toán (Lưu ý: Nếu bạn đã tách hàm này ra common_utils thì sửa dòng này)
        metrics = scanner._calculate_performance_metrics(mock_results)
        
        streak = metrics['streak']
        total_wins = metrics['total_wins']
        
        print("-" * 40)
        print(f"Kết quả Streak:     {streak} (Mong đợi: 2)")
        print(f"Tổng số ngày thắng: {total_wins} (Mong đợi: 4)")
        print("-" * 40)
        
        if streak == 2 and total_wins == 4:
            print("✅ KẾT QUẢ: CHÍNH XÁC (Strict Mode OK)")
        else:
            print("❌ KẾT QUẢ: SAI (Vẫn tính cộng dồn)")
            
    except AttributeError:
        print("❌ LỖI: Không tìm thấy hàm '_calculate_performance_metrics' trong DeBridgeScanner.")

if __name__ == "__main__":
    test_logic()