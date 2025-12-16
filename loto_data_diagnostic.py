import logging
import sys
from typing import List, Any

# ===================================================================================
# CÁC HÀM CẦN KIỂM TRA (Trích xuất từ utils.py)
# ===================================================================================

def getAllLoto_V30(row: List[Any]) -> List[str]:
    """Lấy tất cả 27 loto từ 1 hàng DuLieu_AI (đã sắp xếp cột B->I)"""
    lotos = []
    try:
        # row[0]=MaSoKy, row[1]=Col_A_Ky (Chúng ta chỉ quan tâm từ row[2] trở đi)
        
        # 1. Giải Đặc Biệt (GĐB) - row[2]
        lotos.append(str(row[2] or "0").strip()[-2:].zfill(2))
        
        # 2. Giải Nhất (G1) - row[3]
        lotos.append(str(row[3] or "0").strip()[-2:].zfill(2))
        
        # 3. Các giải còn lại (G2 đến G7) - row[4] đến row[9]
        for i in range(4, 10):
            if row[i]:
                # Giải có thể có nhiều số, cách nhau bởi dấu phẩy (Ví dụ: '1122,3344')
                for g in str(row[i]).split(","):
                    # Lấy 2 số cuối của từng giải và thêm vào danh sách
                    lotos.append(g.strip()[-2:].zfill(2))
        
        return lotos
        
    except Exception as e:
        print(f"❌ LỖI TRÍCH XUẤT DỮ LIỆU LÔ: {e}")
        return []

# ===================================================================================
# SCRIPT KIỂM TRA CHẨN ĐOÁN
# ===================================================================================

def run_data_diagnostic():
    """
    Chạy chẩn đoán để kiểm tra hàm trích xuất 27 con Lô có hoạt động đúng không.
    Sử dụng dữ liệu KQXS mô phỏng 27 giải.
    """
    print("====================================================================")
    print("🚀 CHẨN ĐOÁN: TẦNG TRÍCH XUẤT DỮ LIỆU LÔ (getAllLoto_V30)")
    print("====================================================================")
    
    # Dữ liệu KQXS Hà Nội 27 giải (Mô phỏng 1 hàng DuLieu_AI)
    # Cấu trúc: [KyID, Col_A, GĐB, G1, G2, G3, G4, G5, G6, G7]
    mock_row = [
        'Kỳ 12345',  # row[0] - KyID
        '2025-11-28', # row[1] - Col_A_Ky (Ngày)
        '87042',      # row[2] - GĐB (Lô: 42)
        '10031',      # row[3] - G1 (Lô: 31)
        '5566,7788',  # row[4] - G2 (Lô: 66, 88) - 2 giải
        '9900,1020,3040,5060,7080,9010', # row[5] - G3 (Lô: 00, 20, 40, 60, 80, 10) - 6 giải
        '2030,4050,6070,8090', # row[6] - G4 (Lô: 30, 50, 70, 90) - 4 giải
        '0001,2040,6080,9010,1112,3314', # row[7] - G5 (Lô: 01, 40, 80, 10, 12, 14) - 6 giải
        '55,66,77',   # row[8] - G6 (Lô: 55, 66, 77) - 3 giải
        '88,99,10,20' # row[9] - G7 (Lô: 88, 99, 10, 20) - 4 giải
        # TỔNG SỐ LÔ: 1 + 1 + 2 + 6 + 4 + 6 + 3 + 4 = 27 LÔ
    ]
    
    # 2. Chạy hàm kiểm tra
    extracted_lotos = getAllLoto_V30(mock_row)

    # 3. Kiểm tra kết quả
    expected_count = 27
    
    print(f"Tổng số Lô trích xuất được: {len(extracted_lotos)}")
    print(f"Danh sách Lô (5 số đầu): {extracted_lotos[:5]}")
    print(f"Danh sách Lô (5 số cuối): {extracted_lotos[-5:]}")
    
    if len(extracted_lotos) == expected_count:
        print("\n✅ KẾT QUẢ: HÀM TRÍCH XUẤT DỮ LIỆU LÔ HOẠT ĐỘNG CHÍNH XÁC (27/27 Lô).")
        print("   => Vấn đề nằm ở Tầng Quét Cầu (Scanner Logic).")
    elif len(extracted_lotos) == 0:
        print("\n❌ KẾT QUẢ: LỖI NGHIÊM TRỌNG (0 Lô). Có thể dữ liệu đầu vào bị sai định dạng.")
        print("   => Vấn đề nằm ở Tầng Utility (Chưa trích xuất được dữ liệu).")
    else:
        print(f"\n⚠️ KẾT QUẢ: LỖI SỐ LƯỢNG LÔ (Trích xuất: {len(extracted_lotos)}/{expected_count}).")
        print("   => Vấn đề nằm ở Tầng Utility (Hàm tách dữ liệu bị thiếu/sai logic).")

if __name__ == "__main__":
    run_data_diagnostic()