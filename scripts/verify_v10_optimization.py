# Tên file: scripts/verify_v10_optimization.py
# Mục tiêu: Kiểm tra logic On-Demand Analysis (Lô/Đề tách biệt) và đo lường hiệu năng.

import sys
import os
import time
import pandas as pd

# Thêm đường dẫn project root để import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

try:
    from logic.db_manager import DB_NAME
    from logic.data_repository import load_data_ai_from_db
    from services.analysis_service import AnalysisService
    
    # Giả lập Logger để không bị lỗi khi khởi tạo Service
    class MockLogger:
        def log(self, msg):
            print(f"[LOG] {msg}")

except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    sys.exit(1)

def measure_execution(service, all_data, lo_mode, de_mode, label):
    print(f"\n{'='*60}")
    print(f"🚀 TEST CASE: {label}")
    print(f"   Cấu hình: Lô={lo_mode}, Đề={de_mode}")
    print(f"{'-'*60}")
    
    start_time = time.time()
    
    # Gọi hàm phân tích
    result = service.prepare_dashboard_data(
        all_data, 
        data_limit=500, # Test với 500 kỳ để giả lập thực tế
        lo_mode=lo_mode, 
        de_mode=de_mode
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"⏱️ Thời gian thực thi: {duration:.4f} giây")
    
    # Kiểm tra dữ liệu trả về
    verify_data(result, lo_mode, de_mode)
    
    return duration

def verify_data(result, expect_lo, expect_de):
    if not result:
        print("❌ LỖI: Không nhận được kết quả trả về!")
        return

    # 1. Kiểm tra Dữ liệu Lô
    has_lo_data = False
    # Kiểm tra một số key đặc trưng của Lô
    if result.get('stats_n_day') and result.get('top_scores'):
        has_lo_data = True
    
    # 2. Kiểm tra Dữ liệu Đề
    has_de_data = False
    if result.get('df_de') is not None and not result.get('df_de').empty:
        has_de_data = True
        
    # Đánh giá
    print("📊 Kết quả kiểm tra dữ liệu:")
    
    # Check Lô
    if expect_lo:
        if has_lo_data: print("   ✅ [LÔ] Có dữ liệu (Đúng)")
        else: print("   ❌ [LÔ] Thiếu dữ liệu (Sai)")
    else:
        if not has_lo_data: print("   ✅ [LÔ] Không có dữ liệu (Đúng - Đã bỏ qua)")
        else: 
            # Có thể list rỗng vẫn được khởi tạo, kiểm tra kỹ hơn độ dài
            if len(result.get('top_scores', [])) == 0:
                 print("   ✅ [LÔ] Dữ liệu rỗng (Đúng - Đã bỏ qua)")
            else:
                 print("   ⚠️ [LÔ] Vẫn tính toán dữ liệu? (Cần kiểm tra lại)")

    # Check Đề
    if expect_de:
        if has_de_data: print("   ✅ [ĐỀ] Có dữ liệu DataFrame (Đúng)")
        else: print("   ❌ [ĐỀ] Thiếu dữ liệu DataFrame (Sai)")
    else:
        if not has_de_data: print("   ✅ [ĐỀ] Không có dữ liệu (Đúng - Đã bỏ qua)")
        else: print("   ❌ [ĐỀ] Vẫn tính toán dữ liệu? (Sai)")

def main():
    print("🛠️ BẮT ĐẦU KIỂM THỬ TÍNH NĂNG ON-DEMAND ANALYSIS (V10.0)")
    
    # 1. Setup môi trường
    if not os.path.exists(DB_NAME):
        print(f"❌ Không tìm thấy DB tại {DB_NAME}")
        return

    print("... Đang tải dữ liệu từ DB...")
    all_data, msg = load_data_ai_from_db(DB_NAME)
    if not all_data:
        print("❌ DB rỗng hoặc lỗi tải.")
        return
    print(f"✅ Đã tải {len(all_data)} dòng dữ liệu.")
    
    # Khởi tạo Service
    service = AnalysisService(DB_NAME, logger=MockLogger())
    
    # 2. Chạy các Test Case
    
    # Case 1: Chạy Cả Hai (Baseline)
    t_full = measure_execution(service, all_data, True, True, "FULL ANALYSIS")
    
    # Case 2: Chỉ Chạy Lô
    t_lo = measure_execution(service, all_data, True, False, "ONLY LO MODE")
    
    # Case 3: Chỉ Chạy Đề
    t_de = measure_execution(service, all_data, False, True, "ONLY DE MODE")
    
    # 3. Tổng kết hiệu năng
    print(f"\n{'='*60}")
    print("📈 TỔNG KẾT HIỆU NĂNG")
    print(f"{'='*60}")
    print(f"1. Full Mode: {t_full:.4f}s")
    print(f"2. Lô Only  : {t_lo:.4f}s (Tiết kiệm: {t_full - t_lo:.4f}s)")
    print(f"3. Đề Only  : {t_de:.4f}s (Tiết kiệm: {t_full - t_de:.4f}s)")
    
    if t_de < 1.0:
        print("\n✅ ĐÁNH GIÁ: Chế độ Đề chạy RẤT NHANH (<1s). Tối ưu thành công!")
    else:
        print("\n⚠️ ĐÁNH GIÁ: Chế độ Đề còn chậm, cần kiểm tra thêm.")

if __name__ == "__main__":
    main()