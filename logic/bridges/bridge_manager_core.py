# Tên file: logic/bridges/bridge_manager_core.py
# (PHIÊN BẢN V10.0 - REFACTORED: SEPARATED SCANNING FROM MANAGEMENT)
#
# Mục đích: Chỉ giữ logic QUẢN LÝ (Management) cầu Lô.
#           Logic DÒ TÌM (Scanning) đã được tách sang lo_bridge_scanner.py.

import os
import sqlite3
import sys
from typing import List, Optional, Dict

# =========================================================================
# PATH FIX
# =========================================================================
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except Exception:
    pass

# =========================================================================
# IMPORTS
# =========================================================================
try:
    from logic.config_manager import SETTINGS
except ImportError:
    SETTINGS = type("obj", (object,), {"AUTO_ADD_MIN_RATE": 50.0, "AUTO_PRUNE_MIN_RATE": 40.0})

try:
    from logic.data_repository import get_all_managed_bridges
    from logic.db_manager import (
        DB_NAME, update_managed_bridge
    )
except ImportError:
    DB_NAME = "data/xo_so_prizes_all_logic.db"
    def update_managed_bridge(*args, **kwargs): return False, "Lỗi Import"
    def get_all_managed_bridges(*args, **kwargs): return []

try:
    from logic.bridges.bridges_memory import get_27_loto_names
except ImportError:
    pass

# Import scanning functions from lo_bridge_scanner
try:
    from logic.bridges.lo_bridge_scanner import (
        TIM_CAU_TOT_NHAT_V16,
        TIM_CAU_BAC_NHO_TOT_NHAT,
        update_fixed_lo_bridges,
        _ensure_core_db_columns
    )
except ImportError:
    print("WARNING: Could not import scanning functions from lo_bridge_scanner")
    def TIM_CAU_TOT_NHAT_V16(*args, **kwargs): return []
    def TIM_CAU_BAC_NHO_TOT_NHAT(*args, **kwargs): return []
    def update_fixed_lo_bridges(*args, **kwargs): return 0
    def _ensure_core_db_columns(*args, **kwargs): pass

# ===================================================================================
# HELPER FUNCTIONS
# ===================================================================================

def is_de_bridge(bridge):
    """
    Determine if a bridge is a De (Đề) bridge based on its name or type.
    
    Args:
        bridge: Bridge dict with 'name' and optional 'type' keys
        
    Returns:
        bool: True if it's a De bridge, False if it's a Lo bridge
    """
    bridge_name = bridge.get('name', '')
    bridge_type = bridge.get('type', '')
    
    # Check if bridge name or type indicates it's a De bridge
    de_indicators = ['DE_', 'Đề', 'de_', 'đề']
    
    for indicator in de_indicators:
        if indicator in bridge_name or indicator in bridge_type:
            return True
    
    return False

# ===================================================================================
# MANAGEMENT FUNCTIONS (Các hàm quản lý cầu)
# ===================================================================================
# Note: Scanning functions (TIM_CAU_TOT_NHAT_V16, TIM_CAU_BAC_NHO_TOT_NHAT, 
#       update_fixed_lo_bridges) have been moved to lo_bridge_scanner.py

def find_and_auto_manage_bridges(all_data_ai, db_name=DB_NAME):
    """
    Tự động dò tìm và quản lý cầu Lô.
    
    Calls scanning functions from lo_bridge_scanner module.
    
    Args:
        all_data_ai: Dữ liệu toàn bộ kỳ quay
        db_name: Đường dẫn database
        
    Returns:
        String message about bridges found/updated
    """
    try:
        if not all_data_ai:
            return "Lỗi: Không có dữ liệu."
        msg = []
        
        print("... [Auto] Dò V17 Shadow (K2N Scan) ...")
        res_v17 = TIM_CAU_TOT_NHAT_V16(all_data_ai, 2, len(all_data_ai)+1, db_name)
        msg.append(f"V17 (Scan): {len(res_v17)-1 if res_v17 else 0} cầu")
        
        print("... [Auto] Dò Bạc Nhớ (K2N Scan) ...")
        res_bn = TIM_CAU_BAC_NHO_TOT_NHAT(all_data_ai, 2, len(all_data_ai)+1, db_name)
        msg.append(f"Bạc Nhớ (Scan): {len(res_bn)-1 if res_bn else 0} cầu")
        
        print("... [Auto] Cập nhật Fixed (K1N Real) ...")
        c_fix = update_fixed_lo_bridges(all_data_ai, db_name)
        msg.append(f"Fixed (K1N): {c_fix} cầu")
        
        return " | ".join(msg)
    except Exception as e:
        return f"Lỗi: {e}"

