import sys
import os
import re
import inspect

# --- CẤU HÌNH ĐƯỜNG DẪN ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

try:
    from logic.bridges.bridge_manager_de import de_manager
    from logic.bridges.bridges_v16 import get_index_from_name_V16, getPositionName_V16
    from logic.db_manager import DB_NAME
    from logic.data_repository import get_all_data_ai
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    sys.exit(1)

def check_source_code():
    print("="*80)
    print("🔍 KIỂM TRA MÃ NGUỒN THỰC TẾ (SOURCE CODE INSPECTION)")
    print("="*80)
    
    try:
        # Lấy source code của hàm _map_safe_name_to_index
        source = inspect.getsource(de_manager._map_safe_name_to_index)
        print("--- Code hiện tại của hàm _map_safe_name_to_index ---")
        print(source)
        print("-----------------------------------------------------")
        
        # Kiểm tra Regex
        if r'[\[\.]?' in source or r'[\\.]?' in source:
            print("✅ Regex có vẻ ĐÚNG (Có chứa [\[\.]?)")
        else:
            print("❌ Regex có vẻ SAI/CŨ (Thiếu [\[\.]?)")
            
    except Exception as e:
        print(f"⚠️ Không thể đọc source code: {e}")

def debug_bridge_logic(bridge_name):
    print("\n" + "="*80)
    print(f"🕵️  DEBUG LOGIC TÍNH TOÁN CẦU: {bridge_name}")
    print("="*80)

    # 1. Test Parse Tên Cầu
    print(f"🔹 [BƯỚC 1] Test Parse Tên: '{bridge_name}'")
    
    # Giả lập b_type dựa trên tên
    b_type = "UNKNOWN"
    if "DE_SET" in bridge_name: b_type = "DE_SET"
    elif "DE_DYN" in bridge_name: b_type = "DE_DYNAMIC_K"
    elif "DE_KILLER" in bridge_name: b_type = "DE_KILLER"
    
    print(f"   -> B_Type giả lập: {b_type}")
    
    try:
        parsed = de_manager._parse_bridge_id_v2(bridge_name, b_type)
        if parsed:
            idx1, idx2, k, mode = parsed
            print(f"   ✅ Parse THÀNH CÔNG!")
            print(f"      - Index 1: {idx1} ({getPositionName_V16(idx1)})")
            print(f"      - Index 2: {idx2} ({getPositionName_V16(idx2)})")
            print(f"      - Mode: {mode}")
        else:
            print(f"   ❌ Parse THẤT BẠI (Trả về None)")
            
            # Debug chi tiết tại sao thất bại
            parts = bridge_name.split("_")
            if len(parts) >= 3:
                p1 = parts[2]
                print(f"      -> Thử map vị trí 1 '{p1}':")
                idx1_try = de_manager._map_safe_name_to_index(p1)
                print(f"         Kết quả: {idx1_try}")
                
                # Test logic chuyển đổi thủ công để xem lỗi ở đâu
                clean_name = p1.replace("[", "").replace("]", "").replace(".", "")
                print(f"         Clean name (logic cũ): '{clean_name}'")
                
                # Test regex match
                # Regex mong đợi: r"(G\d+\.?\d*|GDB)[\[\.]?(\d+)"
                match = re.match(r"(G\d+\.?\d*|GDB)[\[\.]?(\d+)", p1)
                print(f"         Regex Match (Mới): {bool(match)}")
                if match:
                    print(f"         Groups: {match.groups()}")
                    g_name, g_idx = match.groups()
                    recon = f"{g_name}[{g_idx}]"
                    print(f"         Reconstructed: '{recon}'")
                    print(f"         get_index_from_name_V16('{recon}'): {get_index_from_name_V16(recon)}")

    except Exception as e:
        print(f"   ❌ Lỗi Exception khi Parse: {e}")
        import traceback
        traceback.print_exc()

def main():
    check_source_code()
    
    # Test với cầu bị báo lỗi trong log của bạn
    debug_bridge_logic("DE_SET_G3.2.2_G5.5.3")
    
    # Test thêm cầu DYN cũng bị lỗi
    debug_bridge_logic("DE_DYN_G1.4_G6.3.2_K3")

if __name__ == "__main__":
    main()