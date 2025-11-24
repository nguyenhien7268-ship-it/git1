# Tên file: git3/logic/data_parser.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - SỬA W503)
#
import json
import re
import sqlite3
import traceback
from datetime import datetime

# (SỬA LỖI) Tách import cho đúng file (Sử dụng import V6)
try:
    from .data_repository import get_latest_ky_date
    from .db_manager import delete_all_managed_bridges, setup_database
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: data_parser.py không thể import (TRY BLOCK): {e}")

    # Fallback
    from .data_repository import get_latest_ky_date
    from .db_manager import delete_all_managed_bridges, setup_database

# ==========================================================================
# (V6) LOGIC TÁCH BIỆT - PHÂN TÍCH CÚ PHÁP (PARSING)
# (Sử dụng lại hàm _parse_single_ky V6 để lấy 27 lô)
# ==========================================================================


def _parse_single_ky(ky_data, date_str, ky_str):
    """
    (NÂNG CẤP V6) Phân tích 1 kỳ, trích xuất 8 giải (chuẩn hóa) và 27 lô.
    Hỗ trợ 3 định dạng:
    1. JSON V7 (ky_data là list 8 chuỗi)
    2. JSON Web (ky_data là list 8 list con [["ĐB", "123"], ...])
    3. Text Paste (ky_data là list 8 chuỗi)
    """
    try:
        # 1. Xử lý Kỳ (ky)
        ky_str = str(ky_str).strip()
        if not ky_str:
            return None

        # 2. Xử lý Ngày (date)
        date_str = str(date_str).strip()
        dt = None
        try:
            # Thử 1: Định dạng V7 / Text Paste (DD/MM/YYYY)
            dt = datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            try:
                # Thử 2: Định dạng Web JSON (DD-MM HH:MM:SS) - Tự thêm năm hiện tại
                partial_date = date_str.split(" ")[0]  # Lấy "DD-MM"
                current_year = datetime.now().year
                full_date_str = f"{partial_date}-{current_year}"
                dt = datetime.strptime(full_date_str, "%d-%m-%Y")
            except ValueError:
                # (SỬA LỖI V3) Fallback cho các định dạng ngày khác (ví dụ: '08-11 23:59:29' từ 8 11.json)
                try:
                    partial_date = date_str.split(" ")[0]  # Lấy "DD-MM"
                    current_year = datetime.now().year
                    full_date_str = f"{partial_date}-{current_year}"
                    dt = datetime.strptime(full_date_str, "%m-%d-%Y")  # Thử MM-DD-YYYY
                except ValueError:
                    print(
                        f"Bỏ qua kỳ {ky_str}: Định dạng ngày không hợp lệ '{date_str}'"
                    )
                    return None

        date_sql = dt.strftime("%Y-%m-%d")

        # 3. Xử lý 8 Giải (giai) - (NÂNG CẤP V6)
        prize_data_dict = {}
        giai_keys_v7 = ["gdb", "g1", "g2", "g3", "g4", "g5", "g6", "g7"]

        if isinstance(ky_data, list) and len(ky_data) == 8:
            # Kiểm tra xem đây là format [["ĐB", "123"], ...] (Web JSON)
            if isinstance(ky_data[0], list) and len(ky_data[0]) >= 2:
                # (Sửa V6) Chuyển tên giải V6 (Đặc Biệt) sang V7 (gdb)
                prize_map = {
                    "đặc biệt": "gdb",
                    "nhất": "g1",
                    "nhì": "g2",
                    "ba": "g3",
                    "bốn": "g4",
                    "năm": "g5",
                    "sáu": "g6",
                    "bảy": "g7",
                }
                temp_dict = {}
                for prize in ky_data:
                    temp_dict[prize[0].lower()] = prize[1]

                for key_v6, key_v7 in prize_map.items():
                    prize_data_dict[key_v7] = temp_dict.get(key_v6, "")

            # Hay format ["123", "456", ...] (V7 JSON hoặc Text Paste)
            elif isinstance(ky_data[0], str):
                prize_data_dict = dict(zip(giai_keys_v7, ky_data))  # "gdb", "g1"...

        if not prize_data_dict:
            print(f"Bỏ qua kỳ {ky_str}: Lỗi cấu trúc ky_data không xác định.")
            return None

        # (LOGIC V6 CŨ) Trích xuất tường minh và chuẩn hóa dấu phẩy
        gdb_str = prize_data_dict.get("gdb", "")
        g1_str = prize_data_dict.get("g1", "")
        g2_str = prize_data_dict.get("g2", "")
        g3_str = prize_data_dict.get("g3", "")
        g4_str = prize_data_dict.get("g4", "")
        g5_str = prize_data_dict.get("g5", "")
        g6_str = prize_data_dict.get("g6", "")
        g7_str = prize_data_dict.get("g7", "")

        # (LOGIC V6 CŨ) Dùng re.findall (logic V6) để trích xuất CHUỖI SỐ
        gdb_nums = re.findall(r"\d+", gdb_str)
        g1_nums = re.findall(r"\d+", g1_str)
        g2_nums = re.findall(r"\d+", g2_str)
        g3_nums = re.findall(r"\d+", g3_str)
        g4_nums = re.findall(r"\d+", g4_str)
        g5_nums = re.findall(r"\d+", g5_str)
        g6_nums = re.findall(r"\d+", g6_str)
        g7_nums = re.findall(r"\d+", g7_str)

        # Chuẩn hóa DB (dùng dấu phẩy)
        giai_values_for_db = [
            ",".join(gdb_nums),
            ",".join(g1_nums),
            ",".join(g2_nums),
            ",".join(g3_nums),
            ",".join(g4_nums),
            ",".join(g5_nums),
            ",".join(g6_nums),
            ",".join(g7_nums),
        ]

        # 4. Trích xuất Lô (An toàn - Giới hạn số lượng)
        lotos = []

        # (LOGIC V6 CŨ) Giới hạn số lượng lô cho từng giải
        lotos.extend([num[-2:].zfill(2) for num in gdb_nums][:1])  # 1 Lô
        lotos.extend([num[-2:].zfill(2) for num in g1_nums][:1])  # 1 Lô
        lotos.extend([num[-2:].zfill(2) for num in g2_nums][:2])  # 2 Lô
        lotos.extend([num[-2:].zfill(2) for num in g3_nums][:6])  # 6 Lô
        lotos.extend([num[-2:].zfill(2) for num in g4_nums][:4])  # 4 Lô
        lotos.extend([num[-2:].zfill(2) for num in g5_nums][:6])  # 6 Lô
        lotos.extend([num[-2:].zfill(2) for num in g6_nums][:3])  # 3 Lô
        lotos.extend([num[-2:].zfill(2) for num in g7_nums][:4])  # 4 Lô

        # 5. Kiểm tra 27 Lô
        if len(lotos) != 27:
            print(f"Bỏ qua kỳ {ky_str}: Không đủ 27 lô (tìm thấy {len(lotos)}).")
            return None

        # 6. Tạo Hàng (Row) cho CSDL (37 cột)
        row_A_I = [ky_str, date_sql] + giai_values_for_db + lotos

        return tuple(row_A_I)

    except Exception as e:
        print(f"LỖI _parse_single_ky (Kỳ {ky_str}, Ngày {date_str}): {e}")
        print(traceback.format_exc())
        return None


