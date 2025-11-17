# Tên file: du-an-backup/logic/bridges/bridges_classic.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - SỬA E741)
#
# ===================================================================================
# I. CẤU HÌNH VÀ HÀM HỖ TRỢ CỐT LÕI (V25)
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
    lotos = []
    try:
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


# ===================================================================================
# II. 15 HÀM LOGIC CẦU LÔ (A:I) (V5) - (Đã sửa lỗi lệch cột)
# ===================================================================================


def getCau1_STL_P5_V30_V5(row):
    try:
        gdb = str(row[2] or "00000").strip()
        de = gdb[-2:].zfill(2)
        a, b = int(de[0]), int(de[1])
        x, y = (a + 5) % 10, (b + 5) % 10
        return taoSTL_V30_Bong(x, y)
    except Exception:
        return ["00", "55"]


def getCau2_VT1_V30_V5(row):
    try:
        g6 = str(row[8] or ",,").split(",")
        g7 = str(row[9] or ",,,").split(",")
        a = (g6[2] if len(g6) > 2 else "0").strip()[-1:]
        b = (g7[3] if len(g7) > 3 else "0").strip()[-1:]
        return taoSTL_V30_Bong(a or "0", b or "0")
    except Exception:
        return ["00", "55"]


def getCau3_VT2_V30_V5(row):
    try:
        a = str(row[2] or "0").strip()[-1:]
        b = str(row[3] or "0").strip()[-1:]
        return taoSTL_V30_Bong(a or "0", b or "0")
    except Exception:
        return ["00", "55"]


def getCau4_VT3_V30_V5(row):
    try:
        a = str(row[2] or "00000").strip()[-2:-1]
        b = str(row[3] or "0").strip()[-1:]
        return taoSTL_V30_Bong(a or "0", b or "0")
    except Exception:
        return ["00", "55"]


def getCau5_TDB1_V30_V5(row):
    try:
        g7 = str(row[9] or ",,,").split(",")
        a = (g7[0] or "0").strip()[:1]
        b = (g7[3] if len(g7) > 3 else "0").strip()[-1:]
        return taoSTL_V30_Bong(a or "0", b or "0")
    except Exception:
        return ["00", "55"]


def getCau6_VT5_V30_V5(row):
    try:
        g7 = str(row[9] or ",,,").split(",")
        a = (g7[1] if len(g7) > 1 else "0").strip()[-1:]
        b = (g7[2] if len(g7) > 2 else "0").strip()[:1]
        return taoSTL_V30_Bong(a or "0", b or "0")
    except Exception:
        return ["00", "55"]


def getCau7_Moi1_V30_V5(row):
    try:
        g5 = str(row[7] or ",,,,,").split(",")
        g7 = str(row[9] or ",,,").split(",")
        a = (g5[0] or "0").strip()[:1]
        b = (g7[0] or "0").strip()[:1]
        return taoSTL_V30_Bong(a or "0", b or "0")
    except Exception:
        return ["00", "55"]


def getCau8_Moi2_V30_V5(row):
    try:
        g3 = str(row[5] or ",,,,,").split(",")
        g4 = str(row[6] or ",,,").split(",")
        a = (g3[0] or "0").strip()[:1]
        b = (g4[0] or "0").strip()[:1]
        return taoSTL_V30_Bong(a or "0", b or "0")
    except Exception:
        return ["00", "55"]


def getCau9_Moi3_V30_V5(row):
    try:
        a = str(row[2] or "0").strip()[:1]
        b = str(row[3] or "0").strip()[:1]
        return taoSTL_V30_Bong(a or "0", b or "0")
    except Exception:
        return ["00", "55"]


def getCau10_Moi4_V30_V5(row):
    try:
        g2 = str(row[4] or ",0").split(",")
        g3 = str(row[5] or ",,0").split(",")
        a = (g2[1] if len(g2) > 1 else "00").strip()[1:2]
        b = (g3[2] if len(g3) > 2 else "00000").strip()[-1:]
        return taoSTL_V30_Bong(a or "0", b or "0")
    except Exception:
        return ["00", "55"]


def getCau11_Moi5_V30_V5(row):
    try:
        gdb = str(row[2] or "00").strip()
        g3 = str(row[5] or ",0").split(",")
        a = gdb[1:2]
        b = (g3[1] if len(g3) > 1 else "00000").strip()[-1:]
        return taoSTL_V30_Bong(a or "0", b or "0")
    except Exception:
        return ["00", "55"]


def getCau12_Moi6_V30_V5(row):
    try:
        gdb = str(row[2] or "00000").strip()
        g3 = str(row[5] or ",,0").split(",")
        a = gdb[-1:]
        b = (g3[2] if len(g3) > 2 else "000").strip()[2:3]
        return taoSTL_V30_Bong(a or "0", b or "0")
    except Exception:
        return ["00", "55"]


def getCau13_G7_3_P8_V30_V5(row):
    try:
        g7 = str(row[9] or ",,0").split(",")
        baseNum = (g7[2] if len(g7) > 2 else "0").strip().zfill(2)
        a, b = int(baseNum[0]), int(baseNum[1])
        x, y = (a + 8) % 10, (b + 8) % 10
        return taoSTL_V30_Bong(x, y)
    except Exception:
        return ["00", "55"]


def getCau14_G1_P2_V30_V5(row):
    try:
        g1 = str(row[3] or "00").strip()
        baseNum = g1[-2:].zfill(2)
        a, b = int(baseNum[0]), int(baseNum[1])
        x, y = (a + 2) % 10, (b + 2) % 10
        return taoSTL_V30_Bong(x, y)
    except Exception:
        return ["00", "55"]


def getCau15_DE_P7_V30_V5(row):
    try:
        gdb = str(row[2] or "00000").strip()
        baseNum = gdb[-2:].zfill(2)
        a, b = int(baseNum[0]), int(baseNum[1])
        x, y = (a + 7) % 10, (b + 7) % 10
        return taoSTL_V30_Bong(x, y)
    except Exception:
        return ["00", "55"]


ALL_15_BRIDGE_FUNCTIONS_V5 = [
    getCau1_STL_P5_V30_V5,
    getCau2_VT1_V30_V5,
    getCau3_VT2_V30_V5,
    getCau4_VT3_V30_V5,
    getCau5_TDB1_V30_V5,
    getCau6_VT5_V30_V5,
    getCau7_Moi1_V30_V5,
    getCau8_Moi2_V30_V5,
    getCau9_Moi3_V30_V5,
    getCau10_Moi4_V30_V5,
    getCau11_Moi5_V30_V5,
    getCau12_Moi6_V30_V5,
    getCau13_G7_3_P8_V30_V5,
    getCau14_G1_P2_V30_V5,
    getCau15_DE_P7_V30_V5,
]

# --- Hàm Thống Kê Loto ---
# (Hàm này được analytics.py sử dụng, nhưng nó phụ thuộc nhiều vào
# getAllLoto_V30, vì vậy để nó ở đây là hợp lý)


def calculate_loto_stats(loto_list):
    dau_stats = {i: [] for i in range(10)}
    duoi_stats = {i: [] for i in range(10)}
    for loto in loto_list:
        if len(loto) == 2 and loto.isdigit():
            dau_int, duoi_int = int(loto[0]), int(loto[1])
            dau_stats[dau_int].append(loto[1])
            duoi_stats[duoi_int].append(loto[0])
    return dau_stats, duoi_stats