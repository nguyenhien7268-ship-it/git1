# File: scripts/verify_v38_scoring.py
import sys
import os

# Add root project path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from logic.de_analytics import calculate_number_scores
    from logic.de_utils import BO_SO_DE
    print("✅ Import thành công module logic.")
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    sys.exit(1)

def run_test():
    print("=== BẮT ĐẦU TEST LOGIC SCORING V3.8 (ULTIMATE) ===")
    
    # 1. Giả lập dữ liệu cầu
    bridges = [
        # Tấn công: Chạm 8 (Streak 5 -> Điểm +5)
        {"type": "DE_PASCAL", "predicted_value": "8", "streak": 5, "name": "Pascal Test"},
        
        # Tấn công: Bộ 00 (00, 55, 05, 50) (Streak 3 -> Điểm +6 [x2 hệ số bộ])
        {"type": "DE_DYNAMIC_BO", "predicted_value": "00", "streak": 3, "name": "Bộ Test"},
        
        # Phòng thủ: Loại Chạm 5 (Streak 4 -> Điểm trừ -12 [x3 hệ số loại])
        {"type": "DE_KILLER", "predicted_value": "LOẠI CHẠM 5", "streak": 4, "name": "Killer Test"}
    ]
    
    # 2. Giả lập thống kê thị trường (Chạm 8 đang hot)
    market_stats = {
        "freq_cham": {8: 20, 0: 5, 5: 5}, # Chạm 8 về 20 lần (Max)
        "freq_bo": {"00": 2}
    }
    
    print(f"INPUT Bridges: {len(bridges)}")
    print("------------------------------------------------")
    
    # 3. Chạy hàm tính điểm
    scores = calculate_number_scores(bridges, market_stats)
    
    # 4. Kiểm tra kết quả các số đặc trưng
    
    # CASE A: Số 88 (Thuộc Chạm 8)
    # Kỳ vọng: +5 (Pascal) + 2.0 (Bonus Chạm 8 Hot) = 7.0
    score_88 = next((s for n, s in scores if n == "88"), 0)
    print(f"Số 88 (Chạm 8 Hot): {score_88:.1f} điểm | Kỳ vọng ~7.0")
    
    # CASE B: Số 00 (Thuộc Bộ 00)
    # Kỳ vọng: +6 (Cầu Bộ) + điểm nhỏ bonus = ~6.x
    score_00 = next((s for n, s in scores if n == "00"), 0)
    print(f"Số 00 (Bộ 00): {score_00:.1f} điểm | Kỳ vọng > 6.0")
    
    # CASE C: Số 55 (Thuộc Bộ 00 NHƯNG dính Loại Chạm 5)
    # Tấn công: +6 (Bộ 00)
    # Phòng thủ: -12 (Loại Chạm 5)
    # Bonus: nhỏ
    # Tổng: Khoảng -6.0
    score_55 = next((s for n, s in scores if n == "55"), 0)
    print(f"Số 55 (Bộ 00 - Dính Killer Chạm 5): {score_55:.1f} điểm | Kỳ vọng < 0 (Bị loại)")
    
    # CASE D: Số 58 (Dính Chạm 8 và Loại Chạm 5)
    # Tấn công: +5 (Chạm 8)
    # Phòng thủ: -12 (Loại Chạm 5)
    # Tổng: ~ -7.0
    score_58 = next((s for n, s in scores if n == "58"), 0)
    print(f"Số 58 (Chạm 8 - Dính Killer Chạm 5): {score_58:.1f} điểm | Kỳ vọng < 0 (Bị loại)")

    # Đánh giá chung
    if score_55 < 0 and score_88 > 5:
        print("\n✅ KẾT QUẢ: Logic hoạt động đúng! Killer đã triệt tiêu số xấu thành công.")
    else:
        print("\n❌ KẾT QUẢ: Logic sai. Vui lòng kiểm tra lại hệ số.")

if __name__ == "__main__":
    run_test()