def _insert_data_batch(cursor, data_list):
    """
    (SỬA LỖI V3) Chèn hàng loạt vào 2 bảng V6: results_A_I và DuLieu_AI
    """
    if not data_list:
        return 0

    # 1. Dọn dẹp Cầu Đã Lưu (vì nạp lại từ đầu)
    # (SỬA LỖI V3) Truyền cursor.connection (conn) thay vì cursor
    delete_all_managed_bridges(cursor.connection)

    # 2. Chuẩn bị câu lệnh SQL

    # (V6) Cần 37 placeholders (1 ky + 1 date + 8 giai + 27 lotos)
    placeholders_37 = ", ".join(["?"] * 37)

    # (V6) Tên cột INSERT (37 cột) cho results_A_I
    query_A_I = f"""
    INSERT OR IGNORE INTO results_A_I (
        ky, date,
        gdb, g1, g2, g3, g4, g5, g6, g7,
        l0, l1, l2, l3, l4, l5, l6, l7, l8, l9,
        l10, l11, l12, l13, l14, l15, l16, l17, l18, l19,
        l20, l21, l22, l23, l24, l25, l26
    ) VALUES (
        {placeholders_37}
    )"""

    # (SỬA LỖI V3) Chuẩn bị data cho DuLieu_AI (10 cột)
    # data_list row format: (ky, date, gdb, g1..g7, l0..l26)
    dulieu_ai_batch = [
        (
            row[0],  # MaSoKy (ky)
            row[0],  # Col_A_Ky (ky)
            row[2],
            row[3],
            row[4],
            row[5],
            row[6],
            row[7],
            row[8],
            row[9],  # gdb (Col_B) -> g7 (Col_I)
        )
        for row in data_list
    ]

    query_DuLieu_AI = """
    INSERT OR IGNORE INTO DuLieu_AI (
        MaSoKy, Col_A_Ky,
        Col_B_GDB, Col_C_G1, Col_D_G2, Col_E_G3,
        Col_F_G4, Col_G_G5, Col_H_G6, Col_I_G7
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    try:
        # Chèn A:I (38 cột)
        cursor.executemany(query_A_I, data_list)
        count_A_I = cursor.rowcount  # Trả về số hàng A:I đã chèn

        # Chèn A:I (10 cột)
        cursor.executemany(query_DuLieu_AI, dulieu_ai_batch)

        return count_A_I

    except sqlite3.IntegrityError as e:
        print(f"Lỗi Integrity (Trùng lặp) khi chèn batch: {e}")
        return 0
    except Exception as e:
        print(f"Lỗi _insert_data_batch (V6 schema): {e}")
        print(traceback.format_exc())
        return 0


def _insert_data_batch_APPEND(cursor, data_list):
    """
    (SỬA LỖI V3) Chèn hàng loạt (APPEND) vào 2 bảng V6: results_A_I và DuLieu_AI.
    KHÔNG XÓA CẦU.
    """
    if not data_list:
        return 0

    # (V6) Cần 37 placeholders
    placeholders_37 = ", ".join(["?"] * 37)

    query_A_I = f"""
    INSERT OR IGNORE INTO results_A_I (
        ky, date,
        gdb, g1, g2, g3, g4, g5, g6, g7,
        l0, l1, l2, l3, l4, l5, l6, l7, l8, l9,
        l10, l11, l12, l13, l14, l15, l16, l17, l18, l19,
        l20, l21, l22, l23, l24, l25, l26
    ) VALUES (
        {placeholders_37}
    )"""

    # (SỬA LỖI V3) Chuẩn bị data cho DuLieu_AI (10 cột)
    dulieu_ai_batch = [
        (
            row[0],  # MaSoKy (ky)
            row[0],  # Col_A_Ky (ky)
            row[2],
            row[3],
            row[4],
            row[5],
            row[6],
            row[7],
            row[8],
            row[9],  # gdb (Col_B) -> g7 (Col_I)
        )
        for row in data_list
    ]

    query_DuLieu_AI = """
    INSERT OR IGNORE INTO DuLieu_AI (
        MaSoKy, Col_A_Ky,
        Col_B_GDB, Col_C_G1, Col_D_G2, Col_E_G3,
        Col_F_G4, Col_G_G5, Col_H_G6, Col_I_G7
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    try:
        cursor.executemany(query_A_I, data_list)
        count_A_I = cursor.rowcount

        cursor.executemany(query_DuLieu_AI, dulieu_ai_batch)

        return count_A_I

    except Exception as e:
        print(f"Lỗi _insert_data_batch_APPEND (V6 schema): {e}")
        print(traceback.format_exc())
        return 0


# ==========================================================================
# (V7) API: HÀM CHÍNH (GỌI TỪ CONTROLLER)
# (Sử dụng logic phát hiện JSON V7, nhưng gọi hàm parse V6)
# ==========================================================================


def parse_and_insert_data(raw_data, conn, cursor):
    """
    (MERGE V7+V6) API: Tự động phát hiện định dạng (V7 hoặc Web JSON) và chèn vào DB.
    XÓA HẾT CẦU ĐÃ LƯU.
    """
    parsed_data = []
    # (SỬA LỖI V3) Gọi bằng conn (Connection) thay vì cursor (Cursor)
    delete_all_managed_bridges(conn)

    try:
        data = json.loads(raw_data)

        # THỬ 1: ĐỊNH DẠNG V7 ({"data": {"ky": ...}})
        if "data" in data and "ky" in data["data"]:
            print("(V7.0) Đã phát hiện định dạng JSON (V7).")
            v7_data = data["data"]["ky"]
            sorted_keys = sorted(v7_data.keys(), key=lambda k: int(k))
            for ky_str in sorted_keys:
                ky_info = v7_data[ky_str]
                date_str = ky_info.get("date", "")
                giai_data = ky_info.get("giai", [])  # Đây là list: ["123", "456"]

                # (SỬA V3) Gọi hàm _parse_single_ky (V6) để lấy 27 lô
                parsed_ky = _parse_single_ky(giai_data, date_str, ky_str)
                if parsed_ky:
                    parsed_data.append(parsed_ky)

        # (SỬA LỖI V2) THỬ 2: ĐỊNH DẠNG WEB JSON ({"kyInfo": [...], "tablesData": [...]})
        elif "kyInfo" in data and "tablesData" in data:  # <-- 1. Sửa tên key
            print("(V7.0) Đã phát hiện định dạng JSON (Web).")
            ky_info_list = data["kyInfo"]
            tables_data_list = data["tablesData"]  # <-- 1. Sửa tên key

            # (SỬA LỖI V2) Kiểm tra tỷ lệ 1:2 (1 kỳ : 2 bảng)
            if len(ky_info_list) * 2 != len(tables_data_list):
                print(
                    f"Lỗi: JSON (Web) không khớp. kyInfo ({len(ky_info_list)}) và tablesData ({len(tables_data_list)}) không theo tỷ lệ 1:2."
                )

            else:
                combined_list = []
                for i in range(len(ky_info_list)):
                    ky_str_check = ky_info_list[i].get("kỳNumber")
                    if ky_str_check and ky_str_check.isdigit():
                        # (SỬA LỖI V2) Ghép kyInfo[i] với Bảng Giải Thưởng (tablesData[i*2])
                        combined_list.append(
                            (
                                int(ky_str_check),
                                ky_info_list[i],
                                tables_data_list[i * 2],
                            )
                        )

                combined_list.sort(key=lambda x: x[0])  # Sắp xếp theo kỳ

                for ky_int, ky_info, table_data in combined_list:
                    ky_str = str(ky_int)
                    date_str = ky_info.get("kỳDate")  # "DD-MM HH:MM:SS"
                    content = table_data.get(
                        "content", []
                    )  # [["Đặc Biệt", "33963"], ...]

                    # <<< BỘ CHUYỂN ĐỔI (ADAPTER) >>>
                    # Chuyển [["ĐB", "123"], ...] THÀNH ["123", "456", ...]
                    giai_data_list = []
                    # (SỬA LỖI V2) Kiểm tra kỹ đây là bảng giải (có "Đặc Biệt")
                    if (
                        isinstance(content, list)
                        and len(content) == 8
                        and isinstance(content[0], list)
                        and len(content[0]) >= 2
                        and ("Đặc Biệt" in content[0][0] or "GDB" in content[0][0])
                    ):

                        for giai_pair in content:
                            giai_data_list.append(
                                giai_pair[1]
                            )  # Chỉ lấy chuỗi số (ví dụ: "13173 -23763")

                        # (SỬA V3) Gọi hàm _parse_single_ky (V6) để lấy 27 lô
                        parsed_ky = _parse_single_ky(giai_data_list, date_str, ky_str)
                        if parsed_ky:
                            parsed_data.append(parsed_ky)
                    else:
                        print(
                            f"Bỏ qua kỳ {ky_str}: Lỗi định dạng (Web), không phải bảng giải thưởng (index chẵn)."
                        )

        else:
            # (SỬA V3) Nếu không phải 2 dạng trên, thử dạng Text V6
            print("(V7.0) Không phải JSON V7/Web. Đang thử định dạng Text (V6)...")
            # (SỬA V3) Gọi hàm parse TEXT (V6)
            # Lưu ý: Hàm này APPEND, nhưng vì đã gọi delete_all_managed_bridges
            # và _insert_data_batch sẽ chèn (không IGNORE) nên vẫn đúng
            total_inserted = parse_and_APPEND_data_TEXT(raw_data, conn, cursor)
            conn.commit()
            return total_inserted

    except json.JSONDecodeError:
        # (SỬA V3) Nếu JSON lỗi -> Thử Text V6
        print("(V7.0) Không phải JSON. Đang thử định dạng Text (V6)...")
        total_inserted = parse_and_APPEND_data_TEXT(raw_data, conn, cursor)
        conn.commit()
        return total_inserted
    except Exception as e:
        print(f"Lỗi parse_and_insert_data (JSON V7/Web): {e}")
        traceback.print_exc()
        return 0

    # (SỬA V3) Chỉ chạy nếu là JSON V7 hoặc Web
    if not parsed_data:
        return 0

    total_inserted = _insert_data_batch(cursor, parsed_data)

    conn.commit()
    return total_inserted


def parse_and_APPEND_data(raw_data, conn, cursor):
    """
    (MERGE V7+V6) API: Tự động phát hiện (V7 hoặc Web JSON) và chèn (APPEND).
    KHÔNG XÓA CẦU ĐÃ LƯU. (Dùng INSERT OR IGNORE)
    """
    # =========================================================================
    # (SỬA LỖI V8) Đổi cursor thành conn
    latest_ky_str, latest_date_obj = get_latest_ky_date(conn)
    # =========================================================================
    print(f"(Append) Kỳ mới nhất trong DB: {latest_ky_str} ({latest_date_obj})")

    parsed_data = []

    try:
        data = json.loads(raw_data)

        # THỬ 1: ĐỊNH DẠNG V7 ({"data": {"ky": ...}})
        if "data" in data and "ky" in data["data"]:
            print("(V7.0 - Append) Đã phát hiện định dạng JSON (V7).")
            v7_data = data["data"]["ky"]
            sorted_keys = sorted(v7_data.keys(), key=lambda k: int(k))  # Sort keys
            for ky_str in sorted_keys:
                if latest_ky_str is not None and int(ky_str) <= int(latest_ky_str):
                    continue

                ky_info = v7_data[ky_str]
                date_str = ky_info.get("date", "")
                giai_data = ky_info.get("giai", [])  # list: ["123", "456"]
                parsed_ky = _parse_single_ky(giai_data, date_str, ky_str)
                if parsed_ky:
                    parsed_data.append(parsed_ky)

        # (SỬA LỖI V2) THỬ 2: ĐỊNH DẠNG WEB JSON ({"kyInfo": [...], "tablesData": [...]})
        elif "kyInfo" in data and "tablesData" in data:  # <-- 1. Sửa tên key
            print("(V7.0 - Append) Đã phát hiện định dạng JSON (Web).")
            ky_info_list = data["kyInfo"]
            tables_data_list = data["tablesData"]  # <-- 1. Sửa tên key

            # (SỬA LỖI V2) Kiểm tra tỷ lệ 1:2
            if len(ky_info_list) * 2 != len(tables_data_list):
                print(
                    f"Lỗi: JSON (Web) không khớp. kyInfo ({len(ky_info_list)}) và tablesData ({len(tables_data_list)}) không theo tỷ lệ 1:2."
                )

            else:
                combined_list = []
                for i in range(len(ky_info_list)):
                    ky_str_check = ky_info_list[i].get("kỳNumber")
                    if ky_str_check and ky_str_check.isdigit():
                        # (SỬA LỖI V2) Ghép kyInfo[i] với Bảng Giải Thưởng (tablesData[i*2])
                        combined_list.append(
                            (
                                int(ky_str_check),
                                ky_info_list[i],
                                tables_data_list[i * 2],
                            )
                        )

                combined_list.sort(key=lambda x: x[0])  # Sắp xếp theo kỳ

                for ky_int, ky_info, table_data in combined_list:
                    ky_str = str(ky_int)

                    if latest_ky_str is not None and ky_int <= int(latest_ky_str):
                        continue

                    date_str = ky_info.get("kỳDate")  # "DD-MM HH:MM:SS"
                    content = table_data.get(
                        "content", []
                    )  # [["Đặc Biệt", "33963"], ...]

                    # <<< BỘ CHUYỂN ĐỔI (ADAPTER) >>>
                    giai_data_list = []
                    # (SỬA LỖI V2) Kiểm tra kỹ đây là bảng giải (có "Đặc Biệt")
                    if (
                        isinstance(content, list)
                        and len(content) == 8
                        and isinstance(content[0], list)
                        and len(content[0]) >= 2
                        and ("Đặc Biệt" in content[0][0] or "GDB" in content[0][0])
                    ):

                        for giai_pair in content:
                            giai_data_list.append(giai_pair[1])  # Chỉ lấy số

                        parsed_ky = _parse_single_ky(giai_data_list, date_str, ky_str)
                        if parsed_ky:
                            parsed_data.append(parsed_ky)
                    else:
                        print(
                            f"Bỏ qua kỳ {ky_str}: Lỗi định dạng (Web), không phải bảng giải thưởng (index chẵn)."
                        )

        else:
            # (SỬA V3) Nếu không phải 2 dạng trên, thử dạng Text V6
            print(
                "(V7.0 - Append) Không phải JSON V7/Web. Đang thử định dạng Text (V6)..."
            )
            total_inserted = parse_and_APPEND_data_TEXT(raw_data, conn, cursor)
            conn.commit()
            return total_inserted

    except json.JSONDecodeError:
        # (SỬA V3) Nếu JSON lỗi -> Thử Text V6
        print("(V7.0 - Append) Không phải JSON. Đang thử định dạng Text (V6)...")
        total_inserted = parse_and_APPEND_data_TEXT(raw_data, conn, cursor)
        conn.commit()
        return total_inserted
    except Exception as e:
        print(f"Lỗi parse_and_APPEND_data (JSON V7/Web): {e}")
        traceback.print_exc()
        return 0

    # (SỬA V3) Chỉ chạy nếu là JSON V7 hoặc Web
    if not parsed_data:
        return 0

    # (SỬA V3) Gọi hàm APPEND V6
    total_inserted = _insert_data_batch_APPEND(cursor, parsed_data)

    conn.commit()
    return total_inserted


def parse_and_APPEND_data_TEXT(raw_data, conn, cursor):
    """
    (NÂNG CẤP V6) API: Phân tích dữ liệu TEXT (dán tay) và chèn vào DB.
    (SỬA LỖI V9) Hỗ trợ định dạng dtky.txt (Web Text) VÀ xử lý ngắt dòng.
    """
    parsed_data = []
    current_ky_str = None
    current_date_str = None
    current_ky_data = []  # Lưu 8 chuỗi giải

    # Lấy ngày/kỳ mới nhất từ DB để lọc trùng
    # =========================================================================
    # (SỬA LỖI V8) Đổi cursor thành conn
    latest_ky, latest_date = get_latest_ky_date(conn)
    # =========================================================================
    latest_ky_int = 0
    if latest_ky and latest_ky.isdigit():
        latest_ky_int = int(latest_ky)

    lines = raw_data.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # (Sửa V7) Hỗ trợ cả 2 định dạng:
        # 1. Kỳ 123(DD/MM/YYYY)
        ky_match_v7 = re.match(r"^\s*(?:Kỳ\s*)?(\d+)\s*\((.*?)\)", line)
        # 2. Kỳ #123 - Ngày DD/MM/YYYY
        ky_match_v6 = re.match(
            r"(?:Kỳ|kỳ)\s*#?(\d+)\s*-\s*Ngày\s*(\d{1,2}/\d{1,2}/\d{4})", line
        )

        # (SỬA LỖI V11) Sửa Regex, xóa \s* và chỉ định \d{10} cho Kỳ
        # Ví dụ: Kỳ 251118030017-11 19:29:29 (Dính liền)
        ky_match_web = re.match(
            r"^\s*(?:Kỳ\s*)?(\d{10})(\d{1,2}-\d{1,2}\s+\d{2}:\d{2}:\d{2})", line
        )

        match_found = None
        if ky_match_v7:
            match_found = ky_match_v7
        elif ky_match_v6:
            match_found = ky_match_v6
        # (SỬA LỖI V8) Ưu tiên 3
        elif ky_match_web:
            match_found = ky_match_web

        if match_found:
            # Nếu đang có 1 kỳ cũ, lưu nó lại
            if current_ky_str and len(current_ky_data) == 8:
                parsed_ky = _parse_single_ky(
                    current_ky_data, current_date_str, current_ky_str
                )
                if parsed_ky:
                    parsed_data.append(parsed_ky)

            # Bắt đầu kỳ mới
            current_ky_str = match_found.group(1).strip()
            current_date_str = match_found.group(2).strip()
            current_ky_data = []

            # =========================================================================
            # (SỬA LỖI V12) BẬT LẠI KIỂM TRA TRÙNG LẶP
            try:
                ky_to_check = current_ky_str

                if int(ky_to_check) <= latest_ky_int:
                    current_ky_str = None  # Reset để bỏ qua các dòng giải
                    continue
            except ValueError:
                pass  # Bỏ qua nếu ky không phải số
            continue
            # =========================================================================

        # =========================================================================
        # (SỬA LỖI V9) Logic bắt giải thưởng (hỗ trợ "Nhất", "Nhì"...)
        giai_match = re.match(
            r"^(GĐB|ĐB|Đặc Biệt|G[1-7]|Nhất|Nhì|Ba|Bốn|Năm|Sáu|Bảy)\b",
            line,
            re.IGNORECASE,
        )

        if giai_match and current_ky_str:
            giai_data = line[giai_match.end(0):].strip()
            giai_keyword = giai_match.group(1).upper()

            # Nếu là GĐB/ĐB/Đặc Biệt -> Phải là giải đầu tiên (reset)
            if "ĐB" in giai_keyword or "ĐẶC BIỆT" in giai_keyword:
                if giai_data:
                    current_ky_data = [giai_data]

            # Nếu là các giải khác (Nhất, Nhì, G1, G2...)
            elif len(current_ky_data) > 0 and len(current_ky_data) < 8:
                if giai_data:
                    current_ky_data.append(giai_data)

            continue  # Đã xử lý xong dòng này

        # (SỬA LỖI V9) Xử lý các dòng bị ngắt (ví dụ: -659)
        # Chỉ bắt các dòng CHỈ CÓ SỐ / DẤU CÁCH / DẤU GẠCH (KHÔNG CÓ DẤU PHẨY)
        elif re.match(r"^[ \d-]+$", line) and current_ky_str:
            giai_data = line.strip()
            # NẾU dòng này là số/gạch VÀ CÓ giải trước đó
            if giai_data and current_ky_data:
                current_ky_data[-1] = current_ky_data[-1] + " " + giai_data
            continue  # Đã xử lý xong dòng này

        # Các dòng Lô rác (ví dụ: 0 7,6) sẽ bị bỏ qua
        # vì chúng không khớp với bất kỳ regex nào ở trên.
        # =========================================================================

    if current_ky_str and len(current_ky_data) == 8:
        parsed_ky = _parse_single_ky(current_ky_data, current_date_str, current_ky_str)
        if parsed_ky:
            parsed_data.append(parsed_ky)

    if not parsed_data:
        return 0

    total_inserted = _insert_data_batch_APPEND(cursor, parsed_data)

    # conn.commit() # Hàm cha sẽ commit
    return total_inserted


# ==========================================================================
# (DI CHUYỂN TỪ LOTTERY_SERVICE.PY)
# ==========================================================================


def run_and_update_from_text(raw_data):
    # ==========================================================
    print("ĐANG CHẠY CODE V11 (BẢN ỔN ĐỊNH). BẮT ĐẦU PARSE...")
    # ==========================================================
    conn = None
    try:
        conn, cursor = setup_database()
        total_keys_added = parse_and_APPEND_data_TEXT(raw_data, conn, cursor)
        conn.commit()  # (Sửa V7) Commit ở đây
        conn.close()

        if total_keys_added > 0:
            return True, f"Đã thêm thành công {total_keys_added} kỳ mới."
        else:
            return (
                False,
                "Không có kỳ nào được thêm (có thể do trùng lặp, sai định dạng, hoặc file rỗng).",
            )
    except Exception as e:
        if conn:
            conn.close()
        return (
            False,
            f"Lỗi nghiêm trọng khi thêm từ text: {e}\n{traceback.format_exc()}",
        )


class DataParser:
    def get_positions_map(self, row) -> list:
        """
        Lấy mảng phẳng 107 con số từ tất cả các giải (GDB -> G7).
        Logic map vị trí chuẩn V16 (Google Script).
        """
        positions = []
        try:
            def parse_digits(val):
                if not val: return []
                s = str(val)
                return [int(d) for d in s if d.isdigit()]
            # 1. GĐB (5 số)
            positions.extend(parse_digits(row.get('GDB', ''))[:5])
            while len(positions) < 5: positions.append(0)
            # 2. G1 (5 số)
            positions.extend(parse_digits(row.get('G1', ''))[:5])
            while len(positions) < 10: positions.append(0)
            # 3. G2 (2 giải * 5)
            g2 = str(row.get('G2', '')).split(',')
            for g in g2: positions.extend(parse_digits(g)[:5])
            while len(positions) < 20: positions.append(0)
            # 4. G3 (6 giải * 5)
            g3 = str(row.get('G3', '')).split(',')
            for g in g3: positions.extend(parse_digits(g)[:5])
            while len(positions) < 50: positions.append(0)
            # 5. G4 (4 giải * 4)
            g4 = str(row.get('G4', '')).split(',')
            for g in g4: positions.extend(parse_digits(g)[:4])
            while len(positions) < 66: positions.append(0)
            # 6. G5 (6 giải * 4)
            g5 = str(row.get('G5', '')).split(',')
            for g in g5: positions.extend(parse_digits(g)[:4])
            while len(positions) < 90: positions.append(0)
            # 7. G6 (3 giải * 3)
            g6 = str(row.get('G6', '')).split(',')
            for g in g6: positions.extend(parse_digits(g)[:3])
            while len(positions) < 99: positions.append(0)
            # 8. G7 (4 giải * 2)
            g7 = str(row.get('G7', '')).split(',')
            for g in g7: positions.extend(parse_digits(g)[:2])
            # Cắt hoặc bù cho đủ 107
            if len(positions) > 107: positions = positions[:107]
            while len(positions) < 107: positions.append(0)
            return positions
        except Exception as e:
            print(f"Parser Error: {e}")
            return [0] * 107