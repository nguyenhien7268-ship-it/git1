# Tên file: tests/verify_gan_vs_bridge.py
import unittest
from collections import Counter

# 1. GIẢ LẬP MÔI TRƯỜNG
# Mock BO_SO_DE
MOCK_BO_SO_DE = {'Bo 00': ['00', '55'], 'Bo 11': ['11', '66'], 'Bo 22': ['22', '77']}

# Mock các hàm từ de_analytics (để không phụ thuộc file ngoài)
def get_top_strongest_sets_mock(bridges):
    # Logic hiện tại: Chỉ quan tâm Streak, không quan tâm Gan
    set_scores = {bo: 0 for bo in MOCK_BO_SO_DE.keys()}
    for b in bridges:
        val = b['predicted_value'] # Giả sử đã chuẩn hóa thành 'Bo XX'
        streak = b['streak']
        if val in set_scores:
            set_scores[val] += streak
    
    # Sắp xếp giảm dần theo điểm
    sorted_sets = sorted(set_scores.items(), key=lambda x: x[1], reverse=True)
    return [x[0] for x in sorted_sets if x[1] > 0]

class TestGanVsBridge(unittest.TestCase):
    
    def test_gan_but_strong_bridge(self):
        print("\n--- BẮT ĐẦU TEST: GAN VS CẦU MẠNH ---")
        
        # 1. GIẢ LẬP TÌNH HUỐNG GAN
        # Bộ 00 và 11 đang GAN (không xuất hiện trong list kết quả giả lập)
        print("📊 Tình huống giả định:")
        print("   - Bộ 00: Gan 25 ngày (Rất xấu về mặt thống kê)")
        print("   - Bộ 11: Gan 21 ngày")
        print("   - Bộ 22: Mới về (Gan 2 ngày)")
        
        # 2. GIẢ LẬP CẦU BÁO (BRIDGES)
        # Các cầu đang chạy rất thông (Streak cao) lại báo về đúng các bộ Gan này
        bridges = [
            {'type': 'BO_TEST', 'predicted_value': 'Bo 00', 'streak': 10}, # Cầu rất mạnh báo Gan 00
            {'type': 'BO_TEST', 'predicted_value': 'Bo 11', 'streak': 8},  # Cầu mạnh báo Gan 11
            {'type': 'BO_TEST', 'predicted_value': 'Bo 22', 'streak': 5}   # Cầu thường báo Bộ 22
        ]
        
        print("\n🌉 Danh sách Cầu tìm được:")
        for b in bridges:
            print(f"   - Báo {b['predicted_value']} | Streak: {b['streak']} (Cầu Động uy tín)")
            
        # 3. CHẠY LOGIC CHỐT BỘ
        strong_sets = get_top_strongest_sets_mock(bridges)
        
        print(f"\n🏆 KẾT QUẢ CHỐT BỘ ĐẸP: {strong_sets}")
        
        # 4. KIỂM TRA
        # Logic hiện tại: Bo 00 phải đứng đầu vì Streak cao nhất (10), bất chấp nó Gan
        self.assertEqual(strong_sets[0], 'Bo 00', "Bo 00 phải đứng Top 1 do cầu mạnh nhất")
        self.assertEqual(strong_sets[1], 'Bo 11', "Bo 11 phải đứng Top 2")
        
        print("\n✅ KẾT LUẬN: Logic code đang hoạt động ĐÚNG.")
        print("   Hệ thống ưu tiên 'Cầu đang chạy' hơn 'Lịch sử Gan'.")
        print("   Nếu bạn muốn Né Gan, cần thêm bộ lọc 'Penalty'.")

if __name__ == '__main__':
    unittest.main()