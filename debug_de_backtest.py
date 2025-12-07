# Tên file: debug_de_backtest.py
import sys
import os
import sqlite3
import traceback

# 1. SETUP ĐƯỜNG DẪN
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

print(">>> [INIT] Đang khởi tạo môi trường kiểm tra...")

try:
    from lottery_service import load_data_ai_from_db, DB_NAME
    from logic.de_backtester_core import run_de_bridge_historical_test
    print(f">>> [IMPORT] Thành công. DB_NAME: {DB_NAME}")
except ImportError as e:
    print(f">>> [LỖI IMPORT] Không thể load modules: {e}")
    exit()

# 2. HÀM GIẢ LẬP PARSE CẦU (ĐỂ KIỂM TRA LOGIC)
def mock_parse_bridge(bridge_name):
    """Giả lập logic parse tên cầu: VD GDB.1-G1.2"""
    try:
        parts = bridge_name.split("-")
        if len(parts) != 2: return None
        
        def parse_one(s):
            # GDB.1 -> (GDB, 1)
            p = s.split(".")
            return p[0], int(p[1]) if len(p) > 1 else 0
            
        p1 = parse_one(parts[0])
        p2 = parse_one(parts[1])
        return {"pos1": p1, "pos2": p2}
    except Exception as e:
        print(f"Lỗi parse: {e}")
        return None

# 3. CHẠY TEST
def run_diagnostic():
    print("\n---------------------------------------------------")
    print(">>> [BƯỚC 1] Tải dữ liệu từ DB...")
    
    # Check DB file
    if not os.path.exists(DB_NAME):
        print(f">>> [LỖI] Không tìm thấy file DB tại: {DB_NAME}")
        return

    all_data, msg = load_data_ai_from_db(DB_NAME)
    if not all_data or len(all_data) < 10:
        print(f">>> [LỖI] Dữ liệu quá ít hoặc rỗng. Msg: {msg}")
        return
    print(f">>> [OK] Đã tải {len(all_data)} dòng dữ liệu.")

    # Tạo một tên cầu giả định để test (Cầu Giải ĐB số 1 ghép Giải 1 số 1)
    test_bridge_name = "GDB.0-G1.0" 
    
    print(f"\n>>> [BƯỚC 2] Thử Backtest cầu động: '{test_bridge_name}'")
    
    # Cấu hình Fallback giống như tôi đã sửa trong analysis_service.py
    fallback_config = {
        "name": test_bridge_name,
        "type": "DE_DYNAMIC_K",
        "is_scanner_result": True,
        "def_string": test_bridge_name
    }
    
    print(f">>> Config gửi đi: {fallback_config}")

    try:
        # GỌI HÀM CORE
        results = run_de_bridge_historical_test(fallback_config, all_data, days=30)
        
        if results is None:
            print(">>> [KẾT QUẢ] None (Hàm trả về rỗng - Có lỗi bên trong nhưng bị try/except bắt)")
        elif len(results) == 0:
            print(">>> [KẾT QUẢ] List Rỗng [] (Logic chạy nhưng không tìm thấy cầu hoặc lỗi parse)")
            # Kiểm tra xem logic parse có hoạt động không
            print("    -> Khả năng cao logic trong 'de_backtester_core' chưa xử lý cờ 'is_scanner_result'.")
        else:
            print(f">>> [THÀNH CÔNG] Nhận được {len(results)} kết quả backtest!")
            print("    -> Mẫu kết quả đầu tiên:", results[0])
            
    except Exception as e:
        print(f">>> [CRASH] Lỗi khi gọi run_de_bridge_historical_test:")
        traceback.print_exc()

if __name__ == "__main__":
    run_diagnostic()
    input("\nNhấn Enter để thoát...")