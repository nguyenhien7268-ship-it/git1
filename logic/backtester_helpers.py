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
    Parse K2N backtest results (Dynamic Row Detection).
    
    Args:
        results_data: List of rows from backtest result
        
    Returns:
        tuple: (cache_data_list, pending_k2n_dict)
    """
    cache_data_list = []
    pending_k2n_dict = {}

    if not results_data or len(results_data) < 2:
        print("Lỗi parse_k2n_results: Dữ liệu backtest K2N không hợp lệ.")
        return cache_data_list, pending_k2n_dict

    try:
        # 1. Xác định các hàng dựa trên tiêu đề cột đầu tiên (Cột A)
        headers = results_data[0]
        
        row_rates = None
        row_streaks = None
        row_recent = None
        row_prediction = None

        for row in results_data[1:]:
            first_col = str(row[0]).strip()
            if "Tỷ Lệ" in first_col:
                row_rates = row
            elif "Chuỗi" in first_col:
                row_streaks = row
            elif "Phong Độ" in first_col:
                row_recent = row
            elif "Kỳ" in first_col or "Next" in first_col:
                row_prediction = row

        # Nếu không tìm thấy, fallback về index cũ (nhưng rủi ro)
        if not row_rates and len(results_data) > 1: row_rates = results_data[1]
        if not row_streaks and len(results_data) > 2: row_streaks = results_data[2]
        if not row_recent and len(results_data) > 3: row_recent = results_data[3]
        if not row_prediction and len(results_data) > 4: row_prediction = results_data[4]

        num_bridges = len(headers) - 1

        for j in range(1, num_bridges + 1):
            bridge_name = str(headers[j]).split(" (")[0]

            # Lấy dữ liệu an toàn
            win_rate_text = str(row_rates[j]) if row_rates and j < len(row_rates) else "0"
            win_streak_text = str(row_streaks[j]) if row_streaks and j < len(row_streaks) else "0"
            recent_form_text = str(row_recent[j]) if row_recent and j < len(row_recent) else "0/10"
            pending_text = str(row_prediction[j]) if row_prediction and j < len(row_prediction) else ""

            # Parse current_streak and max_lose_streak
            current_streak = 0
            max_lose_streak = 0
            if "/" in win_streak_text:
                parts = win_streak_text.split("/")
                try:
                    part0 = parts[0].strip().replace("thắng", "").replace("thua", "").strip()
                    current_streak = int(part0)
                    if len(parts) > 1:
                        part1 = parts[1].strip().replace("thắng", "").replace("thua", "").strip()
                        max_lose_streak = int(part1)
                except (ValueError, IndexError):
                    current_streak = 0
                    max_lose_streak = 0
            else:
                try:
                    cleaned = win_streak_text.strip().replace("thắng", "").replace("thua", "").strip()
                    current_streak = int(cleaned)
                except ValueError:
                    current_streak = 0

            # Parse recent_win_count
            recent_win_count = 0
            try:
                if "/" in recent_form_text:
                    recent_win_count = int(recent_form_text.split("/")[0].strip())
                else:
                    recent_win_count = int(recent_form_text.strip())
            except (ValueError, IndexError):
                recent_win_count = 0

            # Clean STL for Cache
            clean_stl = pending_text.split("(")[0].strip() if "(" in pending_text else pending_text.strip()
            
            cache_data_list.append((
                win_rate_text,
                current_streak,
                clean_stl if clean_stl else "",
                max_lose_streak,
                recent_win_count,
                bridge_name
            ))

            # Lưu pending với logic mới: Xác định rõ là N1 hay N2
            if pending_text and pending_text.strip() != "":
                stl_only = clean_stl
                
                # Phát hiện trạng thái N2
                is_n2 = "N2" in pending_text or "chờ" in pending_text.lower()
                
                pending_k2n_dict[bridge_name] = {
                    "stl": stl_only,
                    "streak": current_streak,
                    "max_lose": max_lose_streak,
                    "is_n2": is_n2 # (MỚI) Cờ đánh dấu cầu đang chờ N2
                }

    except Exception as e:
        print(f"Lỗi parse_k2n_results: {e}")

    return cache_data_list, pending_k2n_dict