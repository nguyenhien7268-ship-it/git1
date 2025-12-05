# logic/lo_analytics.py (FIXED V3.8.1)
from collections import Counter
try:
    from logic.constants import SCORING_WEIGHTS
except ImportError:
    # Fallback
    SCORING_WEIGHTS = {
        'LO_STREAK_MULTIPLIER': 1.0, 'LO_WINRATE_DIVISOR': 20.0, 'LO_MEMORY_DIVISOR': 10.0,
        'LO_GAN_PENALTY_LOW': 2.0, 'LO_GAN_PENALTY_MED': 5.0, 'LO_GAN_PENALTY_HIGH': 15.0,
        'LO_FREQ_BONUS_MAX': 3.0
    }

def calculate_lo_scores(bridges, gan_stats, freq_stats, top_memory=None):
    """
    Tính điểm Lô tô (00-99) dựa trên công thức Attack - Defense + Bonus.
    (Fixed Tuple/Dict Handling)
    """
    # Khởi tạo bảng điểm 00-99
    scores = {f"{i:02d}": 0.0 for i in range(100)}
    
    # --- 1. ATTACK: CỘNG ĐIỂM TỪ CẦU (BRIDGES) ---
    if bridges:
        for b in bridges:
            pred = str(b.get('next_prediction_stl', ''))
            nums = []
            
            if '-' in pred:
                nums = pred.split('-')
            elif pred.strip().isdigit():
                nums = [pred.strip()]
            
            try:
                streak = float(b.get('current_streak', 1))
                wr_text = str(b.get('win_rate_text', '0')).replace('%', '')
                win_rate = float(wr_text) if wr_text else 0
            except:
                streak, win_rate = 1.0, 50.0
            
            # Attack Score
            attack_score = (streak * SCORING_WEIGHTS['LO_STREAK_MULTIPLIER']) + \
                           (win_rate / SCORING_WEIGHTS['LO_WINRATE_DIVISOR'])
            
            for n in nums:
                n = n.strip()
                if n in scores:
                    scores[n] += attack_score

    # --- 1b. ATTACK BONUS: CẦU BẠC NHỚ ---
    if top_memory:
        for item in top_memory:
            try:
                pred_mem = str(item.get('prediction', '')) 
                nums = pred_mem.split('-') if '-' in pred_mem else [pred_mem]
                conf = float(item.get('confidence', 0))
                bonus = conf / SCORING_WEIGHTS['LO_MEMORY_DIVISOR']
                for n in nums:
                    n = n.strip()
                    if n in scores:
                        scores[n] += bonus
            except: continue

    # --- 2. DEFENSE: PHẠT LÔ GAN (KILLER) - ĐÃ FIX LỖI TUPLE ---
    if gan_stats:
        for item in gan_stats:
            try:
                # Xử lý đa hình (Polymorphism) cho Dict và Tuple
                if isinstance(item, dict):
                    so = item.get('so')
                    ngay_gan = item.get('so_ngay_gan', item.get('gan', 0))
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    so = item[0]
                    ngay_gan = item[1]
                else:
                    continue

                if so in scores and ngay_gan > 10:
                    penalty = 0
                    if 10 < ngay_gan <= 15: penalty = SCORING_WEIGHTS['LO_GAN_PENALTY_LOW']
                    elif 15 < ngay_gan <= 25: penalty = SCORING_WEIGHTS['LO_GAN_PENALTY_MED']
                    elif ngay_gan > 25: penalty = SCORING_WEIGHTS['LO_GAN_PENALTY_HIGH']
                    scores[so] -= penalty
            except Exception as e: 
                # print(f"Lỗi tính gan: {e}") 
                continue

    # --- 3. BONUS: THƯỞNG TẦN SUẤT ---
    if freq_stats:
        max_freq = 0
        freq_map = {}
        for item in freq_stats:
            try:
                if isinstance(item, dict):
                    so = item.get('so')
                    count = item.get('so_lan_ve', item.get('freq', 0))
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    so = item[0]
                    count = item[1]
                else:
                    continue
                
                freq_map[so] = count
                if count > max_freq: max_freq = count
            except: continue
            
        if max_freq > 0:
            for so, count in freq_map.items():
                if so in scores:
                    bonus = (count / max_freq) * SCORING_WEIGHTS['LO_FREQ_BONUS_MAX']
                    scores[so] += bonus

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)