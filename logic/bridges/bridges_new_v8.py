# Tên file: code1/logic/bridges/bridges_new_v8.py
#
# (NỘI DUNG TỆP MỚI V8.0)
#
# File này chứa logic cho 6 cầu mới (Siêu Ngắn, Báo Trùng, và 4 cầu từ bảng)
# được tách thành 9 hàm cầu riêng biệt.
# ===================================================================

# --- HÀM HỖ TRỢ NỘI BỘ ---

BONG_DUONG_MAP = {0: 5, 1: 6, 2: 7, 3: 8, 4: 9, 5: 0, 6: 1, 7: 2, 8: 3, 9: 4}

def _get_digit(s, index):
    """Lấy 1 chữ số (int) tại vị trí (index) của 1 chuỗi/số an toàn."""
    try:
        s_cleaned = "".join(filter(str.isdigit, str(s)))
        return int(s_cleaned[index])
    except (IndexError, TypeError, ValueError, TypeError):
        return None

def _get_prize_number(prev_row, giai_index, num_index):
    """
    Lấy một số giải đầy đủ (string) từ mảng row của DB.
    GDB=2, G1=3, G2=4, G3=5, G4=6, G5=7, G6=8, G7=9
    """
    try:
        prize_str_list = str(prev_row[giai_index])
        numbers = prize_str_list.split(',')
        if num_index < len(numbers):
            return str(numbers[num_index]).strip()
        return None
    except Exception:
        return None

def _format_stl(a, b):
    """Định dạng 2 số thành 1 cặp STL (string list)."""
    if a is None or b is None:
        return None
    # Ghép và đảo
    return [f"{a}{b}".zfill(2), f"{b}{a}".zfill(2)]

def _get_bong_duong(n):
    """Lấy bóng dương của một số (int)."""
    try:
        return BONG_DUONG_MAP.get(int(n))
    except (ValueError, TypeError):
        return None

# ===================================================================
# LOGIC 1: CẦU SIÊU NGẮN (Tách thành 2 hàm cầu)
# ===================================================================

def _get_cau_1_inputs(prev_row):
    gdb_str = str(prev_row[2]) # Col_B_GDB
    g3_5_str = _get_prize_number(prev_row, 5, 4) # Giai 3 (index 5), số thứ 5 (index 4)

    tam_a = _get_digit(gdb_str, 2) # GDB[2] (vị trí thứ 3)
    
    d3 = _get_digit(gdb_str, 2)
    d4 = _get_digit(gdb_str, 3)
    d5 = _get_digit(gdb_str, 4)
    
    tam_b = None
    if all(x is not None for x in [d3, d4, d5]):
        tam_b = (d3 + d4 + d5) % 10 # Tổng 3 số cuối (hàng đơn vị)
        
    tam_c = _get_digit(g3_5_str, 2) # G3.5[2] (vị trí thứ 3)

    return tam_a, tam_b, tam_c

def cau_V8_1_SieuNgan_AB(prev_row):
    """(V8) Cầu 1a (Siêu Ngắn): Ghép Tam_A (GDB[2]) với Tam_B (Tổng 3 cuối GDB)"""
    try:
        tam_a, tam_b, _ = _get_cau_1_inputs(prev_row)
        return _format_stl(tam_a, tam_b)
    except Exception:
        return None

def cau_V8_1_SieuNgan_BC(prev_row):
    """(V8) Cầu 1b (Siêu Ngắn): Ghép Tam_B (Tổng 3 cuối GDB) với Tam_C (G3.5[2])"""
    try:
        _, tam_b, tam_c = _get_cau_1_inputs(prev_row)
        return _format_stl(tam_b, tam_c)
    except Exception:
        return None

# ===================================================================
# LOGIC 2: CẦU BÁO TRÙNG / CẦU TÂM + TỔNG ĐỀ (Tách thành 3 hàm cầu)
# ===================================================================

def _get_cau_2_inputs(prev_row):
    gdb_str = str(prev_row[2]) # Col_B_GDB
    g3_2_str = _get_prize_number(prev_row, 5, 1) # Giai 3 (index 5), số thứ 2 (index 1)
    g3_5_str = _get_prize_number(prev_row, 5, 4) # Giai 3 (index 5), số thứ 5 (index 4)

    tam_a = _get_digit(g3_5_str, 2) # Tâm G3.5[2]
    tam_b = _get_digit(g3_2_str, 2) # Tâm G3.2[2]

    d1 = _get_digit(gdb_str, 0)
    d2 = _get_digit(gdb_str, 1)
    
    tong_de = None
    if all(x is not None for x in [d1, d2]):
        tong_de = (d1 + d2) % 10 # Tổng 2 số đầu ĐB (hàng đơn vị)
        
    return tam_a, tam_b, tong_de

