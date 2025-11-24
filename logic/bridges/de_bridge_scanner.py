import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from logic.bridges.bridge_manager_core import Bridge, BridgeLocation
from logic.data_parser import DataParser

class DeBridgeScanner:
    """
    Module quét cầu Đề (Giải Đặc Biệt) tự động.
    Tìm các cặp vị trí (A, B) sao cho (A + B) % 10 = Chạm Đề.
    """
    def __init__(self):
        self.parser = DataParser()

    def scan_best_bridges(self, df: pd.DataFrame, scan_depth: int = 30, limit: int = 20) -> List[Bridge]:
        """
        Quét toàn bộ 107x107 cặp vị trí để tìm cầu thông.
        """
        if len(df) < scan_depth + 5:
            return []

        # 1. Chuẩn bị dữ liệu cache (để chạy nhanh hơn)
        # Lấy data của scan_depth ngày gần nhất
        work_df = df.tail(scan_depth + 5).copy().reset_index(drop=True)
        cached_maps = []
        targets = [] # List các cặp [Chục, Đơn vị] của GDB

        for _, row in work_df.iterrows():
            # Lấy map 107 vị trí
            pos_map = self.parser.get_positions_map(row)
            cached_maps.append(pos_map)
            
            # Lấy GDB
            gdb = str(row.get('GDB', '00'))
            # Xử lý an toàn nếu GDB thiếu
            if not gdb or gdb == 'nan': gdb = '00'
            if len(gdb) >= 2:
                targets.append([int(gdb[-2]), int(gdb[-1])])
            else:
                targets.append([0, 0])

        found_bridges = []
        num_positions = 107
        
        # 2. Quét Brute-force (Vét cạn)
        # Scan ngược từ ngày mới nhất về quá khứ
        current_idx = len(cached_maps) - 1
        
        for p1 in range(num_positions):
            for p2 in range(p1, num_positions): # p2 >= p1 để tránh trùng
                
                streak = 0
                
                # Kiểm tra độ thông (Streak)
                # Bắt đầu từ ngày hôm qua (idx-1) dội lại quá khứ
                # Vì ngày hôm nay (idx) là ngày cần dự đoán, chưa có KQ
                for i in range(current_idx - 1, -1, -1):
                    # Data ngày i dùng để dự đoán cho ngày i+1
                    map_i = cached_maps[i]
                    val1 = map_i[p1]
                    val2 = map_i[p2]
                    if val1 is None or val2 is None: break
                    pred_touch = (val1 + val2) % 10
                    # Kết quả thực tế của ngày i+1
                    actual_touch_set = targets[i+1]
                    if pred_touch in actual_touch_set:
                        streak += 1
                    else:
                        break # Gãy cầu
                if streak >= 3: # Chỉ lấy cầu chạy thông >= 3 ngày
                    # Tính dự đoán cho ngày mai
                    last_map = cached_maps[current_idx]
                    future_val1 = last_map[p1]
                    future_val2 = last_map[p2]
                    if future_val1 is not None and future_val2 is not None:
                        future_pred = (future_val1 + future_val2) % 10
                        bridge = Bridge(
                            locations=[BridgeLocation(p1, 0), BridgeLocation(p2, 0)],
                            value=future_pred,
                            predicted_value=future_pred,
                            score=float(streak),
                            bridge_type="DE_TOUCH"
                        )
                        found_bridges.append(bridge)
        # 3. Sắp xếp giảm dần theo độ thông
        found_bridges.sort(key=lambda x: x.score, reverse=True)
        return found_bridges[:limit]
