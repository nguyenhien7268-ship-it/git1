# Tên file: git1/logic/data_repository.py
#
# (PHIÊN BẢN V7.9.1 - Thêm Wrapper get_all_data_ai)
#
import sqlite3
import os
from datetime import datetime

# --- CẤU HÌNH ĐƯỜNG DẪN DB TUYỆT ĐỐI ---
# Lấy thư mục hiện tại của file này (thư mục logic)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Lấy thư mục gốc dự án (cha của logic)
project_root = os.path.dirname(current_dir)
# Đường dẫn thư mục data
data_dir = os.path.join(project_root, "data")
# Đường dẫn DB tuyệt đối
DB_NAME = os.path.join(data_dir, "xo_so_prizes_all_logic.db")
# ----------------------------------------

# Import các hàm xử lý cầu V17
try:
    from logic.bridges.bridges_v16 import getAllPositions_V17_Shadow, taoSTL_V30_Bong
except ImportError:
    try:
        from bridges.bridges_v16 import getAllPositions_V17_Shadow, taoSTL_V30_Bong
    except ImportError:
        def getAllPositions_V17_Shadow(row):
            return []
        def taoSTL_V30_Bong(p1, p2):
            return ["00", "00"]

# Import các hàm xử lý Memory Bridge (Bạc Nhớ)
try:
    from logic.bridges.bridges_memory import calculate_bridge_stl, get_27_loto_positions
except ImportError:
    try:
        from bridges.bridges_memory import calculate_bridge_stl, get_27_loto_positions
    except ImportError:
        def calculate_bridge_stl(loto1, loto2, algorithm_type):
            return ["00", "00"]
        def get_27_loto_positions(row):
            return ["00"] * 27

# Import re cho parsing bridge name
import re

