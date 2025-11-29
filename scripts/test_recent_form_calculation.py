# test_recent_form_calculation.py - Fix ModuleNotFoundError và Assertion

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# -------------------------------------------------------------------
# --- FIX LỖI IMPORT: Đảm bảo thư mục chứa gói 'logic' được tìm thấy ---
# -------------------------------------------------------------------
# Lấy thư mục gốc của project (ví dụ: C:\Users\KAKA\Documents\27loto\CODE5\git1)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Đi lên một cấp từ thư mục 'tests' để có được thư mục gốc của project
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# -------------------------------------------------------------------


# Import hàm cần kiểm tra (Bây giờ sẽ tìm thấy 'logic' vì đã sửa đường dẫn)
from logic.backtester_core import BACKTEST_MANAGED_BRIDGES_K2N 


# =============================================================================
# CÁC HÀM MOCK ĐỂ CÔ LẬP BACKTEST ENGINE
# =============================================================================

# Dữ liệu giả định cho 10 kỳ backtest
MOCK_END_ROW = 19
MOCK_START_ROW = 10
MOCK_OFFSET = 0
MOCK_ALL_DATA = [
    [i for i in range(100)], # Dòng tiêu đề giả
    *[[f'25112903{i}', '12345', '1234', '123', '12', '1', '0', '0', '0', '1'] for i in range(1, 20)], # 19 dòng dữ liệu giả, mỗi dòng có 10 phần tử
]
MOCK_BRIDGES = [{'name': 'TestBridge_1', 'pos1_idx': 0, 'pos2_idx': 1}]

def mock_validate_params(data, start, end):
    """Giả lập _validate_backtest_params trả về dữ liệu lịch sử được kiểm soát."""
    return MOCK_ALL_DATA, MOCK_END_ROW, MOCK_START_ROW, MOCK_OFFSET, None

def mock_get_all_managed_bridges(db_name, only_enabled):
    """Giả lập việc tải danh sách cầu."""
    return MOCK_BRIDGES

def mock_get_all_loto_v30(row):
    """Giả lập việc trích xuất tập Loto."""
    return [str(row[0])[-2:]]

# Dãy kết quả Hit (Win/Loss) mong muốn trong 10 kỳ: 5 lần thắng
# PHẢI CHỨA TỪ "Ăn" để code production (đã sửa) đếm được.
HIT_SEQUENCE_RETURN = ['✅ (Ăn N1)', '❌ (Trượt)', '✅ (Ăn N1)', '❌ (Trượt)', '✅ (Ăn N1)', '❌ (Trượt)', '✅ (Ăn N1)', '❌ (Trượt)', '✅ (Ăn N1)', '❌ (Trượt)'] 
hit_sequence_iterator = iter(HIT_SEQUENCE_RETURN)

def mock_check_hit_set(pred, loto_set):
    """Buộc kết quả Hit/Miss theo thứ tự đã định nghĩa."""
    global hit_sequence_iterator
    try:
        # Lấy kết quả tiếp theo từ iterator
        result = next(hit_sequence_iterator)
        return result
    except StopIteration:
        return '❌ (Trượt)' 

# Các hàm Mock cần thiết để tránh lỗi runtime (không quan trọng cho logic này)
def mock_get_positions(row): return [1, 2, 3]
def mock_get_lotos(row): return ['11', '22']
def mock_tao_stl(a, b): return ['11', '22']


# =============================================================================
# LỚP KIỂM THỬ SỬ DỤNG UNTEST.MOCK
# =============================================================================

class TestRecentFormCalculation(unittest.TestCase):
    
    @patch('logic.backtester_core._validate_backtest_params', return_value=(MOCK_ALL_DATA, MOCK_END_ROW, MOCK_START_ROW, MOCK_OFFSET, None))
    @patch('logic.backtester_core.get_all_managed_bridges', side_effect=mock_get_all_managed_bridges)
    @patch('logic.backtester_core.getAllLoto_V30', side_effect=mock_get_all_loto_v30)
    @patch('logic.backtester_core.checkHitSet_V30_K2N', side_effect=mock_check_hit_set)
    @patch('logic.backtester_core.getAllPositions_V17_Shadow', side_effect=mock_get_positions)
    @patch('logic.backtester_core.get_27_loto_positions', side_effect=mock_get_lotos)
    @patch('logic.backtester_core.taoSTL_V30_Bong', side_effect=mock_tao_stl)
    def test_recent_form_calculation_is_correct(self, mock_validate, *args):
        """Kiểm tra xem Phong Độ 10 Kỳ có tính toán đúng 5/10 không."""
        
        # 1. Reset iterator cho mỗi lần chạy test
        global hit_sequence_iterator
        hit_sequence_iterator = iter(HIT_SEQUENCE_RETURN)
        
        # 2. Chạy hàm backtest
        results = BACKTEST_MANAGED_BRIDGES_K2N(
            toan_bo_A_I=MagicMock(), 
            ky_bat_dau_kiem_tra=MOCK_START_ROW, 
            ky_ket_thuc_kiem_tra=MOCK_END_ROW,
            history=True
        )
        
        # 3. Định vị hàng Phong Độ 10 Kỳ
        recent_form_row = results[3] 
        
        # 4. Khẳng định kết quả
        expected_recent_form = "5/10"
        actual_recent_form = recent_form_row[1]
        
        self.assertEqual(recent_form_row[0], "Phong Độ 10 Kỳ", "Lỗi cấu trúc: Hàng 3 không phải là Phong Độ 10 Kỳ")
        self.assertEqual(actual_recent_form, expected_recent_form, 
            f"Lỗi tính toán Phong Độ 10 Kỳ. Thực tế: {actual_recent_form}, Mong đợi: {expected_recent_form}.")
        
        # Kiểm tra xem có 10 dòng lịch sử chi tiết được trả về không
        history_rows = results[5:]
        self.assertEqual(len(history_rows), 10, f"Số lượng kỳ lịch sử trả về không đúng (Thực tế: {len(history_rows)})")

if __name__ == '__main__':
    unittest.main()