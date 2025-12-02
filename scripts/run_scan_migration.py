import sys
import os
import sqlite3

# 1. Setup đường dẫn
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# 2. Import module
try:
    from services.data_service import DataService
    from logic.bridges.de_bridge_scanner import DeBridgeScanner
    from logic.bridges.bridge_manager_core import find_and_auto_manage_bridges, init_all_756_memory_bridges_to_db
    from logic.db_manager import DB_NAME
except ImportError as e:
    print(f"❌ LỖI IMPORT: {e}")
    sys.exit(1)

def run_migration_scan():
    print("🚀 BẮT ĐẦU QUÉT TOÀN DIỆN (FULL MIGRATION V2.1)...")
    
    # --- BƯỚC 1: TẢI DỮ LIỆU ---
    print(f"1️⃣  Đang tải dữ liệu từ DB: {DB_NAME}...")
    data_service = DataService(DB_NAME)
    all_data = data_service.load_data()
    
    if not all_data or len(all_data) < 50:
        print(f"❌ LỖI: Dữ liệu quá ít ({len(all_data) if all_data else 0} bản ghi).")
        return

    # --- BƯỚC 2: KHỞI TẠO BẠC NHỚ (NẾU CHƯA CÓ) ---
    print("2️⃣  Kiểm tra & Khởi tạo Cầu Bạc Nhớ (LO_MEM)...")
    # Hàm này sẽ thêm 756 cầu bạc nhớ vào DB với tên chuẩn LO_MEM_...
    # (Nếu đã có rồi nó sẽ bỏ qua, không sao cả)
    _, msg, added, _ = init_all_756_memory_bridges_to_db(DB_NAME, enable_all=True)
    print(f"   -> {msg}")

    # --- BƯỚC 3: QUÉT CẦU LÔ (CORE) ---
    print("3️⃣  Đang quét Cầu Lô (V17 & Fixed & Bạc Nhớ)...")
    # Hàm này gọi TIM_CAU_TOT_NHAT_V16 (sinh LO_POS) và update Fixed (LO_STL_FIXED)
    scan_msg = find_and_auto_manage_bridges(all_data, DB_NAME)
    print(f"   -> Kết quả Lô: {scan_msg}")

    # --- BƯỚC 4: QUÉT CẦU ĐỀ (DE SCANNER) ---
    print("4️⃣  Đang quét Cầu Đề (Scanner)...")
    scanner = DeBridgeScanner()
    count_de, bridges_de = scanner.scan_all(all_data)
    
    de_set = sum(1 for b in bridges_de if b.get('type') == 'DE_SET')
    de_dyn = sum(1 for b in bridges_de if b.get('type') == 'DE_DYNAMIC_K')
    
    print(f"   -> Kết quả Đề: Tổng {count_de} cầu (Bộ: {de_set}, Động: {de_dyn})")

    print("\n✅ HOÀN TẤT QUÁ TRÌNH NÂNG CẤP!")
    print("   Hệ thống bây giờ đã có đầy đủ:")
    print("   - LO_POS_... (Lô Vị Trí)")
    print("   - LO_MEM_... (Lô Bạc Nhớ)")
    print("   - LO_STL_FIXED_... (Lô Cố Định)")
    print("   - DE_SET_... (Đề Bộ)")
    print("   - DE_DYN_... (Đề Động)")

if __name__ == "__main__":
    run_migration_scan()