def load_data_ai_from_db(db_name=DB_NAME):
    """Tải toàn bộ dữ liệu A:I từ DB (10 cột). Trả về (rows, message)"""
    
    if not os.path.exists(db_name):
        return (
            None,
            f"Lỗi: Không tìm thấy database '{db_name}'. Vui lòng chạy 'Nạp File' trước.",
        )

    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(
            """
        SELECT MaSoKy, Col_A_Ky, Col_B_GDB, Col_C_G1, Col_D_G2, Col_E_G3, Col_F_G4, Col_G_G5, Col_H_G6, Col_I_G7
        FROM DuLieu_AI
        ORDER BY MaSoKy ASC
        """
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return (
                None,
                f"Lỗi: Database '{db_name}' rỗng. Vui lòng chạy 'Nạp File' trước.",
            )

        return rows, f"Đã tải {len(rows)} hàng A:I từ CSDL."
    except Exception as e:
        return None, f"Lỗi SQL khi tải dữ liệu A:I: {e}"


def get_all_data_ai(db_name=DB_NAME):
    """
    (V7.9 Extension) Wrapper lấy dữ liệu A:I dạng list, bỏ qua message.
    Dùng cho các script Logic/Backend để code gọn hơn.
    """
    rows, _ = load_data_ai_from_db(db_name)
    return rows if rows else []


def get_all_managed_bridges(db_name=DB_NAME, only_enabled=False):
    """
    (V7.1) Lấy danh sách Cầu Đã Lưu (từ bảng ManagedBridges).
    Hàm này trả về dict (thay vì list) để dễ tra cứu.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        # Thiết lập row_factory để trả về dict
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql_query = "SELECT * FROM ManagedBridges"
        if only_enabled:
            sql_query += " WHERE is_enabled = 1"
        sql_query += " ORDER BY name ASC"

        cursor.execute(sql_query)
        rows = cursor.fetchall()

        # Chuyển đổi [sqlite3.Row] thành [dict]
        dict_rows = [dict(row) for row in rows]

        return dict_rows

    except Exception:
        # Nếu bảng không tồn tại hoặc lỗi, trả về danh sách rỗng
        return []
    finally:
        if conn:
            conn.close()


def get_latest_ky_date(conn):
    """
    (V7.0) Lấy KỲ và NGÀY mới nhất từ CSDL A:I để kiểm tra trùng lặp.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT ky, date FROM results_A_I ORDER BY ky DESC LIMIT 1")
        latest = cursor.fetchone()

        if latest:
            latest_ky_str = str(latest[0]).strip()
            date_str = str(latest[1]).strip()

            # Thử 1: Định dạng chuẩn dd/mm/YYYY
            try:
                latest_date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                return latest_ky_str, latest_date_obj
            except ValueError:
                pass

            # Thử 2: Định dạng chuẩn YYYY-mm-dd
            try:
                latest_date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                return latest_ky_str, latest_date_obj
            except ValueError:
                pass

            # Thử 3: Định dạng thiếu năm dd-mm (VD: 13-11)
            try:
                # Thêm năm hiện tại vào
                date_str_with_year = f"{date_str}-{datetime.now().year}"
                latest_date_obj = datetime.strptime(date_str_with_year, "%d-%m-%Y")
                return latest_ky_str, latest_date_obj
            except ValueError:
                pass

            # Thử 4: Định dạng thiếu năm dd/mm (VD: 13/11)
            try:
                # Thêm năm hiện tại vào
                date_str_with_year = f"{date_str}/{datetime.now().year}"
                latest_date_obj = datetime.strptime(date_str_with_year, "%d/%m/%Y")
                return latest_ky_str, latest_date_obj
            except ValueError:
                pass

            # Nếu tất cả thất bại
            print(f"Cảnh báo: Không thể phân tích ngày '{date_str}' từ CSDL.")

    except Exception as e:
        print(f"Lỗi get_latest_ky_date: {e}")

    return None, None


def get_bridge_by_name(bridge_name, db_name=DB_NAME):
    """
    Lấy thông tin cầu từ DB bằng tên.
    
    Args:
        bridge_name: Tên cầu
        db_name: Đường dẫn database
    
    Returns:
        dict: Thông tin cầu hoặc None nếu không tìm thấy
    """
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ManagedBridges WHERE name = ?", (bridge_name,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    except Exception as e:
        print(f"Lỗi get_bridge_by_name: {e}")
        return None
    finally:
        if conn:
            conn.close()


def get_managed_bridges_with_prediction(db_name=DB_NAME, current_data=None, only_enabled=True):
    """
    (V7.9.2) Lấy danh sách Cầu Đã Lưu và tính toán dự đoán nếu có current_data.
    Trả về danh sách cầu với next_prediction_stl đã được tính toán.
    
    Args:
        db_name: Đường dẫn database
        current_data: Dữ liệu A:I hiện tại (list các row), nếu có sẽ tính dự đoán
        only_enabled: Chỉ lấy cầu đang bật
    
    Returns:
        List[dict]: Danh sách cầu với next_prediction_stl đã được cập nhật
    """
    # Lấy danh sách cầu từ DB
    bridges = get_all_managed_bridges(db_name, only_enabled=only_enabled)
    
    # Nếu không có current_data, trả về ngay (giữ nguyên next_prediction_stl từ DB)
    if not current_data or len(current_data) == 0:
        return bridges
    
    # Lấy dòng cuối cùng để tính dự đoán
    last_row = current_data[-1]
    
    try:
        # Lấy positions từ dòng cuối
        positions = getAllPositions_V17_Shadow(last_row)
        
        # Lấy lotos từ dòng cuối cho Memory Bridge
        last_lotos = get_27_loto_positions(last_row)
        
        # Duyệt qua từng cầu và tính toán dự đoán
        for bridge in bridges:
            pos1_idx = bridge.get("pos1_idx")
            pos2_idx = bridge.get("pos2_idx")
            
            # Khởi tạo next_prediction_stl từ DB (nếu có)
            if "next_prediction_stl" not in bridge or not bridge.get("next_prediction_stl"):
                bridge["next_prediction_stl"] = "N/A"
            
            # Bỏ qua nếu không có vị trí
            if pos1_idx is None or pos2_idx is None:
                continue
            
            try:
                # Kiểm tra Memory Bridge (Bạc Nhớ)
                if pos1_idx == -1 and pos2_idx == -1:
                    bridge_name = bridge.get("name", "")
                    pred_stl = None
                    
                    # Parse và tính toán cho Memory Bridge
                    if "Tổng(" in bridge_name:
                        match = re.search(r'Tổng\((\d+)\+(\d+)\)', bridge_name)
                        if match:
                            pos1, pos2 = int(match.group(1)), int(match.group(2))
                            if pos1 < len(last_lotos) and pos2 < len(last_lotos):
                                loto1, loto2 = last_lotos[pos1], last_lotos[pos2]
                                if loto1 and loto2:
                                    pred_stl = calculate_bridge_stl(loto1, loto2, "sum")
                    elif "Hiệu(" in bridge_name:
                        match = re.search(r'Hiệu\((\d+)-(\d+)\)', bridge_name)
                        if match:
                            pos1, pos2 = int(match.group(1)), int(match.group(2))
                            if pos1 < len(last_lotos) and pos2 < len(last_lotos):
                                loto1, loto2 = last_lotos[pos1], last_lotos[pos2]
                                if loto1 and loto2:
                                    pred_stl = calculate_bridge_stl(loto1, loto2, "diff")
                    
                    if pred_stl and isinstance(pred_stl, list) and len(pred_stl) >= 2:
                        # Chuyển đổi thành chuỗi (VD: ['12', '21'] -> "12,21")
                        pred_str = ",".join(str(x) for x in pred_stl if x)
                        if pred_str:
                            bridge["next_prediction_stl"] = pred_str
                    continue
                
                # V17 Bridge (original logic)
                # Kiểm tra index hợp lệ
                if pos1_idx < len(positions) and pos2_idx < len(positions):
                    p1 = positions[pos1_idx]
                    p2 = positions[pos2_idx]
                    
                    # Bỏ qua nếu giá trị None
                    if p1 is None or p2 is None:
                        continue
                    
                    # Tính toán STL dự đoán
                    pred_stl = taoSTL_V30_Bong(int(p1), int(p2))
                    
                    # Chuyển đổi thành chuỗi (VD: ['12', '21'] -> "12,21")
                    if isinstance(pred_stl, list) and len(pred_stl) >= 2:
                        pred_str = ",".join(str(x) for x in pred_stl if x)
                        if pred_str:
                            bridge["next_prediction_stl"] = pred_str
            except (ValueError, TypeError, IndexError) as e:
                # Giữ nguyên giá trị từ DB nếu có lỗi
                pass
    except Exception as e:
        # Nếu có lỗi khi tính toán, vẫn trả về danh sách cầu (không có dự đoán)
        print(f"Lỗi khi tính toán dự đoán cầu: {e}")
    
    return bridges