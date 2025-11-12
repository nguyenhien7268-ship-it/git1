# Tên file: du-an-backup/logic/data_parser.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - SỬA LỖI IMPORT TRONG EXCEPT)
#
import json
import re
import traceback
from datetime import datetime
import sqlite3 

# (SỬA LỖI) Tách import cho đúng file
try:
    # Các hàm này ở trong db_manager
    from .db_manager import (
        setup_database, 
        delete_all_managed_bridges,
        DB_NAME
    )
    # Hàm này ở trong data_repository
    from .data_repository import (
        get_latest_ky_date
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: data_parser.py không thể import (TRY BLOCK): {e}")
    
    # (SỬA) Fallback PHẢI dùng import tương đối (dấu chấm)
    from .db_manager import (
        setup_database, 
        delete_all_managed_bridges,
        DB_NAME
    )
    from .data_repository import (
        get_latest_ky_date
    )

# ==========================================================================
# (V7.0) LOGIC TÁCH BIỆT - PHÂN TÍCH CÚ PHÁP (PARSING)
# (Các hàm còn lại giữ nguyên)
# ==========================================================================

def _parse_single_ky(ky_data, date_str, ky_str):
    giai_keys = ['gdb', 'g1', 'g2', 'g3', 'g4', 'g5', 'g6', 'g7']
    giai_values = []

    if isinstance(ky_data, dict):
        for key in giai_keys:
            giai_list = [str(g).strip() for g in ky_data.get(key, [])]
            giai_values.append(",".join(giai_list))
    
    elif isinstance(ky_data, list):
        if len(ky_data) < 8:
            print(f"Cảnh báo: Kỳ {ky_str} có định dạng text không hợp lệ (thiếu giải). Bỏ qua.")
            return None
        
        for giai_list_str in ky_data:
            giai_list = [str(g).strip() for g in giai_list_str.split('-')]
            giai_values.append(",".join(giai_list))
            
    else:
        return None 

    return tuple([ky_str, date_str] + giai_values)

def _insert_data_batch(cursor, batch_data):
    try:
        cursor.executemany("""
            INSERT INTO xo_so_data (
                ky_quay, date_str, 
                gdb, g1, g2, g3, g4, g5, g6, g7
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch_data)
        
        backtest_batch = [
            (
                row[0], # ky_quay
                row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9] # gdb -> g7
            )
            for row in batch_data
        ]
        
        cursor.executemany("""
            INSERT INTO backtest_data (
                ky_quay_A,
                gdb_A, g1_A, g2_A, g3_A, g4_A, g5_A, g6_A, g7_A
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, backtest_batch)
        
        return len(batch_data)
        
    except sqlite3.IntegrityError as e:
        print(f"Lỗi IntegrityError (có thể trùng lặp): {e}")
        return 0
    except Exception as e:
        print(f"Lỗi khi chèn hàng loạt: {e}")
        traceback.print_exc()
        return 0

# ==========================================================================
# CÁC HÀM API CHÍNH (GỌI TỪ SERVICE)
# ==========================================================================

def parse_and_insert_data(raw_data, conn, cursor):
    parsed_data = []
    delete_all_managed_bridges(cursor)
    
    try:
        data_json = json.loads(raw_data)
        print("(V7.0) Đã phát hiện định dạng JSON.")
        
        sorted_keys = sorted(data_json.keys(), key=lambda k: int(k))
        
        for ky_str in sorted_keys:
            ky_data = data_json[ky_str]
            date_str = ky_data.get('date', 'N/A') 
            parsed_ky = _parse_single_ky(ky_data, date_str, ky_str)
            if parsed_ky:
                parsed_data.append(parsed_ky)
                
    except json.JSONDecodeError:
        print("(V7.0) Không phải JSON. Đang thử định dạng Text (V6)...")
        lines = raw_data.strip().split('\n')
        current_ky_data = []
        current_ky_str = None
        current_date_str = None

        for line in lines:
            line = line.strip()
            if not line: continue

            match = re.match(r"^\s*(\d+)\s*\((.*?)\)", line)
            
            if match:
                if current_ky_str and len(current_ky_data) == 8:
                    parsed_ky = _parse_single_ky(current_ky_data, current_date_str, current_ky_str)
                    if parsed_ky:
                        parsed_data.append(parsed_ky)
                
                current_ky_str = match.group(1).strip()
                current_date_str = match.group(2).strip()
                current_ky_data = []
            
            elif (re.match(r"^\s*[\d\s-]+\s*$", line) and current_ky_str):
                if len(current_ky_data) < 8:
                    current_ky_data.append(line.replace(" ", "")) 

        if current_ky_str and len(current_ky_data) == 8:
            parsed_ky = _parse_single_ky(current_ky_data, current_date_str, current_ky_str)
            if parsed_ky:
                parsed_data.append(parsed_ky)

    if not parsed_data:
        return 0
        
    total_inserted = _insert_data_batch(cursor, parsed_data)
    
    conn.commit()
    return total_inserted


def parse_and_APPEND_data(raw_data, conn, cursor):
    latest_ky_str, latest_date_obj = get_latest_ky_date(cursor)
    print(f"(Append) Kỳ mới nhất trong DB: {latest_ky_str} ({latest_date_obj})")

    parsed_data = []
    
    try:
        data_json = json.loads(raw_data)
        print("(V7.0 - Append) Đã phát hiện định dạng JSON.")
        
        sorted_keys = sorted(data_json.keys(), key=lambda k: int(k))
        
        for ky_str in sorted_keys:
            # (SỬA LỖI) Xử lý trường hợp DB rỗng (latest_ky_str is None)
            if latest_ky_str is not None and int(ky_str) <= int(latest_ky_str):
                continue
                
            ky_data = data_json[ky_str]
            date_str = ky_data.get('date', 'N/A')
            parsed_ky = _parse_single_ky(ky_data, date_str, ky_str)
            if parsed_ky:
                parsed_data.append(parsed_ky)
                
    except json.JSONDecodeError:
        print("(V7.0 - Append) Không phải JSON. Đang thử định dạng Text (V6)...")
        lines = raw_data.strip().split('\n')
        current_ky_data = []
        current_ky_str = None
        current_date_str = None

        for line in lines:
            line = line.strip()
            if not line: continue

            match = re.match(r"^\s*(\d+)\s*\((.*?)\)", line)
            
            if match:
                ky_str_check = match.group(1).strip()
                
                # (SỬA LỖI) Xử lý trường hợp DB rỗng (latest_ky_str is None)
                if latest_ky_str is not None and int(ky_str_check) <= int(latest_ky_str):
                    current_ky_str = None 
                    continue 

                if current_ky_str and len(current_ky_data) == 8:
                    parsed_ky = _parse_single_ky(current_ky_data, current_date_str, current_ky_str)
                    if parsed_ky:
                        parsed_data.append(parsed_ky)
                
                current_ky_str = ky_str_check
                current_date_str = match.group(2).strip()
                current_ky_data = []
            
            elif (re.match(r"^\s*[\d\s-]+\s*$", line) and current_ky_str):
                if len(current_ky_data) < 8:
                    current_ky_data.append(line.replace(" ", ""))

        if current_ky_str and len(current_ky_data) == 8:
            parsed_ky = _parse_single_ky(current_ky_data, current_date_str, current_ky_str)
            if parsed_ky:
                parsed_data.append(parsed_ky)

    if not parsed_data:
        return 0
        
    total_inserted = _insert_data_batch(cursor, parsed_data)
    
    conn.commit()
    return total_inserted

def parse_and_APPEND_data_TEXT(raw_data, conn, cursor):
    latest_ky_str, latest_date_obj = get_latest_ky_date(cursor)
    print(f"(Append-Text) Kỳ mới nhất trong DB: {latest_ky_str} ({latest_date_obj})")

    parsed_data = []
    
    lines = raw_data.strip().split('\n')
    current_ky_data = []
    current_ky_str = None
    current_date_str = None

    for line in lines:
        line = line.strip()
        if not line: continue

        match = re.match(r"^\s*(?:Kỳ\s*)?(\d+)\s*\((.*?)\)", line)
        
        if match:
            ky_str_check = match.group(1).strip()
            
            if latest_ky_str is not None and int(ky_str_check) <= int(latest_ky_str):
                current_ky_str = None 
                continue 

            if current_ky_str and len(current_ky_data) == 8:
                parsed_ky = _parse_single_ky(current_ky_data, current_date_str, current_ky_str)
                if parsed_ky:
                    parsed_data.append(parsed_ky)
            
            current_ky_str = ky_str_check
            current_date_str = match.group(2).strip()
            current_ky_data = []
        
        elif (re.match(r"^\s*(GDB|G[1-7]):?\s*([\d\s-]+)\s*$", line, re.IGNORECASE) and current_ky_str):
            if len(current_ky_data) < 8:
                giai_data = re.match(r"^\s*(GDB|G[1-7]):?\s*([\d\s-]+)\s*$", line, re.IGNORECASE).group(2)
                current_ky_data.append(giai_data.replace(" ", ""))
        
        elif (re.match(r"^\s*[\d\s-]+\s*$", line) and current_ky_str):
             if len(current_ky_data) < 8:
                current_ky_data.append(line.replace(" ", ""))

    if current_ky_str and len(current_ky_data) == 8:
        parsed_ky = _parse_single_ky(current_ky_data, current_date_str, current_ky_str)
        if parsed_ky:
            parsed_data.append(parsed_ky)

    if not parsed_data:
        return 0
        
    total_inserted = _insert_data_batch(cursor, parsed_data)
    
    conn.commit()
    return total_inserted

# ==========================================================================
# (DI CHUYỂN TỪ LOTTERY_SERVICE.PY)
# ==========================================================================

def run_and_update_from_text(raw_data):
    conn = None
    try:
        conn, cursor = setup_database()
        total_keys_added = parse_and_APPEND_data_TEXT(raw_data, conn, cursor)
        conn.close()
        
        if total_keys_added > 0:
            return True, f"Đã thêm thành công {total_keys_added} kỳ mới."
        else:
            return False, "Không có kỳ nào được thêm (có thể do trùng lặp hoặc định dạng sai)."
            
    except Exception as e:
        if conn: conn.close()
        import traceback
        return False, f"Lỗi nghiêm trọng khi thêm data kỳ mới: {e}\n{traceback.format_exc()}"