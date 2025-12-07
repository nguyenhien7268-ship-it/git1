import sys
import os
import sqlite3
import re

# --- CẤU HÌNH ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

try:
    from logic.db_manager import DB_NAME
    from logic.data_repository import get_all_data_ai
    from logic.bridges.bridges_v16 import get_index_from_name_V16
    from logic.de_backtester_core import run_de_bridge_historical_test
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    sys.exit(1)

def check_name_parsing(bridge_name):
    """Mô phỏng logic parse của hệ thống để xem có đọc được tên không"""
    # Logic cũ của Bridge Manager (Gây lỗi)
    # Regex này không bắt được dấu '[' nên sẽ trượt các cầu lỗi tên
    match = re.match(r"(G\d+\.?\d*|GDB)(\d+)", bridge_name)
    
    # Logic V16 chuẩn
    idx = get_index_from_name_V16(bridge_name)
    
    return {
        "regex_manager_ok": bool(match),
        "v16_parser_ok": (idx is not None)
    }

def main():
    print("\n" + "="*80)
    print("🚑 CHẨN ĐOÁN ĐỒNG BỘ DỮ LIỆU CẦU (DB SYNC DIAGNOSTIC)")
    print("="*80)

    # 1. Tải dữ liệu
    print("⏳ Đang tải dữ liệu thực tế...")
    all_data = get_all_data_ai(DB_NAME)
    if not all_data:
        print("❌ DB rỗng.")
        return

    # 2. Lấy cầu từ DB
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, current_streak, type FROM ManagedBridges WHERE is_enabled=1 AND type LIKE 'DE_%'")
    bridges = [dict(row) for row in cursor.fetchall()]
    conn.close()

    print(f"✅ Đang kiểm tra {len(bridges)} cầu Đề đang hoạt động...")
    print("-" * 100)
    print(f"{'TÊN CẦU':<25} | {'DB STREAK':<10} | {'REAL STREAK':<12} | {'TRẠNG THÁI':<15} | {'NGUYÊN NHÂN'}")
    print("-" * 100)

    error_count = 0
    sync_error_count = 0

    for b in bridges:
        name = b['name']
        db_streak = b['current_streak']
        
        # A. Kiểm tra Parse Tên
        parse_status = check_name_parsing(name)
        is_name_broken = not (parse_status['regex_manager_ok'] or parse_status['v16_parser_ok'])
        
        # B. Tính toán Streak Thực tế (Real-time)
        # Chạy backtest 5 ngày gần nhất để lấy streak hiện tại
        try:
            history = run_de_bridge_historical_test(b, all_data, days=10)
            if history and not isinstance(history[0], str):
                # Tính streak từ history
                real_streak = 0
                for day in reversed(history):
                    if day['is_win']: real_streak += 1
                    else: break
            else:
                real_streak = -1 # Lỗi backtest
        except:
            real_streak = -2 # Crash

        # C. So sánh & Đánh giá
        status = "✅ OK"
        reason = ""
        
        if is_name_broken:
            status = "❌ LỖI TÊN"
            reason = "Sai định dạng (Thiếu ngoặc/Format lạ)"
            error_count += 1
        
        if real_streak >= 0 and db_streak != real_streak:
            status = "⚠️ LỆCH SỐ"
            reason += f" (DB treo {db_streak}, Thực {real_streak})"
            sync_error_count += 1
            
        # Chỉ in ra các cầu có vấn đề hoặc cầu tiêu biểu
        if status != "✅ OK":
            print(f"{name:<25} | {str(db_streak):<10} | {str(real_streak):<12} | {status:<15} | {reason}")

    print("-" * 100)
    print(f"📊 TỔNG KẾT:")
    print(f"   - Tổng số cầu kiểm tra: {len(bridges)}")
    print(f"   - Số cầu bị lỗi tên (Unparsable): {error_count}")
    print(f"   - Số cầu bị lệch dữ liệu (Desync): {sync_error_count}")
    
    if error_count > 0:
        print("\n👉 KẾT LUẬN: Hệ thống không thể đọc tên các cầu bị lỗi,")
        print("   dẫn đến việc không thể cập nhật Streak mới (DB vẫn giữ số cũ).")
        print("   -> Cần xóa các cầu này và quét lại sau khi đã fix Scanner.")

if __name__ == "__main__":
    main()