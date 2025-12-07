# Tên file: generate_audit_report.py
import sys
import os
import json
from collections import Counter

# Setup đường dẫn
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from lottery_service import load_data_ai_from_db, DB_NAME
    from logic.bridges.de_bridge_scanner import run_de_scanner
    from logic.de_analytics import calculate_number_scores, analyze_market_trends
    from logic.de_utils import get_gdb_last_2, BO_SO_DE
    
    # Hàm hỗ trợ phân tích chi tiết điểm số
    def analyze_score_contribution(target_num, bridges):
        """Phân tích xem số này được điểm từ những đâu"""
        details = {
            "total_bridges": 0,
            "bridge_types": Counter(),
            "score_breakdown": []
        }
        
        # Mô phỏng lại logic tính điểm để lấy chi tiết
        STANDARD_CONST = 20.0 
        
        for bridge in bridges:
            try:
                # Logic xác định số trong cầu (copy từ de_analytics)
                target_numbers = set()
                if 'numbers' in bridge and isinstance(bridge['numbers'], list):
                    target_numbers.update(bridge['numbers'])
                else:
                    val = str(bridge.get('predicted_value', ''))
                    # (Logic parse giản lược để audit)
                    if "Bộ" in val:
                        for k, v in BO_SO_DE.items():
                            if k in val: target_numbers.update(v)
                    elif "," in val:
                        parts = [int(v) for v in val.replace("Chạm","").split(',') if v.strip().isdigit()]
                        for p in parts:
                            for i in range(10): target_numbers.add(f"{p}{i}"); target_numbers.add(f"{i}{p}")
                
                # Nếu cầu này có chứa số mục tiêu -> Ghi nhận
                if target_num in target_numbers:
                    details["total_bridges"] += 1
                    b_type = bridge.get('type', 'UNKNOWN')
                    details["bridge_types"][b_type] += 1
                    
                    count = len(target_numbers)
                    if count > 0:
                        streak = float(bridge.get('streak', 0))
                        density_weight = STANDARD_CONST / float(count)
                        streak_bonus = 1.0 + (streak * 0.1)
                        final_score = density_weight * streak_bonus
                        
                        details["score_breakdown"].append({
                            "name": bridge.get('name'),
                            "type": b_type,
                            "streak": streak,
                            "count": count,
                            "points": round(final_score, 2)
                        })
            except: continue
            
        # Sắp xếp các cầu đóng góp điểm cao nhất
        details["score_breakdown"].sort(key=lambda x: x["points"], reverse=True)
        return details

    print(f"\n>>> ĐANG TẠO BÁO CÁO KIỂM TOÁN HỆ THỐNG (AUDIT REPORT)...")
    
    # 1. Tải dữ liệu
    all_data, msg = load_data_ai_from_db(DB_NAME)
    if not all_data or len(all_data) < 100:
        print(f"❌ Lỗi tải dữ liệu: {msg}")
        sys.exit()

    # Cấu hình: Kiểm tra 15 kỳ gần nhất (để file báo cáo không quá dài)
    TEST_DAYS = 15
    start_index = len(all_data) - TEST_DAYS
    
    report_lines = []
    report_lines.append(f"BÁO CÁO KIỂM TOÁN HIỆU QUẢ SCORING V3 (FAIRNESS)")
    report_lines.append(f"Thời gian test: 15 kỳ gần nhất")
    report_lines.append("="*80)

    for i in range(start_index, len(all_data)):
        past_data = all_data[:i]
        current_row = all_data[i]
        
        ky = str(current_row[0])
        kq_thuc_te = get_gdb_last_2(current_row)
        if not kq_thuc_te: continue
        
        # A. Quét & Tính điểm
        # Lưu ý: Không truyền scan_limit vào run_de_scanner để tránh lỗi, tự cắt list sau
        try:
            _, bridges = run_de_scanner(past_data)
            bridges = bridges[:200] # Lấy 200 cầu tốt nhất để phân tích
        except Exception as e:
            print(f"Lỗi Scanner kỳ {ky}: {e}")
            continue

        market_stats = analyze_market_trends(past_data)
        ranked_scores = calculate_number_scores(bridges, market_stats)
        
        # B. Tìm thông tin KQ thực tế
        kq_rank = -1
        kq_score = 0
        kq_info = ""
        
        for rank, (num, score, info) in enumerate(ranked_scores):
            if num == kq_thuc_te:
                kq_rank = rank + 1
                kq_score = score
                kq_info = info
                break
        
        # C. Tìm thông tin Top 1 (Số sai nhưng điểm cao nhất)
        top1_num, top1_score, top1_info = ranked_scores[0]
        
        # D. Phân tích sâu (Deep Dive)
        report_lines.append(f"\n>>> KỲ {ky} | KQ: {kq_thuc_te} | Hạng: #{kq_rank} | Điểm: {kq_score:.1f}")
        
        # 1. Tại sao KQ lại được điểm này?
        kq_audit = analyze_score_contribution(kq_thuc_te, bridges)
        report_lines.append(f"    [PHÂN TÍCH KQ {kq_thuc_te}]: Được {kq_audit['total_bridges']} cầu ủng hộ.")
        report_lines.append(f"    - Cơ cấu cầu: {dict(kq_audit['bridge_types'])}")
        if kq_audit['score_breakdown']:
            top_b = kq_audit['score_breakdown'][0]
            report_lines.append(f"    - Cầu to nhất: {top_b['name']} ({top_b['type']}) -> +{top_b['points']}đ (Streak {top_b['streak']})")
        
        # 2. Tại sao Top 1 lại cao điểm hơn? (Nếu KQ không phải Top 1)
        if kq_rank > 1:
            top1_audit = analyze_score_contribution(top1_num, bridges)
            diff = top1_score - kq_score
            report_lines.append(f"    [SO SÁNH TOP 1 {top1_num}]: Cao hơn KQ {diff:.1f} điểm.")
            report_lines.append(f"    - Top 1 được {top1_audit['total_bridges']} cầu ủng hộ. Cơ cấu: {dict(top1_audit['bridge_types'])}")
            if top1_audit['score_breakdown']:
                top_b1 = top1_audit['score_breakdown'][0]
                report_lines.append(f"    - Cầu to nhất của Top 1: {top_b1['name']} -> +{top_b1['points']}đ")
                
            # Đánh giá nguyên nhân
            if top1_audit['total_bridges'] > kq_audit['total_bridges'] * 2:
                report_lines.append(f"    => NHẬN XÉT: Top 1 thắng nhờ SỐ LƯỢNG cầu áp đảo (Spam cầu).")
            elif top1_audit['score_breakdown'] and kq_audit['score_breakdown'] and \
                 top1_audit['score_breakdown'][0]['points'] > kq_audit['score_breakdown'][0]['points']:
                report_lines.append(f"    => NHẬN XÉT: Top 1 thắng nhờ CHẤT LƯỢNG cầu (Cầu Bộ/Kép điểm cao).")
        
        print(f"   -> Đã phân tích kỳ {ky}...")

    # Ghi file
    with open("AUDIT_REPORT_V3.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print("\n✅ ĐÃ TẠO BÁO CÁO THÀNH CÔNG: 'AUDIT_REPORT_V3.txt'")
    print(">>> Hãy gửi file này cho Gemini để tinh chỉnh thuật toán.")

except Exception as e:
    print(f"Lỗi: {e}")
    import traceback
    traceback.print_exc()