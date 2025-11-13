"""
==================================================================================
LOGIC PHÂN TÍCH TIỆN ÍCH (V8.2)
Tệp này được tạo để phá vỡ lỗi phụ thuộc tuần hoàn (Circular Import)
giữa ml_model.py và dashboard_analytics.py.

Chứa các hàm phân tích (Hot/Gan) được cả hai mô-đun trên sử dụng.
==================================================================================
"""
from collections import Counter

# Import các hàm cầu cổ điển
try:
    from .bridges.bridges_classic import getAllLoto_V30 
except ImportError:
    try:
        from logic.bridges.bridges_classic import getAllLoto_V30 
    except ImportError:
        print("LỖI NGHIÊM TRỌNG: analytics_utils.py không thể import bridges_classic!")
        def getAllLoto_V30(r): return []

# Import SETTINGS
try:
    from .config_manager import SETTINGS
except ImportError:
    from config_manager import SETTINGS
    # Fallback definition cho SETTINGS
    SETTINGS = type('obj', (object,), {
        'STATS_DAYS': 7, 
        'GAN_DAYS': 15
    })

def get_loto_stats_last_n_days(all_data_ai, n=None):
    """ (ĐÃ DI CHUYỂN TỪ dashboard_analytics) Lấy thống kê tần suất loto (hot/lạnh). """
    try:
        if n is None:
            n = SETTINGS.STATS_DAYS
            
        if not all_data_ai or len(all_data_ai) == 0:
            return []
            
        if len(all_data_ai) < n:
            n = len(all_data_ai)
        
        last_n_rows = all_data_ai[-n:]
        
        all_lotos_hits = [] 
        day_appearance_counter = Counter() 
        
        for row in last_n_rows:
            lotos_in_this_row = getAllLoto_V30(row)
            all_lotos_hits.extend(lotos_in_this_row)
            unique_lotos_in_this_row = set(lotos_in_this_row)
            day_appearance_counter.update(unique_lotos_in_this_row) 
        
        loto_hit_counts = Counter(all_lotos_hits)
        sorted_lotos_by_hits = sorted(loto_hit_counts.items(), key=lambda item: item[1], reverse=True)
        
        final_stats = []
        for loto, hit_count in sorted_lotos_by_hits:
            day_count = day_appearance_counter.get(loto, 0) 
            final_stats.append((loto, hit_count, day_count)) 
            
        return final_stats
        
    except Exception as e:
        print(f"Lỗi get_loto_stats_last_n_days: {e}")
        return []

def get_loto_gan_stats(all_data_ai, n_days=None):
    """ (ĐÃ DI CHUYỂN TỪ dashboard_analytics) Tìm các loto (00-99) đã không xuất hiện trong n_days gần nhất (Lô Gan). """
    gan_stats = []
    try:
        if n_days is None:
            n_days = SETTINGS.GAN_DAYS
            
        if not all_data_ai or len(all_data_ai) < n_days:
            return []
            
        all_100_lotos = {str(i).zfill(2) for i in range(100)}
        
        recent_lotos = set()
        recent_rows = all_data_ai[-n_days:]
        for row in recent_rows:
            lotos_in_this_row = getAllLoto_V30(row)
            recent_lotos.update(lotos_in_this_row)
            
        gan_lotos = all_100_lotos - recent_lotos
        
        if not gan_lotos:
            return [] 

        full_history = all_data_ai[:] 
        full_history.reverse() 
        
        for loto in gan_lotos:
            days_gan = 0
            found = False
            for i, row in enumerate(full_history):
                if i < n_days: 
                    days_gan += 1
                    continue
                
                loto_set_this_day = set(getAllLoto_V30(row))
                if loto in loto_set_this_day:
                    found = True
                    break 
                else:
                    days_gan += 1 
            
            if found:
                gan_stats.append((loto, days_gan))
            else:
                gan_stats.append((loto, len(full_history)))

        gan_stats.sort(key=lambda x: x[1], reverse=True)
        return gan_stats

    except Exception as e:
        print(f"Lỗi get_loto_gan_stats: {e}")
        return []