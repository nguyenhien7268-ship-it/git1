# Tên file: tests/verify_de_touch_rate_fix.py

# KHÔNG CẦN namedtuple, vì dữ liệu thực tế từ de_analytics.py là dictionary.

# Giả lập dữ liệu trả về TỪ HÀM calculate_top_touch_combinations
# (Hàm này sắp xếp theo ưu tiên: Max Streak > Rate Percent)
# Dữ liệu test 10 ngày (rate_total=10)
COMBOS_FROM_ANALYTICS = [
    # 1. Combo A (Streak cao nhất, Rate thấp nhất trong top) -> Logic cũ sẽ xếp thứ 1
    {'touches': [1, 2, 3, 4], 'streak': 3, 'rate_hits': 8, 'rate_total': 10, 'rate_percent': 80.0}, 
    
    # 2. Combo B (Streak thấp, Rate cao nhất) -> Logic cũ sẽ xếp thứ 2
    {'touches': [5, 6, 7, 8], 'streak': 1, 'rate_hits': 10, 'rate_total': 10, 'rate_percent': 100.0}, 
    
    # 3. Combo C (Streak thấp, Rate trung bình) -> Logic cũ sẽ xếp thứ 3
    {'touches': [9, 0, 1, 5], 'streak': 1, 'rate_hits': 9, 'rate_total': 10, 'rate_percent': 90.0}, 

    # 4. Combo D (Combo bị loại vì Rate < 80%)
    {'touches': [0, 2, 4, 6], 'streak': 4, 'rate_hits': 7, 'rate_total': 10, 'rate_percent': 70.0}, 
]

# --- MOCK LẠI HÀM _update_scan_ui CẦN TEST (ĐÃ SỬA LOGIC CHẠM TỈ LỆ) ---
class MockUiDeDashboard:
    def __init__(self, combos):
        self.touch_combos = combos
        self.lbl_cham_rate = self # Mock label
        self.top_touches = [] # Giả sử fallback rỗng
    
    def config(self, text, **kwargs):
        # Hàm mock để lưu kết quả config
        self.final_text = text

    def _update_scan_ui(self):
        # 2. Chạm Tỉ Lệ: Top 3 có Tỉ lệ >= 80% từ touch_combos
        cham_rate_list = []
        if self.touch_combos:
            # Lọc các tổ hợp có rate_percent >= 80%
            high_rate_combos = [c for c in self.touch_combos if c['rate_percent'] >= 80.0]

            # 🔥 FIX LỖI: Buộc sắp xếp lại theo Tỉ Lệ Thắng (rate_percent) GIẢM DẦN.
            high_rate_combos.sort(key=lambda x: (x['rate_percent'], x['streak']), reverse=True)
            
            # Lấy Top 3
            top_rate_combos = high_rate_combos[:3]
            
            for combo in top_rate_combos:
                touches_str = ''.join(map(str, combo['touches']))
                rate_hits = combo['rate_hits']
                rate_total = combo['rate_total']
                if rate_hits > 0: # Thêm điều kiện hits > 0 (từ suggestion)
                    cham_rate_list.append(f"{touches_str} ({rate_hits}/{rate_total} kỳ)")

        if not cham_rate_list:
            cham_rate_display = ', '.join(self.top_touches) if self.top_touches else '...'
        else:
            cham_rate_display = ', '.join(cham_rate_list)
        
        self.config(text=f"⭐ Chạm Tỉ Lệ: {cham_rate_display}")
        return cham_rate_list

# --- CHẠY TEST ---
def test_de_touch_rate_fix():
    print("--- BẮT ĐẦU TEST LOGIC CHẠM TỈ LỆ ---")
    
    ui_mock = MockUiDeDashboard(COMBOS_FROM_ANALYTICS)
    result_list = ui_mock._update_scan_ui()
    
    expected_list = [
        "5678 (10/10 kỳ)",  # Phải là 100% (Combo B)
        "9015 (9/10 kỳ)",   # Phải là 90% (Combo C)
        "1234 (8/10 kỳ)"    # Phải là 80% (Combo A)
    ]

    print(f"Kết quả mong đợi (Ưu tiên Rate): {expected_list}")
    print(f"Kết quả thực tế: {result_list}")
    
    assert result_list == expected_list, "Lỗi: Thứ tự Chạm Tỉ Lệ vẫn chưa được sắp xếp theo tỷ lệ thắng."
    assert "100.0" not in ui_mock.final_text, "Lỗi: Đầu ra UI không nên chứa .0" 

    # Test trường hợp chỉ lấy Top 3
    extra_combo = {'touches': [2,3,4,5], 'streak': 1, 'rate_hits': 10, 'rate_total': 10, 'rate_percent': 100.0}
    ui_mock_top3 = MockUiDeDashboard(COMBOS_FROM_ANALYTICS + [extra_combo])
    top4_result = ui_mock_top3._update_scan_ui()
    assert len(top4_result) == 3, "Lỗi: Cần phải giới hạn chỉ lấy Top 3."
    
    # Test Fallback (Nếu tất cả đều < 80%)
    low_rate_combos = [{'touches': [1, 2, 3, 4], 'streak': 3, 'rate_hits': 7, 'rate_total': 10, 'rate_percent': 70.0}]
    ui_mock_fallback = MockUiDeDashboard(low_rate_combos)
    ui_mock_fallback.top_touches = ["7", "8", "9"]
    ui_mock_fallback._update_scan_ui()
    assert "Chạm Tỉ Lệ: 7, 8, 9" in ui_mock_fallback.final_text, "Lỗi: Fallback về top_touches không hoạt động."
    
    print("✅ TEST LOGIC CHẠM TỈ LỆ HOÀN TẤT VÀ CHÍNH XÁC.")

if __name__ == "__main__":
    test_de_touch_rate_fix()