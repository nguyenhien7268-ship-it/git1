# scripts/debug_backtest_exception.py
import sys
import os
import traceback

# Setup đường dẫn
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from services.analysis_service import AnalysisService
    from services.data_service import DataService
    from logic.db_manager import DB_NAME
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    sys.exit(1)

def run_debug():
    print("--- 🔍 DEBUG BACKTEST CẦU BỘ (DE_SET) ---")
    
    # 1. Tải dữ liệu
    ds = DataService(DB_NAME)
    all_data = ds.load_data()
    if not all_data:
        print("❌ Không có dữ liệu.")
        return

    # 2. Chọn một cầu Bộ mẫu (Lấy từ kết quả scan trước đó)
    bridge_name = "DE_SET_GDB2_G12" 
    print(f"👉 Đang thử Backtest cầu: {bridge_name}")

    # 3. Gọi AnalysisService
    service = AnalysisService(DB_NAME)
    
    try:
        # Gọi hàm backtest mà UI đang sử dụng
        if hasattr(service, 'run_de_backtest_30_days'):
            results = service.run_de_backtest_30_days(bridge_name, all_data)
            print(f"✅ Thành công! Kết quả: {len(results) if results else 'None'} dòng.")
        else:
            print("❌ Lỗi: AnalysisService không có hàm 'run_de_backtest_30_days'.")
            
    except Exception as e:
        print("\n❌ PHÁT HIỆN LỖI (EXCEPTION):")
        print("-" * 40)
        traceback.print_exc()
        print("-" * 40)
        print("👉 Nguyên nhân: AnalysisService chưa xử lý được ID 'DE_SET'.")

if __name__ == "__main__":
    run_debug()