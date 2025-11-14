# ===================================================================================
# (GĐ 2) TÁI CẤU TRÚC FILE - KẾ THỪA TỪ BASE_BRIDGE
# ===================================================================================

# Import các lớp cơ sở và dịch vụ
from .base_bridge import BaseBridge
from ..data_service import DataService, global_data_service
from .. import utils # Import hàm utils chung (nếu cần)

# =HA_G2_HELPER_START===============================================================
# I. CẤU HÌNH VÀ HÀM HỖ TRỢ CỐT LÕI (V25 / V30)
# Các hàm này sẽ được chuyển thành phương thức private (_*) trong class
# ===================================================================================

BONG_DUONG_V30 = {
    '0': '5', '1': '6', '2': '7', '3': '8', '4': '9',
    '5': '0', '6': '1', '7': '2', '8': '3', '9': '4'
}

def _getBongDuong_V30(digit):
    return BONG_DUONG_V30.get(str(digit), str(digit))

def _taoSTL_V30_Bong(a, b):
    strA, strB = str(a), str(b)
    if strA == strB:
        kep = f"{strA}{strB}".zfill(2)
        bongDigit = _getBongDuong_V30(strA)
        bongKep = f"{bongDigit}{bongDigit}".zfill(2)
        return [kep, bongKep]
    else:
        lo1 = f"{strA}{strB}".zfill(2)
        lo2 = f"{strB}{strA}".zfill(2)
        return [lo1, lo2]

def _getAllLoto_V30_from_row(row_dict):
    """
    (SỬA GĐ 2) Lấy tất cả loto từ 1 hàng dữ liệu (dạng dict)
    từ DataService.
    """
    lotos = []
    try:
        # Sử dụng tên cột chuẩn (Col_B_GDB, Col_C_G1, ...)
        lotos.append(str(row_dict.get('Col_B_GDB') or '0').strip()[-2:].zfill(2)) # GĐB
        lotos.append(str(row_dict.get('Col_C_G1') or '0').strip()[-2:].zfill(2)) # G1
        
        # G2 (Col_D_G2) -> G7 (Col_I_G7)
        for col_name in ['Col_D_G2', 'Col_E_G3', 'Col_F_G4', 'Col_G_G5', 'Col_H_G6', 'Col_I_G7']:
            prize_data = row_dict.get(col_name)
            if prize_data:
                for g in str(prize_data).split(','):
                    lotos.append(g.strip()[-2:].zfill(2))
                    
    except Exception as e:
        print(f"Lỗi _getAllLoto_V30_from_row: {e}")
        pass 
    
    # Sử dụng hàm utils đã được kiểm thử (nếu có)
    return utils.clean_loto_list(lotos)

def _checkHitSet_V30_K2N(stlPair, lotoSet):
    """
    Kiểm tra xem cặp STL có trúng trong tập lotoSet hay không.
    Trả về số nháy (0, 1, hoặc 2)
    """
    try:
        hits = 0
        if stlPair[0] in lotoSet:
            hits += 1
        # Xử lý trường hợp kép (STL[0] == STL[1])
        if stlPair[0] != stlPair[1] and stlPair[1] in lotoSet:
            hits += 1
        return hits
    except Exception:
        return 0 # Lỗi -> coi như 0 nháy

# ===================================================================================
# II. 15 HÀM LOGIC CẦU LÔ (A:I) (V5) - (Đã sửa lỗi lệch cột)
# Các hàm này sẽ được gọi bởi lớp ClassicBridge
# (SỬA GĐ 2) Chuyển đổi để chấp nhận row_dict thay vì row (tuple)
# ===================================================================================

def _getCau1_STL_P5_V30_V5(row_dict):
    try:
        gdb = str(row_dict.get('Col_B_GDB') or '00000').strip()
        de = gdb[-2:].zfill(2)
        a, b = int(de[0]), int(de[1])
        x, y = (a + 5) % 10, (b + 5) % 10
        return _taoSTL_V30_Bong(x, y)
    except Exception: return ['00', '55']

def _getCau2_VT1_V30_V5(row_dict):
    try:
        g6 = str(row_dict.get('Col_H_G6') or ',,').split(',')
        g7 = str(row_dict.get('Col_I_G7') or ',,,').split(',')
        a = (g6[2] if len(g6) > 2 else '0').strip()[-1:]
        b = (g7[3] if len(g7) > 3 else '0').strip()[-1:]
        return _taoSTL_V30_Bong(a or '0', b or '0')
    except Exception: return ['00', '55']

