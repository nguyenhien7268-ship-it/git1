import os

# Cấu hình
PROJECT_DIR = "."  # Thư mục hiện tại
EXCLUDE_DIRS = {'__pycache__', '.git', '.idea', 'venv', 'backups', 'archive'}
EXCLUDE_FILES = {'ALL_CODE_BASE.txt', 'CODE_LOGIC.txt', 'DOCS_AND_CONFIG.txt', '.coverage'}

def generate_sources():
    # Nguồn 1: Chỉ chứa logic lập trình
    code_extensions = ('.py',)
    # Nguồn 2: Chứa tài liệu, hướng dẫn và cấu hình
    doc_extensions = ('.md', '.json', '.txt')

    with open("CODE_LOGIC.txt", "w", encoding="utf-8") as f_code, \
         open("DOCS_AND_CONFIG.txt", "w", encoding="utf-8") as f_docs:
        
        for root, dirs, files in os.walk(PROJECT_DIR):
            # Loại bỏ các thư mục không cần thiết
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                if file in EXCLUDE_FILES:
                    continue
                
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                # Header phân cách để NotebookLM dễ nhận diện file
                header = f"\n\n{'='*30}\nFILE: {file_path}\n{'='*30}\n\n"
                
                try:
                    if ext in code_extensions:
                        with open(file_path, "r", encoding="utf-8") as src:
                            f_code.write(header + src.read())
                        print(f"[CODE] Đã thêm: {file_path}")
                        
                    elif ext in doc_extensions:
                        with open(file_path, "r", encoding="utf-8") as src:
                            f_docs.write(header + src.read())
                        print(f"[DOCS] Đã thêm: {file_path}")
                        
                except Exception as e:
                    print(f"Lỗi khi đọc {file_path}: {e}")

if __name__ == "__main__":
    print("Bắt đầu gom file theo phong cách Antigravity...")
    generate_sources()
    print("\nHoàn thành!")
    print("- Nguồn 1: CODE_LOGIC.txt (Tải lên NotebookLM để hiểu logic)")
    print("- Nguồn 2: DOCS_AND_CONFIG.txt (Tải lên NotebookLM để hiểu ý đồ & tham số)")