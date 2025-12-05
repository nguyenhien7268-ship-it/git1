# Tên file: scripts/verify_real_scoring.py
# (PHIÊN BẢN V3.8.3 - FIX IMPORT PATH)

import sys
import os
import sqlite3
import time

# Thêm đường dẫn project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from logic.db_manager import DB_NAME
    from logic.data_repository import load_data_ai_from_db
    
    # [QUAN TRỌNG] Fix đường dẫn import dashboard_scorer
    try:
        from logic.analytics.dashboard_scorer import prepare_daily_features, get_top_scored_pairs
    except ImportError:
        from logic.dashboard_analytics import prepare_daily_features, get_top_scored_pairs

    # [QUAN TRỌNG] Fix đường dẫn import de_bridge_scanner (nằm trong bridges)
    from logic.bridges.de_bridge_scanner import run_de_scanner
    
    from logic.de_analytics import calculate_number_scores, analyze_market_trends
except ImportError as e:
    print(f"❌ Lỗi Import Ban Đầu: {e}")
    sys.exit(1)

def verify_real_lo_scoring():
    print("\n" + "="*50)
    print("🚀 KIỂM TRA SCORING LÔ V3.8 (REAL DATA)")
    print("="*50)
    
    # 1. Tải dữ liệu
    print("... Đang tải dữ liệu từ DB...")
    all_data, msg = load_data_ai_from_db(DB_NAME)
    if not all_data:
        print("❌ LỖI: Không có dữ liệu A:I trong DB.")
        return

    # Lấy 500 kỳ gần nhất để xử lý nhanh
    data_slice = all_data[-500:]
    last_ky = data_slice[-1][0]
    print(f"✅ Đã tải {len(data_slice)} kỳ. Kỳ cuối: {last_ky}")

    # 2. Chuẩn bị Features (Mô phỏng Dashboard)
    print("... Đang tính toán Features (Stats, Consensus, K2N)...")
    t0 = time.time()
    try:
        # Gọi hàm chuẩn bị dữ liệu (giống hệt UI)
        features = prepare_daily_features(data_slice, len(data_slice)-1)
        
        if not features:
            print("⚠️ Cảnh báo: Không tạo được features (Có thể thiếu dữ liệu cầu).")
            return

        # 3. Tính điểm
        print("... Đang chạy Scoring Engine...")
        scores = get_top_scored_pairs(
            features["stats_n_day"],
            features["consensus"],
            features["high_win"],
            features["pending_k2n"],
            features["gan_stats"],
            features["top_memory"],
            features.get("ai_predictions"),
            features.get("recent_data")
        )
        t1 = time.time()
        print(f"✅ Tính toán xong trong {t1-t0:.2f}s.")

        # 4. Hiển thị kết quả
        print("\n🏆 TOP 5 LÔ ĐIỂM CAO NHẤT:")
        print(f"{'Cặp Số':<10} | {'Điểm':<8} | {'Lý do chính'}")
        print("-" * 60)
        
        if scores:
            for item in scores[:5]:
                # Rút gọn lý do để hiển thị
                reasons = str(item.get('reasons', ''))
                reason_short = reasons[:50] + "..." if len(reasons) > 50 else reasons
                print(f"{item.get('pair', '??'):<10} | {item.get('score', 0):<8.1f} | {reason_short}")
        else:
            print("(Không có dữ liệu điểm - Có thể chưa 'Dò Cầu' hoặc chưa 'Làm Mới Cache')")

    except Exception as e:
        print(f"❌ LỖI LOGIC LÔ: {e}")
        import traceback
        traceback.print_exc()

def verify_real_de_scoring():
    print("\n" + "="*50)
    print("🚀 KIỂM TRA SCORING ĐỀ V3.8 (REAL DATA)")
    print("="*50)
    
    # 1. Tải dữ liệu
    all_data, _ = load_data_ai_from_db(DB_NAME)
    if not all_data: return
    data_slice = all_data[-100:] # Lấy 100 kỳ cho Đề
    
    # 2. Quét cầu & Thống kê
    print("... Đang quét cầu Đề & Phân tích thị trường...")
    try:
        # Quét cầu
        count, bridges = run_de_scanner(data_slice)
        print(f"✅ Tìm thấy {len(bridges)} cầu Đề (Scanner V3.3).")
        
        # Thống kê thị trường
        market_stats = analyze_market_trends(data_slice)
        
        # 3. Tính điểm
        print("... Đang chạy Scoring Engine Đề...")
        scores = calculate_number_scores(bridges, market_stats)
        
        # 4. Hiển thị kết quả
        print("\n🏆 TOP 5 SỐ ĐỀ ĐIỂM CAO NHẤT:")
        print(f"{'Số':<6} | {'Điểm':<8} | {'Ghi chú'}")
        print("-" * 40)
        
        if scores:
            for item in scores[:5]:
                # Item là tuple (số, điểm) do hàm sort trả về
                num = item[0]
                score = item[1]
                print(f"{num:<6} | {score:<8.1f} |")
        else:
            print("(Không có dữ liệu điểm)")
            
    except Exception as e:
        print(f"❌ LỖI LOGIC ĐỀ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_real_lo_scoring()
    verify_real_de_scoring()
    print("\n" + "="*50)
    print("👉 NẾU KẾT QUẢ HIỆN RA ĐẦY ĐỦ -> HỆ THỐNG ĐÃ SẴN SÀNG 100%.")