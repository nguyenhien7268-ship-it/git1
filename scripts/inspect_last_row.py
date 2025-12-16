import sys
import os
import sqlite3

# Setup đường dẫn
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

try:
    # [FIX] Import DB_NAME từ db_manager và get_all_data_ai từ data_repository
    from logic.db_manager import DB_NAME
    from logic.data_repository import get_all_data_ai
    from logic.bridges.bridges_v16 import getAllPositions_V17_Shadow, getPositionName_V17_Shadow
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    sys.exit(1)

def inspect_data():
    print("🔍 BẮT ĐẦU KIỂM TRA DỮ LIỆU KỲ MỚI NHẤT...")
    
    if not os.path.exists(DB_NAME):
        print(f"❌ Không tìm thấy DB: {DB_NAME}")
        return

    # 1. Lấy dữ liệu thô
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM DuLieu_AI ORDER BY MaSoKy DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        print("❌ Database rỗng!")
        return

    # Row structure: MaSoKy, Ky, GDB, G1, G2, G3, G4, G5, G6, G7
    print(f"\n📅 KỲ MỚI NHẤT: {row[1]}")
    print("-" * 50)
    
    columns = ["MaSoKy", "Ky", "GDB", "G1", "G2", "G3", "G4", "G5", "G6", "G7"]
    raw_values = list(row)
    
    # In dữ liệu thô để mắt thường nhìn
    for i, val in enumerate(raw_values):
        col_name = columns[i] if i < len(columns) else f"Col_{i}"
        print(f"{col_name:<10}: {val}")
        
        # Cảnh báo nếu chuỗi quá ngắn (Dữ liệu bị thiếu)
        if i >= 2 and isinstance(val, str): # Bỏ qua MaSoKy, Ky
            clean_val = val.replace("-", "").replace(" ", "").replace(",", "")
            # G3 thường có 6 giải x 5 số = 30 số. Nếu ít hơn nhiều là lỗi.
            if col_name == "G3" and len(clean_val) < 25:
                print(f"   ⚠️ CẢNH BÁO: G3 quá ngắn ({len(clean_val)} ký tự). Có thể thiếu giải.")
            if col_name == "G4" and len(clean_val) < 15: # 4 giải x 4 số = 16
                print(f"   ⚠️ CẢNH BÁO: G4 quá ngắn ({len(clean_val)} ký tự).")

    print("-" * 50)
    
    # 2. Kiểm tra việc phân tách Vị Trí (Parsing)
    print("⚙️ TEST PHÂN TÁCH VỊ TRÍ (V17):")
    try:
        # Giả lập row cho hàm V17 (Hàm này thường cần list values)
        positions = getAllPositions_V17_Shadow(raw_values)
        
        # Đếm số lượng vị trí lấy được
        valid_count = sum(1 for p in positions if p is not None and p != "")
        total_count = len(positions)
        
        print(f"✅ Đã tách được: {valid_count}/{total_count} vị trí.")
        
        if valid_count < total_count:
            print("\n❌ CÁC VỊ TRÍ BỊ LỖI (NULL/EMPTY) - GÂY RA N/A:")
            error_count = 0
            for idx, val in enumerate(positions):
                if not val:
                    name = getPositionName_V17_Shadow(idx)
                    print(f"   - Index {idx} ({name}): TRỐNG")
                    error_count += 1
                    if error_count >= 10:
                        print("   ... (và nhiều vị trí khác)")
                        break
            
            print("\n👉 NGUYÊN NHÂN: Do dữ liệu thô (G3, G4...) nhập vào bị sai định dạng (thiếu dấu ngăn cách '-' hoặc thiếu số).")
            print("👉 GIẢI PHÁP: Xóa kỳ này đi và nạp lại chuẩn xác.")
        else:
            print("\n✅ Tất cả vị trí đều hợp lệ. Hệ thống lẽ ra phải dự đoán được.")

    except Exception as e:
        print(f"❌ Lỗi khi chạy parser V17: {e}")

if __name__ == "__main__":
    inspect_data()