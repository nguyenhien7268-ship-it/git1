import sqlite3
import re
import json
from datetime import datetime

# Import các hàm DB từ file .db_manager
try:
    from .db_manager import _process_ky_entry, setup_database
except ImportError:
    # Fallback
    try:
        from db_manager import _process_ky_entry, setup_database
    except ImportError:
        print("Lỗi: Không thể import db_manager trong data_parser.py")
        def _process_ky_entry(m, p, c): return 0
        def setup_database(d): return None, None


# ===================================================================================
# I. HÀM PARSING DỮ LIỆU
# ===================================================================================

def parse_and_insert_data(raw_json_data, conn, cursor):
    cursor.execute("DELETE FROM KyQuay")
    cursor.execute("DELETE FROM DuLieu_AI") 
    cursor.execute("DELETE FROM ManagedBridges")
    conn.commit()
    
    try:
        data_dict = json.loads(raw_json_data)
        if not isinstance(data_dict, dict):
             print(f"Lỗi đọc JSON: File không phải là một đối tượng (object).")
             return 0
    except json.JSONDecodeError as e:
        print(f"Lỗi đọc JSON: {e}")
        return 0

    total_records_ai = 0
    kyInfo = data_dict.get('kyInfo', [])
    tablesData = data_dict.get('tablesData', [])

    if not kyInfo or not tablesData or len(tablesData) < len(kyInfo) * 2:
        print("Lỗi: JSON không hợp lệ hoặc thiếu 'kyInfo'/'tablesData'.")
        return 0

    total_kys = len(kyInfo)
    print(f"Đang phân tích {total_kys} kỳ (theo thứ tự ngược)...")

    for i in range(total_kys - 1, -1, -1):
        try:
            ky_info_item = kyInfo[i]
            ma_so_ky = ky_info_item.get('kỳNumber')
            ky_date_str = ky_info_item.get('kỳDate', '00-00 00:00:00')
            ky_date_parts = ky_date_str.split()
            ngay_thang = ky_date_parts[0] if len(ky_date_parts) > 0 else '00-00'
            thoi_gian = ky_date_parts[1] if len(ky_date_parts) > 1 else '00:00:00'
            if not ma_so_ky: continue
                
            cursor.execute("INSERT OR IGNORE INTO KyQuay (MaSoKy, NgayThang, ThoiGian) VALUES (?, ?, ?)",
                           (ma_so_ky, ngay_thang, thoi_gian))

            table_index = i * 2 
            prize_table_content = tablesData[table_index].get('content')
            if not prize_table_content: continue

            total_records_ai += _process_ky_entry(ma_so_ky, prize_table_content, cursor)
        except Exception as e:
            print(f"Lỗi nghiêm trọng khi xử lý kỳ {i}: {e}")
            continue
    conn.commit()
    return total_records_ai

def parse_and_APPEND_data(raw_json_data, conn, cursor):
    try:
        data_dict = json.loads(raw_json_data)
        if not isinstance(data_dict, dict):
             return parse_and_APPEND_data_TEXT(raw_json_data, conn, cursor)
    except json.JSONDecodeError as e:
        return parse_and_APPEND_data_TEXT(raw_json_data, conn, cursor)

    total_keys_added = 0 
    kyInfo = data_dict.get('kyInfo', [])
    tablesData = data_dict.get('tablesData', [])

    if not kyInfo or not tablesData or len(tablesData) < len(kyInfo) * 2:
        return 0

    total_kys = len(kyInfo)
    print(f"Đang kiểm tra {total_kys} kỳ để thêm (append)...")
    
    for i in range(total_kys):
        try:
            ky_info_item = kyInfo[i]
            ma_so_ky = ky_info_item.get('kỳNumber')
            ky_date_str = ky_info_item.get('kỳDate', '00-00 00:00:00')
            ky_date_parts = ky_date_str.split()
            ngay_thang = ky_date_parts[0] if len(ky_date_parts) > 0 else '00-00'
            thoi_gian = ky_date_parts[1] if len(ky_date_parts) > 1 else '00:00:00'
            if not ma_so_ky: continue
                
            cursor.execute("INSERT OR IGNORE INTO KyQuay (MaSoKy, NgayThang, ThoiGian) VALUES (?, ?, ?)",
                           (ma_so_ky, ngay_thang, thoi_gian))
            
            if cursor.rowcount == 0: continue
            
            print(f"Đang thêm Kỳ mới: {ma_so_ky}")
            total_keys_added += 1

            table_index = i * 2 
            prize_table_content = tablesData[table_index].get('content')
            if not prize_table_content: continue

            _process_ky_entry(ma_so_ky, prize_table_content, cursor)
        except Exception as e:
            print(f"Lỗi nghiêm trọng khi xử lý kỳ {i}: {e}")
            continue
    conn.commit()
    return total_keys_added