def prune_bad_bridges(all_data_ai, db_name=DB_NAME):
    """
    Lọc và tắt các cầu yếu (Low performance bridges).
    Sử dụng dual-config để áp dụng ngưỡng khác nhau cho cầu Lô và Đề.
    
    Args:
        all_data_ai: Dữ liệu toàn bộ kỳ quay (unused but kept for API compatibility)
        db_name: Đường dẫn database
        
    Returns:
        String message about pruning results
    """
    # Get thresholds from dual-config (with fallback)
    try:
        lo_config = SETTINGS.get('lo_config', {})
        de_config = SETTINGS.get('de_config', {})
        
        lo_remove_threshold = lo_config.get('remove_threshold', 43.0)
        de_remove_threshold = de_config.get('remove_threshold', 80.0)
    except:
        # Fallback to old settings if dual-config not available
        lo_remove_threshold = getattr(SETTINGS, 'AUTO_PRUNE_MIN_RATE', 43.0)
        de_remove_threshold = 80.0

    disabled_count = 0
    disabled_lo_count = 0
    disabled_de_count = 0
    skipped_pinned = 0
    
    try:
        bridges = get_all_managed_bridges(db_name, only_enabled=True)
        if not bridges:
            return "Không có cầu để lọc."
        
        for b in bridges:
            try:
                is_pinned = b.get("is_pinned", 0)
                if is_pinned:
                    skipped_pinned += 1
                    continue
                
                # Determine if this is a De bridge
                is_de = is_de_bridge(b)
                remove_threshold = de_remove_threshold if is_de else lo_remove_threshold
                
                # Get K1N rate (primary metric)
                k1n_str = str(b.get("win_rate_text", "0")).replace("%", "")
                try:
                    k1n_val = float(k1n_str)
                except:
                    k1n_val = 0.0
                
                # Get K2N rate (secondary metric)
                k2n_str = str(b.get("search_rate_text", "0")).replace("%", "")
                try:
                    k2n_val = float(k2n_str)
                except:
                    k2n_val = 0.0

                should_disable = False
                
                # Logic: Disable if BOTH K1N and K2N are below threshold
                if k1n_val > 0 or k2n_val > 0:
                    is_k1n_ok = (k1n_val >= remove_threshold)
                    is_k2n_ok = (k2n_val >= remove_threshold)
                    if not is_k1n_ok and not is_k2n_ok:
                        should_disable = True
                else:
                    should_disable = False

                if should_disable:
                    update_managed_bridge(b["id"], b["description"], 0, db_name)
                    disabled_count += 1
                    if is_de:
                        disabled_de_count += 1
                    else:
                        disabled_lo_count += 1
                    
            except Exception as e_inner:
                print(f"Lỗi check cầu {b.get('name')}: {e_inner}")
                pass
                
    except Exception as e:
        return f"Lỗi lọc cầu: {e}"

    msg = f"Lọc cầu hoàn tất. Đã TẮT {disabled_count} cầu yếu "
    msg += f"(Lô: {disabled_lo_count} < {lo_remove_threshold}%, Đề: {disabled_de_count} < {de_remove_threshold}%)."
    if skipped_pinned > 0:
        msg += f" Bỏ qua {skipped_pinned} cầu đã ghim."
    return msg