def _getCau3_VT2_V30_V5(row_dict):
    try:
        a = str(row_dict.get('Col_B_GDB') or '0').strip()[-1:]
        b = str(row_dict.get('Col_C_G1') or '0').strip()[-1:]
        return _taoSTL_V30_Bong(a or '0', b or '0')
    except Exception: return ['00', '55']

def _getCau4_VT3_V30_V5(row_dict):
    try:
        a = str(row_dict.get('Col_B_GDB') or '00000').strip()[-2:-1]
        b = str(row_dict.get('Col_C_G1') or '0').strip()[-1:]
        return _taoSTL_V30_Bong(a or '0', b or '0')
    except Exception: return ['00', '55']

def _getCau5_TDB1_V30_V5(row_dict):
    try:
        g7 = str(row_dict.get('Col_I_G7') or ',,,').split(',')
        a = (g7[0] or '0').strip()[:1]
        b = (g7[3] if len(g7) > 3 else '0').strip()[-1:]
        return _taoSTL_V30_Bong(a or '0', b or '0')
    except Exception: return ['00', '55']

def _getCau6_VT5_V30_V5(row_dict):
    try:
        g7 = str(row_dict.get('Col_I_G7') or ',,,').split(',')
        a = (g7[1] if len(g7) > 1 else '0').strip()[-1:]
        b = (g7[2] if len(g7) > 2 else '0').strip()[:1]
        return _taoSTL_V30_Bong(a or '0', b or '0')
    except Exception: return ['00', '55']

def _getCau7_Moi1_V30_V5(row_dict):
    try:
        g5 = str(row_dict.get('Col_G_G5') or ',,,,,').split(',')
        g7 = str(row_dict.get('Col_I_G7') or ',,,').split(',')
        a = (g5[0] or '0').strip()[:1]
        b = (g7[0] or '0').strip()[:1]
        return _taoSTL_V30_Bong(a or '0', b or '0')
    except Exception: return ['00', '55']

def _getCau8_Moi2_V30_V5(row_dict):
    try:
        g3 = str(row_dict.get('Col_E_G3') or ',,,,,').split(',')
        g4 = str(row_dict.get('Col_F_G4') or ',,,').split(',')
        a = (g3[0] or '0').strip()[:1]
        b = (g4[0] or '0').strip()[:1]
        return _taoSTL_V30_Bong(a or '0', b or '0')
    except Exception: return ['00', '55']

def _getCau9_Moi3_V30_V5(row_dict):
    try:
        a = str(row_dict.get('Col_B_GDB') or '0').strip()[:1]
        b = str(row_dict.get('Col_C_G1') or '0').strip()[:1]
        return _taoSTL_V30_Bong(a or '0', b or '0')
    except Exception: return ['00', '55']

def _getCau10_Moi4_V30_V5(row_dict):
    try:
        g2 = str(row_dict.get('Col_D_G2') or ',0').split(',')
        g3 = str(row_dict.get('Col_E_G3') or ',,0').split(',')
        a = (g2[1] if len(g2) > 1 else '00').strip()[1:2]
        b = (g3[2] if len(g3) > 2 else '00000').strip()[-1:]
        return _taoSTL_V30_Bong(a or '0', b or '0')
    except Exception: return ['00', '55']

def _getCau11_Moi5_V30_V5(row_dict):
    try:
        gdb = str(row_dict.get('Col_B_GDB') or '00').strip()
        g3 = str(row_dict.get('Col_E_G3') or ',0').split(',')
        a = gdb[1:2]
        b = (g3[1] if len(g3) > 1 else '00000').strip()[-1:]
        return _taoSTL_V30_Bong(a or '0', b or '0')
    except Exception: return ['00', '55']

def _getCau12_Moi6_V30_V5(row_dict):
    try:
        gdb = str(row_dict.get('Col_B_GDB') or '00000').strip()
        g3 = str(row_dict.get('Col_E_G3') or ',,0').split(',')
        a = gdb[-1:] 
        b = (g3[2] if len(g3) > 2 else '000').strip()[2:3]
        return _taoSTL_V30_Bong(a or '0', b or '0')
    except Exception: return ['00', '55']

def _getCau13_G7_3_P8_V30_V5(row_dict):
    try:
        g7 = str(row_dict.get('Col_I_G7') or ',,0').split(',')
        baseNum = (g7[2] if len(g7) > 2 else '0').strip().zfill(2)
        a, b = int(baseNum[0]), int(baseNum[1])
        x, y = (a + 8) % 10, (b + 8) % 10
        return _taoSTL_V30_Bong(x, y)
    except Exception: return ['00', '55']

def _getCau14_G1_P2_V30_V5(row_dict):
    try:
        g1 = str(row_dict.get('Col_C_G1') or '00').strip()
        baseNum = g1[-2:].zfill(2)
        a, b = int(baseNum[0]), int(baseNum[1])
        x, y = (a + 2) % 10, (b + 2) % 10
        return _taoSTL_V30_Bong(x, y)
    except Exception: return ['00', '55']

