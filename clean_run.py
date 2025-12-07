import os
import shutil
import sys
import time

print(">>> ĐANG DỌN DẸP FILE RÁC (CACHE)...")

# 1. Quét và xóa tất cả thư mục __pycache__
root_dir = os.path.dirname(os.path.abspath(__file__))
count = 0
for root, dirs, files in os.walk(root_dir):
    for d in dirs:
        if d == "__pycache__":
            path = os.path.join(root, d)
            try:
                shutil.rmtree(path)
                count += 1
                print(f"    Đã xóa: {path}")
            except Exception as e:
                print(f"    Lỗi xóa {path}: {e}")

print(f">>> Đã xóa {count} thư mục cache. Code mới sẽ được nạp lại 100%.")
print(">>> Đang khởi động phần mềm sau 2 giây...")
time.sleep(2)