def auto_manage_bridges(all_data_ai, db_name=DB_NAME):
    """
    Tự động quản lý cầu: Bật lại các cầu có hiệu suất tốt.
    Sử dụng dual-config để áp dụng ngưỡng khác nhau cho cầu Lô và Đề.
    
    Args:
        all_data_ai: Dữ liệu toàn bộ kỳ quay
        db_name: Đường dẫn database
        
    Returns:
        String message about management results
    """
    # Get thresholds from dual-config (with fallback)
    try:
        lo_config = SETTINGS.get('lo_config', {})
        de_config = SETTINGS.get('de_config', {})
        
        lo_add_threshold = lo_config.get('add_threshold', 45.0)
        de_add_threshold = de_config.get('add_threshold', 88.0)
    except:
        # Fallback to old settings if dual-config not available
        lo_add_threshold = getattr(SETTINGS, 'AUTO_ADD_MIN_RATE', 45.0)
        de_add_threshold = 88.0
    
    enabled_count = 0
    enabled_lo_count = 0
    enabled_de_count = 0
    skipped_pinned = 0
    
    try:
        # Get all disabled bridges (is_enabled=0)
        bridges = get_all_managed_bridges(db_name, only_enabled=False)
        if not bridges:
            return "Không có cầu để quản lý."
        
        # Filter to only disabled bridges
        disabled_bridges = [b for b in bridges if b.get('is_enabled', 1) == 0]
        
        if not disabled_bridges:
            return "Không có cầu bị tắt để kiểm tra."
        
        for b in disabled_bridges:
            try:
                is_pinned = b.get("is_pinned", 0)
                if is_pinned:
                    skipped_pinned += 1
                    continue
                
                # Determine if this is a De bridge
                is_de = is_de_bridge(b)
                add_threshold = de_add_threshold if is_de else lo_add_threshold
                
                # Get K1N rate (primary metric)
                k1n_str = str(b.get("win_rate_text", "0")).replace("%", "")
                try:
                    k1n_val = float(k1n_str)
                except:
                    k1n_val = 0.0
                
                # Logic: Re-enable if K1N is above add_threshold
                should_enable = (k1n_val >= add_threshold)
                
                if should_enable:
                    update_managed_bridge(b["id"], b["description"], 1, db_name)
                    enabled_count += 1
                    if is_de:
                        enabled_de_count += 1
                    else:
                        enabled_lo_count += 1
                    
            except Exception as e_inner:
                print(f"Lỗi check cầu {b.get('name')}: {e_inner}")
                pass
                
    except Exception as e:
        return f"Lỗi quản lý cầu: {e}"
    
    msg = f"Quản lý cầu hoàn tất. Đã BẬT LẠI {enabled_count} cầu tiềm năng "
    msg += f"(Lô: {enabled_lo_count} >= {lo_add_threshold}%, Đề: {enabled_de_count} >= {de_add_threshold}%)."
    if skipped_pinned > 0:
        msg += f" Bỏ qua {skipped_pinned} cầu đã ghim."
    return msg

def init_all_756_memory_bridges_to_db(db_name=DB_NAME, progress_callback=None, enable_all=False):
    """
    Khởi tạo toàn bộ 756 cầu Bạc Nhớ vào database.
    
    Args:
        db_name: Đường dẫn database
        progress_callback: Optional callback function for progress updates
        enable_all: Nếu True, kích hoạt tất cả cầu; nếu False, để mặc định tắt
        
    Returns:
        Tuple: (success, message, added_count, error_count)
    """
    print("Khởi tạo Bạc Nhớ chuẩn V2.1...")
    loto_names = get_27_loto_names()
    added = 0
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    _ensure_core_db_columns(cursor)
    
    for i in range(len(loto_names)):
        for j in range(i, len(loto_names)):
            sid = f"LO_MEM_SUM_{loto_names[i]}_{loto_names[j]}"
            sdesc = f"Bạc Nhớ: Tổng({loto_names[i]} + {loto_names[j]})"
            cursor.execute("INSERT OR IGNORE INTO ManagedBridges (name, description, type, is_enabled) VALUES (?, ?, 'LO_MEM', ?)", (sid, sdesc, 1 if enable_all else 0))
            if cursor.rowcount > 0:
                added += 1
            
            did = f"LO_MEM_DIFF_{loto_names[i]}_{loto_names[j]}"
            ddesc = f"Bạc Nhớ: Hiệu(|{loto_names[i]} - {loto_names[j]}|)"
            cursor.execute("INSERT OR IGNORE INTO ManagedBridges (name, description, type, is_enabled) VALUES (?, ?, 'LO_MEM', ?)", (did, ddesc, 1 if enable_all else 0))
            if cursor.rowcount > 0:
                added += 1
            
    conn.commit()
    conn.close()
    return True, f"Thêm {added} cầu Bạc Nhớ chuẩn.", added, 0