#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bridge Executor Module
Calculates predictions for different bridge types given historical data.
Extracted from data_repository.py to support full backtesting.
"""

import re
from abc import ABC, abstractmethod

# Import bridge logic helpers
try:
    from logic.bridges.bridges_v16 import getAllPositions_V17_Shadow, taoSTL_V30_Bong, get_index_from_name_V16
    from logic.bridges.bridges_memory import calculate_bridge_stl, get_27_loto_positions
    from logic.de_utils import get_touches_by_offset
except ImportError:
    # Dummy fallbacks if imports fail (should not happen in production)
    def getAllPositions_V17_Shadow(row): return []
    def taoSTL_V30_Bong(p1, p2): return ["00", "00"]
    def get_index_from_name_V16(name): return None
    def calculate_bridge_stl(loto1, loto2, algorithm_type): return ["00", "00"]
    def get_27_loto_positions(row): return ["00"] * 27
    def get_touches_by_offset(b, k): return []

# --- Helper Functions ---
def _map_loto_name_to_index(name):
    """Maps Lotto position name (e.g. 'Lô G3.5') to index (0-26)"""
    clean_name = name.replace("Lô ", "").strip()
    base_map = {
        "GDB": 0, "G1": 1, "G2": 2, "G3": 4, 
        "G4": 10, "G5": 14, "G6": 20, "G7": 23
    }
    try:
        if "." in clean_name:
            parts = clean_name.split(".")
            g_name = parts[0]
            sub_idx = int(parts[1]) - 1 
            base = base_map.get(g_name)
            if base is not None:
                return base + sub_idx
        else:
            return base_map.get(clean_name)
    except:
        return None
    return None

def _extract_digit_from_col(row, col_name):
    """Extracts last digit from DB column name (e.g. G1 -> row[3])"""
    col_map = {
        "GDB": 2, "G1": 3, 
        "G2": 4, "G2.1": 4, "G2.2": 4,
        "G3": 5, "G4": 6, "G5": 7, "G6": 8, "G7": 9
    }
    base_name = col_name.split(".")[0]
    idx = col_map.get(base_name)
    if idx is None or idx >= len(row): return None
    
    val_str = str(row[idx])
    digits = ''.join(filter(str.isdigit, val_str))
    if not digits: return None
    return int(digits[-1])

# --- Strategy Interface ---
class BridgeStrategy(ABC):
    @abstractmethod
    def execute(self, bridge_name, last_row):
        """
        Execute bridge logic to get prediction
        
        Args:
            bridge_name: Name of the bridge
            last_row: Data row of the LATEST period (to predict NEXT period)
            
        Returns:
            str: Prediction string (e.g. "2,3,7,8") or None if failed
        """
        pass

# --- Concrete Strategies ---

class DynamicKBridgeStrategy(BridgeStrategy):
    """Handles DE_DYN_... bridges (Dynamic K-based)"""
    def execute(self, bridge_name, last_row):
        # Format: DE_DYN_G1_G2_K3
        parts = bridge_name.split("_")
        if len(parts) < 5: return None
        
        n1, n2, k_str = parts[2], parts[3], parts[4]
        try:
            k_val = int(k_str.replace("K", ""))
        except:
            return None
        
        d1 = _extract_digit_from_col(last_row, n1)
        d2 = _extract_digit_from_col(last_row, n2)
        
        if d1 is not None and d2 is not None:
            base_sum = (d1 + d2) % 10
            touches = get_touches_by_offset(base_sum, k_val)
            return ",".join(map(str, touches))
        return None

class MemoryBridgeStrategy(BridgeStrategy):
    """Handles LO_MEM_... bridges (Bạc Nhớ)"""
    def execute(self, bridge_name, last_row):
        # Format: LO_MEM_DIFF_Lô G3.5_Lô G6.3
        parts = bridge_name.split("_")
        if len(parts) < 5: return None
        
        algo_type = parts[2].lower()
        pos1_name = parts[3]
        pos2_name = parts[4]
        
        idx1 = _map_loto_name_to_index(pos1_name)
        idx2 = _map_loto_name_to_index(pos2_name)
        
        lotos_27 = get_27_loto_positions(last_row)
        
        if idx1 is not None and idx2 is not None:
            if idx1 < len(lotos_27) and idx2 < len(lotos_27):
                val1 = lotos_27[idx1]
                val2 = lotos_27[idx2]
                stl = calculate_bridge_stl(val1, val2, algo_type)
                if stl and isinstance(stl, list) and len(stl) > 0:
                    return ",".join(stl)
        return None

class PositionBridgeStrategy(BridgeStrategy):
    """Handles Classic Position Bridges (containing [...])"""
    def execute(self, bridge_name, last_row):
        matches = re.findall(r"(?:Bong\()?(?:G\d+|GDB)\.?\d*\[\d+\]\)?", bridge_name)
        if len(matches) < 2: return None
        
        idx1 = get_index_from_name_V16(matches[0])
        idx2 = get_index_from_name_V16(matches[1])
        
        positions = getAllPositions_V17_Shadow(last_row)
        
        if idx1 is not None and idx2 is not None:
            if idx1 < len(positions) and idx2 < len(positions):
                v1, v2 = positions[idx1], positions[idx2]
                if v1 is not None and v2 is not None:
                    if "DE_POS" in bridge_name:
                        # De Sum Bridge
                        res = (int(v1) + int(v2)) % 10
                        return str(res)
                    else:
                        # Lo Pair Bridge
                        stl = taoSTL_V30_Bong(int(v1), int(v2))
                        return ",".join(stl)
        return None

# --- Main Executor ---
class BridgeExecutor:
    def __init__(self):
        self.strategies = {
            'DE_DYN': DynamicKBridgeStrategy(),
            'LO_MEM': MemoryBridgeStrategy(),
            'POS': PositionBridgeStrategy()
        }
    
    def execute(self, bridge_name, historical_data):
        """
        Execute prediction for a bridge based on historical data.
        prediction is for the NEXT period after the last row in historical_data.
        """
        if not historical_data: return None
        last_row = historical_data[-1]
        
        # Determine strategy
        if bridge_name.startswith("DE_DYN_"):
            return self.strategies['DE_DYN'].execute(bridge_name, last_row)
        elif bridge_name.startswith("LO_MEM_"):
            return self.strategies['LO_MEM'].execute(bridge_name, last_row)
        elif "[" in bridge_name and "]" in bridge_name:
            return self.strategies['POS'].execute(bridge_name, last_row)
            
        return None

