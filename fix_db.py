import sqlite3
conn = sqlite3.connect('data/xo_so_prizes_all_logic.db')
cursor = conn.cursor()

# Xóa cầu Lô cũ (tên bắt đầu bằng getCau...)
cursor.execute("DELETE FROM ManagedBridges WHERE name LIKE 'getCau%'")
# Xóa cầu Lô fix cũ nếu có
cursor.execute("DELETE FROM ManagedBridges WHERE type = 'CAU_LO_FIXED'")

conn.commit()
print("Đã dọn dẹp Cầu Lô cũ. Hãy chạy lại App -> 'Quét Cầu Lô'.")
conn.close()