def parse_and_APPEND_data_TEXT(raw_data, conn, cursor):
    ky_blocks = []
    regex_one_line = re.compile(
        r'Kỳ\s+(\d{10})(\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})[\r\n]+(.*?)(?=[\r\n]*Kỳ|\Z)',
        re.DOTALL
    )
    ky_blocks = regex_one_line.findall(raw_data)

    if not ky_blocks:
        regex_two_line = re.compile(
            r'Kỳ\s+(\d{10})[\r\n]+(\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})[\r\n]+(.*?)(?=[\r\n]*Kỳ|\Z)',
            re.DOTALL
        )
        ky_blocks = regex_two_line.findall(raw_data)

    if not ky_blocks:
        print("Không khớp định dạng chuẩn, thử fallback cuối cùng...")
        now = datetime.now()
        ma_so_ky = now.strftime("%Y%m%d%H%M%S")
        ngay_thang = now.strftime("%m-%d")
        thoi_gian = now.strftime("%H:%M:%S")
        full_content = raw_data
        real_ky_match = re.search(r'Kỳ\s+(\d{10})', raw_data)
        if real_ky_match:
            ma_so_ky = real_ky_match.group(1)
        ky_blocks = [(ma_so_ky, ngay_thang, thoi_gian, full_content)]

    total_keys_added = 0
    for ma_so_ky, ngay_thang, thoi_gian, full_content in ky_blocks:
        try:
            cursor.execute("INSERT OR IGNORE INTO KyQuay (MaSoKy, NgayThang, ThoiGian) VALUES (?, ?, ?)",
                           (ma_so_ky, ngay_thang, thoi_gian))
            if cursor.rowcount == 0:
                print(f"Bỏ qua Kỳ {ma_so_ky} (đã tồn tại).")
                continue
            total_keys_added += 1
            print(f"Đang thêm Kỳ mới: {ma_so_ky}")
        except sqlite3.IntegrityError:
            print(f"Bỏ qua Kỳ {ma_so_ky} (đã tồn tại).")
            continue

        prize_data = {}
        prize_content_block = full_content.split('\n0', 1)[0].strip()
        normalized_content = re.sub(r'[\n\t]+', ' ', prize_content_block)
        normalized_content = re.sub(r'(\d)\s*-\s*(\d)', r'\1 - \2', normalized_content)

        prize_pattern = re.compile(
            r'(Đặc Biệt|Nhất|Nhì|Ba|Bốn|Năm|Sáu|Bảy)' 
            r'\s*([\d\s-]+?)'
            r'(?=(\s*(Đặc Biệt|Nhất|Nhì|Ba|Bốn|Năm|Sáu|Bảy)|\Z))' 
        )
        matches = prize_pattern.findall(normalized_content)
        
        if matches:
            for match in matches:
                prize_name = match[0]
                prize_string = match[1].strip()
                prize_data[prize_name] = prize_string
        else:
            print(f"LỖI: Không thể trích xuất prize_data cho Kỳ {ma_so_ky}.")
            try:
                cursor.execute("DELETE FROM KyQuay WHERE MaSoKy = ?", (ma_so_ky,))
                print(f"Đã rollback (xóa) KyQuay rác: {ma_so_ky}")
                total_keys_added -= 1
            except Exception as e_del:
                print(f"Lỗi khi rollback KyQuay: {e_del}")
            continue

        if not prize_data:
             print(f"LỖI: prize_data rỗng cho Kỳ {ma_so_ky}.")
             try:
                cursor.execute("DELETE FROM KyQuay WHERE MaSoKy = ?", (ma_so_ky,))
                print(f"Đã rollback (xóa) KyQuay rác: {ma_so_ky}")
                total_keys_added -= 1
             except Exception as e_del:
                print(f"Lỗi khi rollback KyQuay: {e_del}")
             continue
        
        prize_table_content = list(prize_data.items())
        _process_ky_entry(ma_so_ky, prize_table_content, cursor)

    conn.commit()
    return total_keys_added