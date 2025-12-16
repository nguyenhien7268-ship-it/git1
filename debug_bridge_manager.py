import os
import re

def fix_dashboard_analytics():
    file_path = 'code6/logic/dashboard_analytics.py'
    
    if not os.path.exists(file_path):
        print(f"❌ Không tìm thấy file: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"🔍 Đang phân tích {file_path}...")

    # Pattern nhận diện vị trí đang tổng hợp kết quả (thường có gán win_rate)
    # Tìm đoạn gán 'win_rate' trong một dictionary
    # Pattern này tìm các dòng kiểu: stats['win_rate'] = ... hoặc 'win_rate': ...
    
    # 1. Tìm vị trí loop qua các bridge/strategy
    # Chúng ta sẽ inject logic predict vào ngay trước khi result được append hoặc return
    
    # Đoạn code chèn thêm (Inject Code)
    # Sử dụng logic an toàn: Kiểm tra method predict/predict_next
    inject_code = """
                # [AUTO-FIX] Inject prediction for UI
                try:
                    if hasattr(bridge, 'predict'):
                        # Lấy dự đoán cho ngày mới nhất
                        _pred = bridge.predict()
                        # Format list thành chuỗi nếu cần
                        if isinstance(_pred, (list, tuple)):
                            stats['prediction'] = ", ".join(map(str, _pred))
                        else:
                            stats['prediction'] = str(_pred)
                    else:
                        stats['prediction'] = "N/A"
                except Exception as e:
                    stats['prediction'] = "Err"
    """

    # Chiến thuật thay thế: Tìm dòng gán win_rate và chèn đoạn code trên ngay sau nó
    # Regex tìm dòng gán win_rate và thụt đầu dòng của nó
    pattern = r"(\s+)(.*?)['\"]win_rate['\"]\s*[:=].*?(\n)"
    
    match = re.search(pattern, content)
    
    if match:
        indentation = match.group(1)
        # Chuẩn hóa indentation cho code inject
        formatted_inject = inject_code.replace("                ", indentation)
        
        # Thực hiện chèn
        new_content = content[:match.end()] + formatted_inject + content[match.end():]
        
        # Backup file cũ
        os.rename(file_path, file_path + ".bak")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print("✅ Đã sửa file logic/dashboard_analytics.py thành công!")
        print("👉 Đã thêm logic lấy dự đoán (predict) vào bảng thống kê.")
        print(f"ℹ️ File gốc đã được backup tại: {file_path}.bak")
    else:
        print("⚠️ Không tìm thấy vị trí inject code an toàn (không thấy key 'win_rate').")
        print("Đề nghị kiểm tra thủ công hàm get_top_performing_bridges.")

if __name__ == "__main__":
    fix_dashboard_analytics()