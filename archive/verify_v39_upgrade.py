# Tên file: code6/scripts/verify_v39_upgrade.py
import sys
import os
import pandas as pd

# Thêm đường dẫn project vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from logic.de_analytics import run_intersection_matrix_analysis, BO_SO_DICT
    print("✅ Import thành công logic module.")
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    sys.exit(1)

def verify_logic():
    print("--- BẮT ĐẦU KIỂM TRA LOGIC V3.8 ---")
    
    # 1. Mock Dataframe
    data = {
        'Ngay': pd.date_range(start='2023-01-01', periods=20),
        'De': [10, 20, 30, 40, 50, 60, 70, 80, 90, 11, 22, 33, 44, 55, 66, 77, 88, 99, 15, 25]
    }
    df = pd.DataFrame(data)
    print(f"1. Tạo DataFrame giả lập: {len(df)} dòng.")

    # 2. Run Analysis
    try:
        result = run_intersection_matrix_analysis(df)
        print("2. Chạy hàm phân tích: OK")
        
        ranked = result.get('ranked', [])
        print(f"3. Kết quả trả về: {len(ranked)} số được chấm điểm.")
        
        if ranked:
            top_1 = ranked[0]
            print(f"   -> Top 1: Số {top_1['so']} ({top_1['diem']} điểm) - Rank: {top_1['rank']}")
            print(f"   -> Lý do: {top_1['note']}")
        else:
            print("❌ Không có kết quả xếp hạng.")
            
    except Exception as e:
        print(f"❌ Lỗi khi chạy phân tích: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_logic()