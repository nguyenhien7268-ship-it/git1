import re

# Import các hàm hỗ trợ từ .bridges_classic
try:
    # (MỚI) Thêm BONG_DUONG_V30 vào import
    from .bridges_classic import getAllLoto_V30, taoSTL_V30_Bong, BONG_DUONG_V30
except ImportError:
    # Fallback
    try:
        from bridges_classic import getAllLoto_V30, taoSTL_V30_Bong, BONG_DUONG_V30
    except ImportError:
        print("Lỗi: Không thể import bridges_classic trong bridges_v16.py")
        def getAllLoto_V30(r): return []
        def taoSTL_V30_Bong(a, b): return ['00', '00']
        BONG_DUONG_V30 = {} # Giả lập

# ===================================================================================
# V. HÀM CÔNG KHAI: DÒ CẦU & TEST CẦU (V16)
# ===================================================================================

def getDigits_V16(s):
    if not s: return []
    return [int(d) for d in str(s) if d.isdigit()]

def getAllPositions_V16(row):
    positions = []
    try:
        positions.extend(getDigits_V16(str(row[2] or '0').strip().zfill(5))) # GĐB (row[2])
        positions.extend(getDigits_V16(str(row[3] or '0').strip().zfill(5))) # G1 (row[3])
        g2 = str(row[4] or '').split(',') # G2
        for g in g2: positions.extend(getDigits_V16(g.strip().zfill(5)))
        while len(positions) < 20: positions.append(None)
        g3 = str(row[5] or '').split(',') # G3
        for g in g3: positions.extend(getDigits_V16(g.strip().zfill(5)))
        while len(positions) < 50: positions.append(None)
        g4 = str(row[6] or '').split(',') # G4
        for g in g4: positions.extend(getDigits_V16(g.strip().zfill(4)))
        while len(positions) < 66: positions.append(None)
        g5 = str(row[7] or '').split(',') # G5
        for g in g5: positions.extend(getDigits_V16(g.strip().zfill(4)))
        while len(positions) < 90: positions.append(None)
        g6 = str(row[8] or '').split(',') # G6
        for g in g6: positions.extend(getDigits_V16(g.strip().zfill(3)))
        while len(positions) < 99: positions.append(None)
        g7 = str(row[9] or '').split(',') # G7
        for g in g7: positions.extend(getDigits_V16(g.strip().zfill(2)))
        while len(positions) < 107: positions.append(None)
        return positions[:107]
    except Exception as e:
        print(f"Lỗi getAllPositions_V16: {e}")
        return [None] * 107

def getPositionName_V16(index):
    if index < 0 or index > 106: return "NULL"
    if index < 5: return f"GDB[{index}]"
    if index < 10: return f"G1[{index - 5}]"
    if index < 20: return f"G2.{(index - 10) // 5 + 1}[{(index - 10) % 5}]"
    if index < 50: return f"G3.{(index - 20) // 5 + 1}[{(index - 20) % 5}]"
    if index < 66: return f"G4.{(index - 50) // 4 + 1}[{(index - 50) % 4}]"
    if index < 90: return f"G5.{(index - 66) // 4 + 1}[{(index - 66) % 4}]"
    if index < 99: return f"G6.{(index - 90) // 3 + 1}[{(index - 90) % 3}]"
    if index < 107: return f"G7.{(index - 99) // 2 + 1}[{(index - 99) % 2}]"
    return "ERROR"

def get_index_from_name_V16(name_str):
    """
    (MỚI - CẬP NHẬT) Hàm này đã được nâng cấp để hiểu tên V17.
    Nó có thể phân tích "GDB[0]" (trả về 0) và "Bong(GDB[0])" (trả về 107).
    """
    processed_name = name_str.strip()
    is_bong = False
    
    # 1. Kiểm tra xem có phải cầu bóng không
    if processed_name.startswith("Bong(") and processed_name.endswith(")"):
        is_bong = True
        # Lấy phần tên gốc bên trong, ví dụ: "Bong(GDB[0])" -> "GDB[0]"
        processed_name = processed_name[5:-1].strip()

    # 2. Phân tích tên gốc
    match = re.match(r'(G\d+|GDB)\.?(\d+)?\[(\d+)\]', processed_name)
    if not match:
        print(f"Lỗi regex: Không thể phân tích '{name_str}'")
        return None
        
    g_name, g_num, g_idx = match.groups()
    base_index = None
    
    try:
        g_num = int(g_num) if g_num else 1
        g_idx = int(g_idx)
        
        if g_name == "GDB":
            if 0 <= g_idx <= 4: base_index = g_idx
        elif g_name == "G1":
            if 0 <= g_idx <= 4: base_index = 5 + g_idx
        elif g_name == "G2":
            if 1 <= g_num <= 2 and 0 <= g_idx <= 4: base_index = 10 + (g_num - 1) * 5 + g_idx
        elif g_name == "G3":
            if 1 <= g_num <= 6 and 0 <= g_idx <= 4: base_index = 20 + (g_num - 1) * 5 + g_idx
        elif g_name == "G4":
            if 1 <= g_num <= 4 and 0 <= g_idx <= 3: base_index = 50 + (g_num - 1) * 4 + g_idx
        elif g_name == "G5":
            if 1 <= g_num <= 6 and 0 <= g_idx <= 3: base_index = 66 + (g_num - 1) * 4 + g_idx
        elif g_name == "G6":
            if 1 <= g_num <= 3 and 0 <= g_idx <= 2: base_index = 90 + (g_num - 1) * 3 + g_idx
        elif g_name == "G7":
            if 1 <= g_num <= 4 and 0 <= g_idx <= 1: base_index = 99 + (g_num - 1) * 2 + g_idx
        
        if base_index is None:
            print(f"Lỗi logic: Tên cầu không hợp lệ '{name_str}'")
            return None
            
        # 3. Trả về chỉ số cuối cùng
        if is_bong:
            return base_index + 107 # Trả về chỉ số trong dải bóng (107-213)
        else:
            return base_index # Trả về chỉ số gốc (0-106)
            
    except Exception as e:
        print(f"Lỗi get_index_from_name_V16: {e}")
        return None

# ===================================================================================
# (MỚI) HÀM MỞ RỘNG V17 - (Thêm 107 vị trí Bóng)
# ===================================================================================

def getAllPositions_V17_Shadow(row):
    """
    (MỚI) Lấy 214 vị trí = 107 vị trí gốc + 107 vị trí bóng.
    """
    # 1. Lấy 107 vị trí gốc (dùng hàm đã có)
    positions_goc = getAllPositions_V16(row)
    
    # 2. Tạo 107 vị trí bóng
    positions_bong = []
    for digit in positions_goc:
        if digit is None:
            positions_bong.append(None)
        else:
            try:
                # Chuyển số (int) về chuỗi (str) để tra cứu bóng
                bong_digit_str = BONG_DUONG_V30.get(str(digit), str(digit))
                positions_bong.append(int(bong_digit_str))
            except Exception:
                positions_bong.append(None)
                
    # 3. Nối hai danh sách lại
    positions_goc.extend(positions_bong)
    return positions_goc # Trả về danh sách 214 vị trí

def getPositionName_V17_Shadow(index):
    """
    (MỚI) Lấy tên của vị trí trong 214 vị trí.
    """
    if index < 0 or index > 213: return "NULL"
    
    if index < 107:
        # 0-106 là vị trí gốc
        return getPositionName_V16(index) # Dùng hàm đã có
    else:
        # 107-213 là vị trí bóng
        index_goc = index - 107
        name_goc = getPositionName_V16(index_goc)
        return f"Bong({name_goc})"