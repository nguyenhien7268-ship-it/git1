import datetime

# --- 1. ĐỊNH NGHĨA DỮ LIỆU CƠ BẢN ---
# Các bộ số đề cơ bản (Mapping từ Tên Bộ -> Danh sách số)
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

# Bóng dương: 0->5, 1->6...
BONG_DUONG_MAP = {0: 5, 1: 6, 2: 7, 3: 8, 4: 9, 5: 0, 6: 1, 7: 2, 8: 3, 9: 4}

# --- 2. CÔNG CỤ XỬ LÝ SỐ ---

def get_gdb_last_2(row_data):
    """Trích xuất 2 số cuối Giải Đặc Biệt."""
    try:
        if len(row_data) < 3: return None
        gdb = str(row_data[2])
        gdb = ''.join(filter(str.isdigit, gdb))
        if not gdb or len(gdb) < 2: return None
        return gdb[-2:]
    except Exception: return None

def check_cham(so_de_str, cham_list):
    """Kiểm tra số đề có dính chạm không."""
    if not so_de_str or len(so_de_str) < 2: return False
    try:
        n1, n2 = int(so_de_str[0]), int(so_de_str[1])
        for c in cham_list:
            if int(c) == n1 or int(c) == n2: return True
    except ValueError: return False
    return False

def check_tong(so_de_str, tong_list):
    """Kiểm tra số đề có thuộc tổng không."""
    if not so_de_str or len(so_de_str) < 2: return False
    try:
        n1, n2 = int(so_de_str[0]), int(so_de_str[1])
        tong = (n1 + n2) % 10
        for t in tong_list:
            if int(t) == tong: return True
    except ValueError: return False
    return False

# --- 3. LOGIC THÔNG MINH MỚI (STRICT MODE & V77 UTILS) ---

def get_bo_name_by_pair(n1, n2):
    """(V77) Tìm tên bộ số từ 2 số bất kỳ (ghép lại)."""
    pair_str = f"{n1}{n2}"
    for bo_name, nums in BO_SO_DE.items():
        if pair_str in nums: return bo_name
    return None

def get_touches_by_offset(base_val, k, logic_type="TONG"):
    """
    (V77) Sinh 4 chạm dựa trên số gốc và độ lệch K.
    logic_type: "TONG" (Biến thiên) hoặc "VITRI" (Cố định).
    """
    touches = set()
    if logic_type == "TONG":
        # Công thức: (Gốc + K) và (Gốc + K + 1)
        v1 = (base_val + k) % 10
        v2 = (base_val + k + 1) % 10
        touches.update([v1, (v1+5)%10, v2, (v2+5)%10])
    else:
        # Logic Vị trí: Lấy thẳng giá trị + bóng
        v = (base_val + k) % 10
        touches.update([v, (v+5)%10])
    return sorted(list(touches))

def get_4_touches_smart(numbers_list):
    """
    (Giữ nguyên Logic cũ) Từ danh sách hạt giống trả về Chạm (Gốc + Bóng).
    """
    touches = set()
    base_nums = [n % 10 for n in numbers_list]
    for n in base_nums:
        touches.add(n)
    
    current_touches = list(touches)
    for t in current_touches:
        touches.add(BONG_DUONG_MAP.get(t, (t+5)%10))
            
    return sorted(list(touches))

def generate_dan_de_from_touches(touch_list, bo_filter_seeds=None):
    """
    (Giữ nguyên Logic cũ) Tạo dàn đề từ list chạm và lọc bằng Bộ (Set).
    """
    full_dan = set()
    for i in range(100):
        s = f"{i:02d}"
        d1, d2 = int(s[0]), int(s[1])
        if d1 in touch_list or d2 in touch_list:
            full_dan.add(s)
            
    if not bo_filter_seeds:
        return sorted(list(full_dan))
        
    valid_bo_nums = set()
    seeds = [n % 10 for n in bo_filter_seeds]
    
    pairs_formed = set()
    for i in range(len(seeds)):
        for j in range(len(seeds)): 
            p1 = f"{seeds[i]}{seeds[j]}"
            pairs_formed.add(p1)

    for pair in pairs_formed:
        for bo_name, bo_values in BO_SO_DE.items():
            if pair in bo_values:
                valid_bo_nums.update(bo_values)
                break
    
    if not valid_bo_nums:
        return sorted(list(full_dan))

    final_dan = full_dan.intersection(valid_bo_nums)
    return sorted(list(final_dan))

# --- 4. ADAPTER ---
def convert_data_for_de_backtest(all_data_ai):
    de_data = []
    for row in all_data_ai:
        gdb_tail = get_gdb_last_2(row)
        if gdb_tail:
            header = row[:2]
            prizes = tuple([gdb_tail] * 27)
            fake_row = header + prizes
            de_data.append(fake_row)
        else:
            de_data.append(row) 
    return de_data