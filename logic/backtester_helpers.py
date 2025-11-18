"""
backtester_helpers.py - Helper and validation functions for backtesting

Extracted from backtester.py to improve maintainability.
Contains: Parameter validation, result parsing, utility functions.
"""


def validate_backtest_params(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra):
    """
    Validate backtest parameters and return processed values.
    
    Returns:
        tuple: (allData, finalEndRow, startCheckRow, offset, error_list)
               If error_list is not None, other values will be None.
    """
    if not all([toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra]):
        return None, None, None, None, [["LỖI:", "Cần đủ tham số."]]
    try:
        startRow, endRow = int(ky_bat_dau_kiem_tra), int(ky_ket_thuc_kiem_tra)
    except ValueError:
        return None, None, None, None, [["LỖI:", "Kỳ BĐ/KT phải là số."]]
    if not (startRow > 1 and startRow <= endRow):
        return None, None, None, None, [["LỖI:", "Kỳ BĐ/KT không hợp lệ."]]
    allData = toan_bo_A_I
    finalEndRow = min(endRow, len(allData) + startRow - 1)
    startCheckRow = startRow + 1
    if startCheckRow > finalEndRow:
        return None, None, None, None, [["LỖI:", "Dữ liệu không đủ để chạy."]]
    offset = startRow
    return allData, finalEndRow, startCheckRow, offset, None


def parse_k2n_results(results_data):
    """
    Parse K2N backtest results (4 rows format).
    
    Args:
        results_data: List of 4 rows [headers, rates, streaks, pending]
        
    Returns:
        tuple: (cache_data_list, pending_k2n_dict)
    """
    cache_data_list = []
    pending_k2n_dict = {}

    if not results_data or len(results_data) < 4:
        print("Lỗi parse_k2n_results: Dữ liệu backtest K2N không hợp lệ.")
        return cache_data_list, pending_k2n_dict

    try:
        headers = results_data[0]  # Hàng 0: Tên cầu
        rates = results_data[1]  # Hàng 1: Tỷ Lệ %
        streaks = results_data[2]  # Hàng 2: Chuỗi Thắng / Thua Max
        pending = results_data[3]  # Hàng 3: Dự đoán

        num_bridges = len(headers) - 1  # Trừ cột "Kỳ"

        for j in range(1, num_bridges + 1):
            bridge_name = str(headers[j]).split(" (")[0]  # Lấy tên gốc
            win_rate_text = str(rates[j]) if j < len(rates) else "0"
            win_streak_text = str(streaks[j]) if j < len(streaks) else "0"
            pending_text = str(pending[j]) if j < len(pending) else ""

            # Parse current_streak and max_lose_streak from win_streak_text
            # Format: "5" or "5 / 3" (win_streak / max_lose_streak)
            current_streak = 0
            max_lose_streak = 0
            if "/" in win_streak_text:
                parts = win_streak_text.split("/")
                try:
                    current_streak = int(parts[0].strip())
                    max_lose_streak = int(parts[1].strip()) if len(parts) > 1 else 0
                except (ValueError, IndexError):
                    current_streak = 0
                    max_lose_streak = 0
            else:
                try:
                    current_streak = int(win_streak_text.strip())
                except ValueError:
                    current_streak = 0

            # Append tuple with all 5 fields needed for SQL UPDATE
            # (win_rate_text, current_streak, next_prediction_stl, max_lose_streak_k2n, bridge_name)
            cache_data_list.append((
                win_rate_text,
                current_streak,
                pending_text if pending_text.strip() else "",
                max_lose_streak,
                bridge_name
            ))

            # Lưu pending với đầy đủ thông tin
            if pending_text and pending_text.strip() != "":
                pending_k2n_dict[bridge_name] = {
                    "stl": pending_text,
                    "streak": current_streak,
                    "max_lose": max_lose_streak
                }

    except Exception as e:
        print(f"Lỗi parse_k2n_results: {e}")

    return cache_data_list, pending_k2n_dict
