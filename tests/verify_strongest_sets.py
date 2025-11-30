# Tên file: tests/verify_fix_bo_mismatch.py
import unittest

# 1. GIẢ LẬP DỮ LIỆU TỪ DE_UTILS (MOCK)
# Đây là cấu trúc dữ liệu thực tế trong hệ thống của bạn
MOCK_BO_SO_DE = {
    'Bo 00': ['00', '05', '50', '55'],
    'Bo 12': ['12', '21', '67', '76'],
    'Bo 23': ['23', '32', '78', '87']
}

# 2. HÀM CẦN KIỂM TRA (SẼ ĐƯỢC THÊM VÀO DE_ANALYTICS.PY)
def _normalize_bo_key(val):
    """
    Helper: Chuẩn hóa giá trị từ cầu (vd: "00") thành key trong BO_SO_DE (vd: "Bo 00")
    """
    val = str(val).strip()
    
    # Trường hợp 1: Scanner trả về đúng chuẩn (vd: "Bo 00") -> Giữ nguyên
    if val in MOCK_BO_SO_DE:
        return val
        
    # Trường hợp 2: Scanner trả về thiếu tiền tố (vd: "00") -> Thử thêm "Bo "
    val_prefix = f"Bo {val}"
    if val_prefix in MOCK_BO_SO_DE:
        return val_prefix
        
    return None

# 3. GIẢ LẬP HÀM TÍNH ĐIỂM (MÔ PHỎNG get_top_strongest_sets)
def calculate_score_simulation(bridges):
    scores = {}
    print(f"\n--- Đang xử lý {len(bridges)} cầu ---")
    
    for b in bridges:
        raw_val = b['predicted_value']
        streak = b['streak']
        
        # ÁP DỤNG HÀM FIX
        normalized_key = _normalize_bo_key(raw_val)
        
        print(f"  > Input: '{raw_val}' | Streak: {streak} => Mapped to: '{normalized_key}'")
        
        if normalized_key:
            if normalized_key not in scores: scores[normalized_key] = 0
            scores[normalized_key] += streak
            
    return scores

# 4. CHẠY TEST CASE
class TestBoMismatchFix(unittest.TestCase):

    def test_fix_missing_prefix(self):
        """Kịch bản: Scanner trả về '00', hệ thống cũ bị fail, hệ thống mới phải nhận diện được."""
        print("\nTEST 1: Scanner trả về số thô (thiếu 'Bo ')")
        
        # Giả lập dữ liệu từ Scanner trả về (Lỗi hiện tại của bạn)
        bridges_input = [
            {'type': 'BO_TEST', 'predicted_value': '00', 'streak': 5}, # Scanner chỉ trả về "00"
            {'type': 'BO_TEST', 'predicted_value': '12', 'streak': 3}  # Scanner chỉ trả về "12"
        ]
        
        final_scores = calculate_score_simulation(bridges_input)
        
        # KỲ VỌNG: Phải tính được điểm cho "Bo 00" và "Bo 12"
        self.assertIn('Bo 00', final_scores, "LỖI: Không nhận diện được '00' là 'Bo 00'")
        self.assertEqual(final_scores['Bo 00'], 5, "LỖI: Điểm số cho 'Bo 00' bị sai")
        
        self.assertIn('Bo 12', final_scores, "LỖI: Không nhận diện được '12' là 'Bo 12'")
        print("=> KẾT QUẢ: Test 1 PASS (Đã tự động fix lỗi thiếu tiền tố)")

    def test_keep_correct_format(self):
        """Kịch bản: Scanner trả về đúng 'Bo 23', hệ thống vẫn phải hoạt động đúng."""
        print("\nTEST 2: Scanner trả về đúng chuẩn")
        
        bridges_input = [
            {'type': 'BO_TEST', 'predicted_value': 'Bo 23', 'streak': 10}
        ]
        
        final_scores = calculate_score_simulation(bridges_input)
        
        self.assertIn('Bo 23', final_scores)
        self.assertEqual(final_scores['Bo 23'], 10)
        print("=> KẾT QUẢ: Test 2 PASS (Giữ nguyên định dạng đúng)")

    def test_invalid_input(self):
        """Kịch bản: Giá trị rác không tồn tại."""
        print("\nTEST 3: Giá trị không tồn tại")
        
        bridges_input = [{'type': 'BO_TEST', 'predicted_value': '999', 'streak': 1}]
        final_scores = calculate_score_simulation(bridges_input)
        
        self.assertEqual(len(final_scores), 0, "Lỗi: Giá trị rác vẫn được tính điểm")
        print("=> KẾT QUẢ: Test 3 PASS (Bỏ qua giá trị rác)")

if __name__ == '__main__':
    unittest.main()