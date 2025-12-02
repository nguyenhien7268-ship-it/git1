import sqlite3
import os
import sys

# Setup đường dẫn
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logic.db_manager import DB_NAME

def analyze_bridge_names():
    print(f"📡 ĐANG KIỂM TRA DATABASE: {DB_NAME}")
    if not os.path.exists(DB_NAME):
        print("❌ Không tìm thấy Database.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Lấy mẫu tất cả các loại tiền tố đang tồn tại
    print("\n📊 PHÂN TÍCH CẤU TRÚC TÊN CẦU (NAMING STRUCTURE):")
    print(f"{'PREFIX (Tiền tố)':<20} | {'SỐ LƯỢNG':<10} | {'VÍ DỤ MẪU (Sample ID)':<30}")
    print("-" * 70)

    # Logic: Lấy phần text trước dấu gạch dưới đầu tiên (hoặc 2 dấu đầu) để nhóm
    data = {}
    cursor.execute("SELECT name FROM ManagedBridges")
    all_names = cursor.fetchall()

    for row in all_names:
        name = row[0]
        # Tách tiền tố: Lấy 2 phần đầu (VD: DE_DYN, LO_STL, GDB...)
        parts = name.split('_')
        if len(parts) >= 2:
            prefix = f"{parts[0]}_{parts[1]}"
        else:
            prefix = "UNKNOWN/OTHER"
        
        if prefix not in data:
            data[prefix] = {"count": 0, "sample": name}
        data[prefix]["count"] += 1

    # In kết quả
    for prefix, info in data.items():
        print(f"{prefix:<20} | {info['count']:<10} | {info['sample']:<30}")

    print("-" * 70)
    
    # 2. Đánh giá nhanh
    print("\n🧐 ĐÁNH GIÁ NHANH:")
    safe = True
    for prefix in data.keys():
        if not (prefix.startswith("DE_") or prefix.startswith("LO_")):
            print(f"   ⚠️  CẢNH BÁO: Nhóm '{prefix}' có vẻ sai quy chuẩn (Không bắt đầu bằng DE_ hoặc LO_)")
            safe = False
    
    if safe:
        print("   ✅ TUYỆT VỜI! Tất cả các cầu đều tuân thủ chuẩn hệ thống (DE_... hoặc LO_...)")
    else:
        print("   👉 Cần xử lý các nhóm bị cảnh báo ở trên.")

    conn.close()

if __name__ == "__main__":
    analyze_bridge_names()