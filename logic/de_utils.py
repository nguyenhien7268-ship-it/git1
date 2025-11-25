import datetime

# --- 1. ĐỊNH NGHĨA DỮ LIỆU CƠ BẢN ---
# Các bộ số đề cơ bản (Dùng để phân tích Gan/Tần suất)
BO_SO_DE = {
    "01": ["01", "06", "10", "15", "51", "60", "56", "65"],
    "02": ["02", "07", "20", "70", "25", "52", "57", "75"],
    "03": ["03", "08", "30", "80", "35", "53", "58", "85"],
    "04": ["04", "09", "40", "90", "45", "54", "59", "95"],
    "12": ["12", "21", "17", "71", "26", "62", "67", "76"],
    "13": ["13", "31", "18", "81", "36", "63", "68", "86"],
    "14": ["14", "41", "19", "91", "46", "64", "69", "96"],
    "23": ["23", "32", "28", "82", "37", "73", "78", "87"],
    "24": ["24", "42", "29", "92", "47", "74", "79", "97"],
    "34": ["34", "43", "39", "93", "48", "84", "89", "98"],
    "00": ["00", "05", "50", "55"],
    "11": ["11", "16", "61", "66"],
    "22": ["22", "27", "72", "77"],
    "33": ["33", "38", "83", "88"],
    "44": ["44", "49", "94", "99"]
}

# --- 2. CÔNG CỤ XỬ LÝ SỐ ---

def get_gdb_last_2(row_data):
    """
    Trích xuất 2 số cuối Giải Đặc Biệt từ dòng dữ liệu thô.
    Return: string 'XY' hoặc None
    """
    try:
        # Giả định cấu trúc row: [date, ky_id, gdb, g1, g2...]
        if len(row_data) < 3:
            return None
        gdb = str(row_data[2])
        # Làm sạch chuỗi (xóa khoảng trắng, ký tự lạ)
        gdb = ''.join(filter(str.isdigit, gdb))
        if not gdb or len(gdb) < 2:
            return None
        return gdb[-2:]
    except Exception:
        return None

def check_cham(so_de_str, cham_list):
    """Kiểm tra số đề có dính chạm không"""
    if not so_de_str or len(so_de_str) < 2: return False
    try:
        n1, n2 = int(so_de_str[0]), int(so_de_str[1])
        for c in cham_list:
            c_int = int(c)
            if c_int == n1 or c_int == n2:
                return True
    except ValueError:
        return False
    return False

def check_tong(so_de_str, tong_list):
    """Kiểm tra số đề có thuộc tổng không"""
    if not so_de_str or len(so_de_str) < 2: return False
    try:
        n1, n2 = int(so_de_str[0]), int(so_de_str[1])
        tong = (n1 + n2) % 10
        for t in tong_list:
            if int(t) == tong:
                return True
    except ValueError:
        return False
    return False

# --- 3. ADAPTER (QUAN TRỌNG: ĐỂ DÙNG KÉ BACKTESTER CŨ) ---

def convert_data_for_de_backtest(all_data_ai):
    """
    Biến đổi dữ liệu Lô thành dữ liệu chỉ có Đề để chạy Backtest.
    Cấu trúc trả về vẫn giống Lô (đủ các cột giải), nhưng toàn bộ các giải
    đều được lấp đầy bằng số Đề (2 số cuối GĐB).
    """
    de_data = []
    for row in all_data_ai:
        gdb_tail = get_gdb_last_2(row)
        if gdb_tail:
            # Lấy phần Header (Date, ID)
            header = row[:2]
            # Tạo phần giải thưởng giả lập: 27 giải đều là số Đề
            prizes = tuple([gdb_tail] * 27)
            # Kết hợp lại
            fake_row = header + prizes
            de_data.append(fake_row)
        else:
            # Giữ nguyên dòng lỗi để không lệch index
            de_data.append(row) 
    return de_data
