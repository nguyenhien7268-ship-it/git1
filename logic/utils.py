import logging
import sys

def setup_logger(name="Logic"):
    """Cấu hình Logger đơn giản."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# ===================================================================================
# CẤU HÌNH VÀ HÀM HỖ TRỢ CỐT LÕI (V25 / V30)
# ===================================================================================

BONG_DUONG_V30 = {
    "0": "5",
    "1": "6",
    "2": "7",
    "3": "8",
    "4": "9",
    "5": "0",
    "6": "1",
    "7": "2",
    "8": "3",
    "9": "4",
}


def getBongDuong_V30(digit):
    return BONG_DUONG_V30.get(str(digit), str(digit))


def taoSTL_V30_Bong(a, b):
    strA, strB = str(a), str(b)
    if strA == strB:
        kep = f"{strA}{strB}".zfill(2)
        bongDigit = getBongDuong_V30(strA)
        bongKep = f"{bongDigit}{bongDigit}".zfill(2)
        return [kep, bongKep]
    else:
        lo1 = f"{strA}{strB}".zfill(2)
        lo2 = f"{strB}{strA}".zfill(2)
        return [lo1, lo2]


def getAllLoto_V30(row):
    """Lấy tất cả 27 loto từ 1 hàng DuLieu_AI (đã sắp xếp cột B->I)"""
    lotos = []
    try:
        # row[0]=MaSoKy, row[1]=Col_A_Ky
        lotos.append(str(row[2] or "0").strip()[-2:].zfill(2))  # GĐB (row[2])
        lotos.append(str(row[3] or "0").strip()[-2:].zfill(2))  # G1 (row[3])
        for i in range(4, 10):  # G2 (row[4]) -> G7 (row[9])
            if row[i]:
                for g in str(row[i]).split(","):
                    lotos.append(g.strip()[-2:].zfill(2))
    except Exception as e:
        print(f"Lỗi getAllLoto_V30: {e}")
        pass
    # (SỬA E741) Đổi 'l' thành 'loto'
    return [loto for loto in lotos if loto and len(loto) == 2 and loto.isdigit()]


def checkHitSet_V30_K2N(stlPair, lotoSet):
    """Kiểm tra 1 cặp STL [a,b] có trong 1 set loto hay không."""
    try:
        hit1 = stlPair[0] in lotoSet
        hit2 = stlPair[1] in lotoSet
        if hit1 and hit2:
            return "✅ (Ăn 2)"
        if hit1 or hit2:
            return "✅ (Ăn 1)"
        return "❌"
    except Exception:
        return "Lỗi check"