def cau_V8_2_BaoTrung_AB(prev_row):
    """(V8) Cầu 2a (Báo Trùng): Ghép Tam_A (G3.5[2]) với Tam_B (G3.2[2])"""
    try:
        tam_a, tam_b, _ = _get_cau_2_inputs(prev_row)
        return _format_stl(tam_a, tam_b)
    except Exception:
        return None

def cau_V8_2_BaoTrung_BC(prev_row):
    """(V8) Cầu 2b (Báo Trùng): Ghép Tam_B (G3.2[2]) với Tong_De (Tổng 2 đầu GDB)"""
    try:
        _, tam_b, tong_de = _get_cau_2_inputs(prev_row)
        return _format_stl(tam_b, tong_de)
    except Exception:
        return None

def cau_V8_2_BaoTrung_Kep(prev_row):
    """(V8) Cầu 2c (Báo Trùng): Logic Kép Báo Trùng (Điều kiện)"""
    try:
        tam_a, tam_b, tong_de = _get_cau_2_inputs(prev_row)
        
        inputs = [tam_a, tam_b, tong_de]
        if any(x is None for x in inputs):
            return None
            
        unique_inputs = set(inputs)
        
        # Điều kiện: CHỈ khi 3 số rút trích chỉ có 2 số riêng biệt
        if len(unique_inputs) == 2:
            kep_list = list(unique_inputs)
            # Trả về 1 cặp STL (2 lô kép)
            return [str(kep_list[0])*2, str(kep_list[1])*2]
            
        return None # Không thỏa điều kiện
    except Exception:
        return None

# ===================================================================
# LOGIC 3 (MỚI 1): Ghép Số Đầu ĐB và Giải_6_2
# ===================================================================
def cau_V8_3_GDB0_G6_2_1(prev_row):
    """(V8) Cầu Mới 1: Ghép ĐB[0] (vị trí 1) với Giải_6_2[1] (vị trí 2)"""
    try:
        gdb_str = str(prev_row[2]) # Col_B_GDB
        g6_2_str = _get_prize_number(prev_row, 8, 1) # Giai 6 (index 8), số thứ 2 (index 1)

        a = _get_digit(gdb_str, 0) # ĐB[0]
        b = _get_digit(g6_2_str, 1) # G6.2[1]
        
        return _format_stl(a, b)
    except Exception:
        return None

# ===================================================================
# LOGIC 4 (MỚI 2): Ghép Số Thứ 2 và Số Thứ 4 ĐB
# ===================================================================
def cau_V8_4_GDB1_GDB3(prev_row):
    """(V8) Cầu Mới 2: Ghép ĐB[1] (vị trí 2) với ĐB[3] (vị trí 4)"""
    try:
        gdb_str = str(prev_row[2]) # Col_B_GDB

        a = _get_digit(gdb_str, 1) # ĐB[1]
        b = _get_digit(gdb_str, 3) # ĐB[3]
        
        return _format_stl(a, b)
    except Exception:
        return None

# ===================================================================
# LOGIC 5 (MỚI 3): Ghép Số Đầu ĐB và Số Cuối Giải Nhất
# ===================================================================
def cau_V8_5_GDB0_G1_4(prev_row):
    """(V8) Cầu Mới 3: Ghép ĐB[0] (vị trí 1) với Giải_Nhất[4] (vị trí 5)"""
    try:
        gdb_str = str(prev_row[2]) # Col_B_GDB
        g1_str = str(prev_row[3]) # Col_C_G1

        a = _get_digit(gdb_str, 0) # ĐB[0]
        b = _get_digit(g1_str, 4) # G1[4]
        
        return _format_stl(a, b)
    except Exception:
        return None

# ===================================================================
# LOGIC 6 (MỚI 4): Ghép Tổng Bóng
# ===================================================================
def cau_V8_6_TongBong_GDB0_G1_0(prev_row):
    """(V8) Cầu Mới 4: Ghép A (Tổng GDB[0]+G1[0]) với B (Bóng Dương A)"""
    try:
        gdb_str = str(prev_row[2]) # Col_B_GDB
        g1_str = str(prev_row[3]) # Col_C_G1

        d1 = _get_digit(gdb_str, 0) # GDB[0]
        d2 = _get_digit(g1_str, 0) # G1[0]
        
        if d1 is None or d2 is None:
            return None
            
        a = (d1 + d2) % 10
        b = _get_bong_duong(a)
        
        return _format_stl(a, b)
    except Exception:
        return None