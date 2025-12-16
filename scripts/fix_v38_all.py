# Tên file: code6/scripts/generate_digest.py
import os

# Cấu hình: Các thư mục và file cần quét
TARGET_DIRS = ['logic', 'services', 'ui', 'scripts']
TARGET_FILES = ['main_app.py', 'app_controller.py', 'config.json', 'README.md']
SKIP_DIRS = ['__pycache__', 'ml_model_files', 'DOC'] # DOC bỏ qua để giảm dung lượng thừa
OUTPUT_FILE = 'PROJECT_FULL_CONTEXT.txt'

def generate_digest():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    output_path = os.path.join(root_dir, OUTPUT_FILE)
    
    print(f"🚀 Đang tạo hồ sơ dự án tại: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as outfile:
        # 1. Ghi cấu trúc thư mục
        outfile.write("=== PROJECT STRUCTURE ===\n")
        for root, dirs, files in os.walk(root_dir):
            # Lọc thư mục ẩn/bỏ qua
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in SKIP_DIRS]
            level = root.replace(root_dir, '').count(os.sep)
            indent = ' ' * 4 * (level)
            outfile.write(f"{indent}{os.path.basename(root)}/\n")
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                if not f.startswith('.') and not f.endswith('.pyc'):
                    outfile.write(f"{subindent}{f}\n")
        
        outfile.write("\n" + "="*50 + "\n\n")

        # 2. Ghi nội dung file code quan trọng
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in SKIP_DIRS]
            
            # Chỉ lấy các thư mục mục tiêu hoặc file gốc
            rel_dir = os.path.relpath(root, root_dir)
            if rel_dir == '.' or any(rel_dir.startswith(d) for d in TARGET_DIRS):
                for file in files:
                    if file.endswith('.py') or file in TARGET_FILES:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, root_dir)
                        
                        outfile.write(f"=== FILE: {rel_path} ===\n")
                        try:
                            with open(file_path, 'r', encoding='utf-8') as infile:
                                content = infile.read()
                                outfile.write(content)
                        except Exception as e:
                            outfile.write(f"[Error reading file: {e}]")
                        outfile.write("\n\n" + "-"*50 + "\n\n")

    print(f"✅ Hoàn tất! File '{OUTPUT_FILE}' đã sẵn sàng.")
    print("👉 Bạn hãy upload file này lên Gemini để AI hiểu toàn bộ dự án ngay lập tức.")

if __name__ == "__main__":
    generate_digest()