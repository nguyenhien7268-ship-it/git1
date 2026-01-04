import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

try:
    from logic.data_repository import get_all_data_ai
    from logic.backtest_runner import BacktestRunner
    from logic.bridge_executor import BridgeExecutor
    
    output_file = "VERIFICATION_RESULTS.txt"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=== KIỂM TRA SAU NÂNG CẤP ===\n\n")
        
        # 1. Check Data Load
        all_data = get_all_data_ai()
        if not all_data:
            f.write("FAIL: Không load được dữ liệu lịch sử.\n")
            sys.exit(1)
        f.write(f"1. Dữ liệu: Đã load {len(all_data)} bản ghi.\n")
        
        # 2. Check Backtest Runner Initialization
        try:
            runner = BacktestRunner()
            f.write("2. BacktestRunner: Khởi tạo thành công.\n")
        except Exception as e:
            f.write(f"FAIL: Lỗi khởi tạo BacktestRunner: {e}\n")
            sys.exit(1)
            
        # 3. Test Run on a Sample Bridge (Dynamic K)
        test_bridge = "DE_DYN_G1.0_G3.6.2_K1" # Example bridge
        f.write(f"\n3. Test Cầu: {test_bridge}\n")
        
        result = runner.run_backtest(test_bridge, all_data, days=10)
        
        if 'error' in result:
            f.write(f"FAIL: Lỗi chạy backtest: {result['error']}\n")
        else:
            f.write("   - Chạy thành công!\n")
            f.write(f"   - Tỉ lệ trúng: {result.get('win_rate')}%\n")
            f.write(f"   - Streak hiện tại (Real): {result.get('real_current_streak')}\n")
            f.write(f"   - Dự đoán ngày mai: {result.get('current_prediction')}\n")
            
            f.write("\n   --- CHI TIẾT 10 NGÀY --- \n")
            history = result.get('history', [])
            
            predictions = set()
            for entry in history:
                date = entry['date']
                pred = entry['predicted']
                res = entry['result']
                actual = entry['actual']
                f.write(f"   [{date}] Dự đoán: {pred} | KQ: {actual} | -> {res}\n")
                predictions.add(pred)
                
            f.write("\n")
            if len(predictions) > 1:
                f.write("✅ KẾT LUẬN: Dự đoán thay đổi theo ngày -> Full Backtest HOẠT ĐỘNG TỐT.\n")
            else:
                f.write("⚠️ CẢNH BÁO: Dự đoán không thay đổi (có thể do cầu ổn định hoặc lỗi).\n")

except Exception as e:
    with open("VERIFICATION_RESULTS.txt", "a", encoding="utf-8") as f:
        f.write(f"\nCRITICAL ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc(file=f)