def _getCau15_DE_P7_V30_V5(row_dict):
    try:
        gdb = str(row_dict.get('Col_B_GDB') or '00000').strip()
        baseNum = gdb[-2:].zfill(2)
        a, b = int(baseNum[0]), int(baseNum[1])
        x, y = (a + 7) % 10, (b + 7) % 10
        return _taoSTL_V30_Bong(x, y)
    except Exception: return ['00', '55']

# (SỬA GĐ 2) Ánh xạ ID cầu sang hàm logic
_ALL_15_BRIDGE_FUNCTIONS_MAP = {
    1: ("CĐ 1 (Đề P+5)", _getCau1_STL_P5_V30_V5),
    2: ("CĐ 2 (G6.3[1] + G7.4[1])", _getCau2_VT1_V30_V5),
    3: ("CĐ 3 (GĐB[4] + G1[4])", _getCau3_VT2_V30_V5),
    4: ("CĐ 4 (GĐB[3] + G1[4])", _getCau4_VT3_V30_V5),
    5: ("CĐ 5 (G7.1[0] + G7.4[1])", _getCau5_TDB1_V30_V5),
    6: ("CĐ 6 (G7.2[1] + G7.3[0])", _getCau6_VT5_V30_V5),
    7: ("CĐ 7 (G5.1[0] + G7.1[0])", _getCau7_Moi1_V30_V5),
    8: ("CĐ 8 (G3.1[0] + G4.1[0])", _getCau8_Moi2_V30_V5),
    9: ("CĐ 9 (GĐB[0] + G1[0])", _getCau9_Moi3_V30_V5),
    10: ("CĐ 10 (G2.2[1] + G3.3[4])", _getCau10_Moi4_V30_V5),
    11: ("CĐ 11 (GĐB[1] + G3.2[4])", _getCau11_Moi5_V30_V5),
    12: ("CĐ 12 (GĐB[4] + G3.3[2])", _getCau12_Moi6_V30_V5),
    13: ("CĐ 13 (G7.3 P+8)", _getCau13_G7_3_P8_V30_V5),
    14: ("CĐ 14 (G1 P+2)", _getCau14_G1_P2_V30_V5),
    15: ("CĐ 15 (Đề P+7)", _getCau15_DE_P7_V30_V5),
}

# ===================================================================================
# III. LỚP CẦU CỔ ĐIỂN (CLASSIC BRIDGE) (MỚI - GĐ 2)
# ===================================================================================

