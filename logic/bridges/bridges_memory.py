# Đây là file mới: logic/bridges_memory.py

# Import các hàm hỗ trợ từ .bridges_classic
try:
    from .bridges_classic import taoSTL_V30_Bong
except ImportError:
    from bridges_classic import taoSTL_V30_Bong

# ===================================================================================
# I. ĐỊNH NGHĨA 27 VỊ TRÍ LÔ
# ===================================================================================

# Danh sách tên của 27 vị trí lô
_LOTO_POSITION_NAMES = [
    "Lô GĐB", "Lô G1",
    "Lô G2.1", "Lô G2.2",
    "Lô G3.1", "Lô G3.2", "Lô G3.3", "Lô G3.4", "Lô G3.5", "Lô G3.6",
    "Lô G4.1", "Lô G4.2", "Lô G4.3", "Lô G4.4",
    "Lô G5.1", "Lô G5.2", "Lô G5.3", "Lô G5.4", "Lô G5.5", "Lô G5.6",
    "Lô G6.1", "Lô G6.2", "Lô G6.3",
    "Lô G7.1", "Lô G7.2", "Lô G7.3", "Lô G7.4"
]

def get_27_loto_names():
    """Trả về danh sách 27 tên của các vị trí lô."""
    return _LOTO_POSITION_NAMES

def get_27_loto_positions(row):
    """
    (MỚI) Lấy 27 con lô (2 số cuối) từ 1 hàng dữ liệu DB.
    Trả về một danh sách 27 chuỗi (string) 2 chữ số.
    """
    lotos = []
    try:
        # 1. GĐB (row[2])
        lotos.append(str(row[2] or '0').strip()[-2:].zfill(2))
        # 2. G1 (row[3])
        lotos.append(str(row[3] or '0').strip()[-2:].zfill(2))
        
        # 3. G2 (row[4]) - 2 giải
        g2 = str(row[4] or ',').split(',')
        lotos.append(str(g2[0] or '0').strip()[-2:].zfill(2))
        lotos.append(str(g2[1] if len(g2) > 1 else '0').strip()[-2:].zfill(2))

        # 4. G3 (row[5]) - 6 giải
        g3 = str(row[5] or ',,,,,').split(',')
        for i in range(6):
            lotos.append(str(g3[i] if len(g3) > i else '0').strip()[-2:].zfill(2))

        # 5. G4 (row[6]) - 4 giải
        g4 = str(row[6] or ',,,').split(',')
        for i in range(4):
            lotos.append(str(g4[i] if len(g4) > i else '0').strip()[-2:].zfill(2))

        # 6. G5 (row[7]) - 6 giải
        g5 = str(row[7] or ',,,,,').split(',')
        for i in range(6):
            lotos.append(str(g5[i] if len(g5) > i else '0').strip()[-2:].zfill(2))
            
        # 7. G6 (row[8]) - 3 giải
        g6 = str(row[8] or ',,').split(',')
        for i in range(3):
            lotos.append(str(g6[i] if len(g6) > i else '0').strip()[-2:].zfill(2))
            
        # 8. G7 (row[9]) - 4 giải
        g7 = str(row[9] or ',,,').split(',')
        for i in range(4):
            lotos.append(str(g7[i] if len(g7) > i else '0').strip()[-2:].zfill(2))

        return lotos # Tổng 1+1+2+6+4+6+3+4 = 27
        
    except Exception as e:
        print(f"Lỗi get_27_loto_positions: {e}")
        return ["00"] * 27

# ===================================================================================
# II. ĐỊNH NGHĨA CÁC THUẬT TOÁN BẠC NHỚ
# ===================================================================================

def calculate_bridge_stl(loto_str_1, loto_str_2, algorithm_type):
    """
    (MỚI) Tính toán và trả về một cặp STL [lô, lộn]
    dựa trên 2 con lô đầu vào và 1 thuật toán.
    """
    try:
        loto1 = int(loto_str_1)
        loto2 = int(loto_str_2)
        btl = 0 # Lô Bạch Thủ
        
        if algorithm_type == 'sum':
            # 1. Thuật toán TỔNG
            btl = (loto1 + loto2) % 100
        elif algorithm_type == 'diff':
            # 2. Thuật toán HIỆU
            btl = abs(loto1 - loto2)
        else:
            return ['00', '00']
            
        btl_str = str(btl).zfill(2)
        
        # 3. Tạo STL (Lô và Lộn)
        # Kiểm tra xem có phải lô kép không
        if btl_str[0] == btl_str[1]:
            # Nếu là kép, dùng hàm taoSTL_V30_Bong để lấy bóng
            # (Hàm này đã xử lý kép -> kép, bóng kép)
            return taoSTL_V30_Bong(btl_str[0], btl_str[1])
        else:
            # Nếu không phải kép, trả về [lô, lộn]
            return [btl_str, btl_str[1] + btl_str[0]]
            
    except Exception as e:
        print(f"Lỗi calculate_bridge_stl: {e}")
        return ['00', '00']