# File: scripts/compare_v37_vs_v38.py
# CHỨC NĂNG: SO SÁNH HIỆU QUẢ GIỮA LOGIC CŨ (V3.7) VÀ ULTIMATE (V3.8)

import sys
import os
import sqlite3
from collections import Counter

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from logic.db_manager import DB_NAME, get_db_connection
    from logic.bridges.de_bridge_scanner import run_de_scanner
    from logic.de_analytics import (
        calculate_number_scores,    # Đây là V3.8 (đã cập nhật)
        analyze_market_trends,
        get_top_strongest_sets,
        BO_SO_DE, get_set_name_of_number, check_cham
    )
    print("✅ Đã load các module logic thành công.")
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    sys.exit(1)

# --- 1. TÁI HIỆN LOGIC V3.7 (LEGACY) ---
def calculate_scores_v37_legacy(bridges):
    """
    Logic cũ: Chỉ cộng điểm cầu tích cực, KHÔNG trừ điểm Killer.
    """
    scores = {f"{i:02d}": 0.0 for i in range(100)}
    for bridge in bridges:
        val = str(bridge.get('predicted_value', ''))
        try:
            streak = float(bridge.get('streak', 1))
        except: streak = 1.0
        
        # Chỉ xử lý cầu bộ và cầu chạm/tổng (Tấn công)
        if 'BO' in str(bridge.get('type','')):
            # Normalize bo key logic cũ (giản lược)
            digits = "".join(filter(str.isdigit, val))
            if digits:
                k = digits.zfill(2)
                if k in BO_SO_DE:
                    for s in BO_SO_DE[k]: scores[s] += streak * 2.0
        elif 'CHAM' in str(bridge.get('type','')) or 'PASCAL' in str(bridge.get('type','')):
            parts = [int(v) for v in val.split(',') if v.strip().isdigit()]
            for s in scores:
                if check_cham(s, parts): scores[s] += streak
                
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

def get_forecast_v37(scores, strong_sets):
    """
    Logic chốt số V3.7: Ép buộc số phải thuộc Top Bộ (Strong Sets).
    """
    top_65 = [x[0] for x in scores[:65]]
    top_sets = strong_sets[:3] if strong_sets else []
    
    priority_nums = []
    backup_nums = []
    
    for num in top_65:
        my_set = get_set_name_of_number(num)
        if my_set and my_set in top_sets:
            priority_nums.append(num)
        else:
            backup_nums.append(num)
            
    final_list = priority_nums + backup_nums
    return sorted(final_list[:10]) # Top 10

# --- 2. LOGIC V3.8 (ULTIMATE) ---
def get_forecast_v38(scores, strong_sets):
    """
    Logic chốt số V3.8: Tin tưởng vào điểm số (đã trừ Killer), Top Bộ chỉ là ưu tiên nhẹ.
    """
    candidates = scores[:15] # Lấy 15 số điểm cao nhất (đã trừ Killer)
    candidate_nums = [x[0] for x in candidates]
    
    top_sets = strong_sets[:3] if strong_sets else []
    
    prioritized = []
    others = []
    
    for num in candidate_nums:
        my_set = get_set_name_of_number(num)
        if my_set and my_set in top_sets:
            prioritized.append(num)
        else:
            others.append(num)
            
    final_list = prioritized + others
    return sorted(final_list[:10])

# --- 3. HÀM CHUẨN BỊ DỮ LIỆU ---
def fetch_all_data_ai():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Lấy dữ liệu thô: ky, gdb, g1...g7
    cursor.execute("""
        SELECT ky, date, gdb, g1, g2, g3, g4, g5, g6, g7 
        FROM results_A_I 
        ORDER BY CAST(ky AS INTEGER) ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    # Convert sang format List[List[str]] cho scanner
    data = []
    for r in rows:
        row_list = [str(r[0]), str(r[1])] # Ky, Date
        # GDB -> G7
        for idx in range(2, 10):
            val = r[idx] if r[idx] else ""
            row_list.append(str(val))
        data.append(row_list)
    return data

# --- 4. ENGINE SO SÁNH ---
def run_comparison(days_to_test=20):
    full_data = fetch_all_data_ai()
    if len(full_data) < 100:
        print("❌ Không đủ dữ liệu để backtest.")
        return

    print(f"\n=== ⚔️ ĐẤU TRƯỜNG V3.7 vs V3.8 ({days_to_test} ngày gần nhất) ⚔️ ===")
    print(f"{'NGÀY':<12} | {'ĐỀ VỀ':<6} | {'V3.7 (Cũ)':<20} | {'V3.8 (Mới)':<20} | {'KQ'}")
    print("-" * 80)

    v37_wins = 0
    v38_wins = 0
    
    # Lặp qua N ngày cuối
    start_idx = len(full_data) - days_to_test
    
    for i in range(start_idx, len(full_data)):
        # Dữ liệu huấn luyện: Từ đầu đến ngày hôm qua (i-1)
        train_data = full_data[:i]
        
        # Dữ liệu thực tế hôm nay (để check kết quả)
        actual_row = full_data[i]
        date_str = actual_row[1]
        gdb_full = actual_row[2]
        if not gdb_full or len(gdb_full) < 2: continue
        de_ve = gdb_full[-2:]
        
        # 1. Chạy phân tích
        _, bridges = run_de_scanner(train_data)
        market_stats = analyze_market_trends(train_data, n_days=60)
        strong_sets = get_top_strongest_sets(bridges, market_stats, train_data[-1])
        
        # 2. Tính điểm & Chốt số V3.7
        scores_v37 = calculate_scores_v37_legacy(bridges)
        top10_v37 = get_forecast_v37(scores_v37, strong_sets)
        
        # 3. Tính điểm & Chốt số V3.8
        scores_v38 = calculate_number_scores(bridges, market_stats) # Hàm chính đã update
        top10_v38 = get_forecast_v38(scores_v38, strong_sets)
        
        # 4. Check Win
        win37 = de_ve in top10_v37
        win38 = de_ve in top10_v38
        
        if win37: v37_wins += 1
        if win38: v38_wins += 1
        
        status = ""
        if win38 and not win37: status = "🔥 V3.8 CỨU!"
        elif win37 and not win38: status = "⚠️ V3.8 FAIL"
        elif win37 and win38: status = "✅ Cả 2 Ăn"
        else: status = "❌ Cả 2 Xịt"
        
        print(f"{date_str:<12} | {de_ve:<6} | {str(win37):<20} | {str(win38):<20} | {status}")

    print("-" * 80)
    print(f"TỔNG KẾT SAU {days_to_test} NGÀY:")
    print(f"🏆 V3.7 Win: {v37_wins} / {days_to_test} ({v37_wins/days_to_test*100:.1f}%)")
    print(f"🚀 V3.8 Win: {v38_wins} / {days_to_test} ({v38_wins/days_to_test*100:.1f}%)")
    
    diff = v38_wins - v37_wins
    if diff > 0:
        print(f"\n=> KẾT LUẬN: V3.8 HIỆU QUẢ HƠN (+{diff} ngày thắng). Nâng cấp thành công!")
    elif diff == 0:
        print("\n=> KẾT LUẬN: Hiệu quả ngang nhau.")
    else:
        print(f"\n=> KẾT LUẬN: V3.8 đang kém hơn. Cần tinh chỉnh lại hệ số phạt Killer.")

if __name__ == "__main__":
    run_comparison(days_to_test=30)