class ClassicBridge(BaseBridge):
    """
    (MỚI - GĐ 2) Lớp triển khai cho 15 Cầu Cổ Điển.
    Mỗi "thực thể" (instance) của lớp này đại diện cho MỘT trong 15 cầu đó.
    """

    def __init__(self, bridge_id):
        if bridge_id not in _ALL_15_BRIDGE_FUNCTIONS_MAP:
            raise ValueError(f"ID Cầu Cổ Điển không hợp lệ: {bridge_id}")
            
        self.bridge_id = bridge_id
        name, logic_func = _ALL_15_BRIDGE_FUNCTIONS_MAP[bridge_id]
        
        self._logic_func = logic_func # Hàm logic (ví dụ: _getCau1_STL_P5_V30_V5)
        
        # Khởi tạo BaseBridge (Hợp đồng)
        super().__init__(
            bridge_name=name,
            description=f"Cầu cổ điển (Classic) số {bridge_id}."
        )

    def get_bridge_name(self):
        return self._bridge_name

    def get_bridge_description(self):
        return self._description

    def calculate_predictions(self, data_service, historical_kys):
        """
        Tính toán dự đoán cho cầu này.
        Cầu cổ điển chỉ cần dữ liệu của 1 NGÀY TRƯỚC (latest_ky).
        """
        if not historical_kys:
            return [] # Không có dữ liệu lịch sử

        # Lấy ngày mới nhất từ danh sách lịch sử
        latest_ky = historical_kys[-1]
        row_dict = data_service.get_results_by_ky(latest_ky)
        
        if not row_dict:
            return [] # Không tìm thấy dữ liệu cho kỳ
            
        # Gọi hàm logic private tương ứng (ví dụ: _getCau1_STL_P5_V30_V5)
        stl_pair = self._logic_func(row_dict)
        
        if not stl_pair or len(stl_pair) != 2:
            return [] # Logic cầu thất bại

        prediction = {
            "number": f"{stl_pair[0]},{stl_pair[1]}", # Định dạng STL
            "source_bridge": self.get_bridge_name(),
            "details": f"Tính từ kỳ {latest_ky}"
        }
        return [prediction]

    def run_backtest(self, data_service, full_ky_list):
        """
        (MỚI - GĐ 2) Chạy backtest đầy đủ cho cầu này.
        """
        if not data_service or not full_ky_list:
            return {
                "bridge_name": self.get_bridge_name(),
                "error": "Không có dữ liệu để backtest."
            }

        win_history = [] # Lịch sử thắng/thua (True/False)
        hit_counts = [] # Lịch sử số nháy (0, 1, 2)
        total_predictions = 0
        total_wins = 0
        
        # Lặp qua TOÀN BỘ lịch sử (bỏ qua ngày đầu tiên vì không có
        # dữ liệu T-1 để tính)
        for i in range(1, len(full_ky_list)):
            ky_T_minus_1 = full_ky_list[i-1] # Dữ liệu ngày hôm trước (T-1)
            ky_T = full_ky_list[i]          # Dữ liệu ngày hôm nay (T)
            
            # 1. Lấy dữ liệu T-1
            row_dict_T_minus_1 = data_service.get_results_by_ky(ky_T_minus_1)
            
            # 2. Lấy dữ liệu T (chỉ để kiểm tra kết quả)
            row_dict_T = data_service.get_results_by_ky(ky_T)

            if not row_dict_T_minus_1 or not row_dict_T:
                continue # Bỏ qua nếu thiếu dữ liệu

            # 3. Tính dự đoán (STL) cho ngày T (dựa trên T-1)
            stl_pair = self._logic_func(row_dict_T_minus_1)
            if not stl_pair or len(stl_pair) != 2:
                continue # Bỏ qua nếu logic cầu không ra số
            
            total_predictions += 1

            # 4. Lấy danh sách loto thực tế của ngày T
            loto_set_T = set(_getAllLoto_V30_from_row(row_dict_T))
            if not loto_set_T:
                continue # Bỏ qua nếu ngày T không có loto

            # 5. Kiểm tra thắng/thua
            hits = _checkHitSet_V30_K2N(stl_pair, loto_set_T)
            
            hit_counts.append(hits)
            is_win = (hits > 0)
            win_history.append(is_win)
            if is_win:
                total_wins += 1

        # 6. Tính toán thống kê
        win_rate = (total_wins / total_predictions) if total_predictions > 0 else 0
        max_lose_streak = utils.calculate_max_lose_streak(win_history)

        return {
            "bridge_name": self.get_bridge_name(),
            "total_days": len(full_ky_list),
            "total_predictions": total_predictions,
            "total_wins": total_wins,
            "total_hits": sum(hit_counts),
            "win_rate": win_rate,
            "win_history": win_history, # List [True, False, ...]
            "max_lose_streak": max_lose_streak,
        }

# ===================================================================================
# IV. HÀM PUBLIC ĐỂ TẠO VÀ LẤY CÁC CẦU (MỚI - GĐ 2)
# BridgeManager sẽ gọi hàm này
# ===================================================================================

def get_all_classic_bridges():
    """
    (MỚI - GĐ 2) Tạo và trả về 15 thực thể (instance) của Cầu Cổ Điển.
    Đây là hàm mà BridgeManager sẽ sử dụng.
    """
    bridges = []
    for bridge_id in _ALL_15_BRIDGE_FUNCTIONS_MAP.keys():
        try:
            bridges.append(ClassicBridge(bridge_id))
        except ValueError as e:
            print(f"Lỗi khi tạo Cầu Cổ Điển ID {bridge_id}: {e}")
    return bridges

# ===================================================================================
# V. HÀM CŨ (ĐỂ TƯƠNG THÍCH NGƯỢC)
# Các hàm này không còn được khuyến nghị sử dụng
# ===================================================================================

# (Giữ lại hàm này nếu analytics.py vẫn gọi trực tiếp)
def calculate_loto_stats(loto_list):
    """(Giữ lại để tương thích ngược)"""
    dau_stats = {i: [] for i in range(10)} 
    duoi_stats = {i: [] for i in range(10)}
    
    # Đảm bảo loto_list đã được clean (loại bỏ loto lỗi)
    cleaned_list = utils.clean_loto_list(loto_list)
    
    for loto in cleaned_list:
        dau_int, duoi_int = int(loto[0]), int(loto[1])
        dau_stats[dau_int].append(loto[1])
        duoi_stats[duoi_int].append(loto[0])
    return dau_stats, duoi_stats

# (Hàm này đã được thay thế bằng _getAllLoto_V30_from_row và
# không nên được sử dụng bên ngoài file này nữa)
# def getAllLoto_V30(row):
#     ...