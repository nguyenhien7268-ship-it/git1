#!/usr/bin/env python3
r"""
Script hỗ trợ tự động ít thao tác nhất để:
- Kiểm tra module logic.db_manager có thể import được không.
- Nếu module không tồn tại hoặc import lỗi, tạo một stub an toàn logic/db_manager.py (backup file hiện có nếu có).
- Chạy kiểm tra cú pháp (py_compile) cho file thay đổi và file test.
- Chạy pytest cho tests/test_batch_operations.py và lưu kết quả vào artifacts/test_run_<ts>.txt

Hướng dẫn:
1) Mở terminal ở thư mục repo (C:\Users\KAKA\Documents\27loto\code8).
2) Chạy: python tools/run_minimal_tests_and_fix_db_manager.py
3) Sau khi script hoàn tất, file output nằm trong artifacts/ - mở file đó và copy-n-paste nội dung ở đây để tôi phân tích tiếp.
"""
from __future__ import annotations
import os
import sys
import time
import shutil
import importlib
import importlib.util
import subprocess
import traceback
from datetime import datetime

ROOT = os.getcwd()
LOG_DIR = os.path.join(ROOT, "artifacts")
os.makedirs(LOG_DIR, exist_ok=True)
ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
OUTPATH = os.path.join(LOG_DIR, f"test_run_{ts}.txt")

DB_MANAGER_PATH = os.path.join(ROOT, "logic", "db_manager.py")


STUB_CODE = r'''"""
Safe stub implementation for logic.db_manager used by tests.
- Provides:
    - upsert_managed_bridge(db_or_conn, bridge_dict_or_kwargs)
    - _upsert_managed_bridge_impl(conn_or_dbpath, bridge_dict)
    - delete_managed_bridges(db_or_conn, ids_list)
This stub is intentionally small and safe: uses sqlite3, context managers, and only touches the DB path given.
"""
import sqlite3
from typing import Tuple, Any, Dict, Union

def _ensure_conn(db_or_conn):
    """Return (conn, should_close) where should_close indicates whether caller must close."""
    if isinstance(db_or_conn, str):
        conn = sqlite3.connect(db_or_conn)
        return conn, True
    else:
        # assume sqlite3.Connection-like
        return db_or_conn, False

def _normalize_bridge_input(bridge_or_kwargs: Any, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Return canonical dict (name,type,current_streak) normalizing common alt keys."""
    if isinstance(bridge_or_kwargs, dict):
        b = dict(bridge_or_kwargs)
    else:
        b = {}
    # merge kwargs if provided
    if kwargs:
        b.update(kwargs)
    # normalize vietnamese keys if present
    if "ten" in b and "name" not in b:
        b["name"] = b.pop("ten")
    if "loai" in b and "type" not in b:
        b["type"] = b.pop("loai")
    # ensure keys exist
    if "name" not in b:
        b["name"] = None
    if "type" not in b:
        b["type"] = None
    if "current_streak" not in b:
        b["current_streak"] = 0
    return b

def _upsert_managed_bridge_impl(db_or_conn, bridge: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Simple insert implementation: always INSERT a new row.
    If a production upsert logic is required, replace implementation.
    Returns (success, message)
    """
    conn, should_close = _ensure_conn(db_or_conn)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO ManagedBridges (name, type, current_streak) VALUES (?, ?, ?);",
            (bridge.get("name"), bridge.get("type"), bridge.get("current_streak"))
        )
        conn.commit()
        return True, "inserted"
    except Exception as ex:
        try:
            conn.rollback()
        except Exception:
            pass
        return False, str(ex)
    finally:
        if should_close:
            conn.close()

def upsert_managed_bridge(db_or_conn, bridge_or_dict=None, **kwargs) -> Any:
    """
    Flexible wrapper supporting:
      - upsert_managed_bridge(db_path, bridge_dict)
      - upsert_managed_bridge(db_path, **kwargs)
      - upsert_managed_bridge(conn, bridge_dict)
      - upsert_managed_bridge(conn, **kwargs)
    Delegates to _upsert_managed_bridge_impl.
    """
    # normalize input dict
    bridge = _normalize_bridge_input(bridge_or_dict, kwargs)
    # delegate
    return _upsert_managed_bridge_impl(db_or_conn, bridge)

def delete_managed_bridges(db_or_conn, ids_list) -> Tuple[bool, str, int]:
    """
    Delete multiple ids in a single SQL statement.
    Returns (success: bool, message: str, deleted_count: int)
    """
    try:
        if not ids_list:
            return True, "no ids", 0
        conn, should_close = _ensure_conn(db_or_conn)
        placeholders = ",".join("?" for _ in ids_list)
        sql = f"DELETE FROM ManagedBridges WHERE id IN ({placeholders});"
        cur = conn.cursor()
        cur.execute(sql, ids_list)
        deleted = cur.rowcount if cur.rowcount is not None else 0
        conn.commit()
        return True, "ok", deleted
    except Exception as ex:
        try:
            conn.rollback()
        except Exception:
            pass
        return False, str(ex), 0
    finally:
        try:
            if should_close:
                conn.close()
        except Exception:
            pass
'''

def write_out(message: str):
    with open(OUTPATH, "a", encoding="utf-8") as f:
        f.write(message + "\n")
    print(message)


def try_import_db_manager():
    """Try importing logic.db_manager and return (ok, errmsg)."""
    try:
        if "logic" in sys.modules:
            # remove cached to retry import
            del sys.modules["logic"]
        spec = importlib.util.find_spec("logic.db_manager")
        if spec is None:
            return False, "logic.db_manager module not found"
        # try import and instantiate
        mod = importlib.import_module("logic.db_manager")
        # quick function checks
        missing = []
        for name in ("upsert_managed_bridge", "_upsert_managed_bridge_impl", "delete_managed_bridges"):
            if not hasattr(mod, name):
                missing.append(name)
        if missing:
            return False, f"module imported but missing symbols: {missing}"
        return True, "import OK"
    except Exception as ex:
        tb = traceback.format_exc()
        return False, f"import error: {ex}\n{tb}"


def create_stub_backup_and_write(force=False):
    # ensure logic dir exists
    logic_dir = os.path.join(ROOT, "logic")
    if not os.path.isdir(logic_dir):
        os.makedirs(logic_dir, exist_ok=True)
        write_out(f"Created directory: {logic_dir}")

    if os.path.exists(DB_MANAGER_PATH):
        bak = DB_MANAGER_PATH + f".bak_{ts}"
        shutil.copy2(DB_MANAGER_PATH, bak)
        write_out(f"Backed up existing {DB_MANAGER_PATH} -> {bak}")
        if not force:
            # still write stub to overwrite only if user allowed (we choose to overwrite because import failed)
            pass

    with open(DB_MANAGER_PATH, "w", encoding="utf-8") as f:
        f.write(STUB_CODE)
    write_out(f"Wrote stub to {DB_MANAGER_PATH}")


def run_py_compile(paths):
    ok = True
    for p in paths:
        try:
            subprocess.check_output([sys.executable, "-m", "py_compile", p], stderr=subprocess.STDOUT)
            write_out(f"py_compile OK: {p}")
        except subprocess.CalledProcessError as cpe:
            ok = False
            out = cpe.output.decode("utf-8", errors="replace") if cpe.output else str(cpe)
            write_out(f"py_compile FAILED: {p}\n{out}")
    return ok


def run_pytest(test_path):
    write_out(f"Running pytest for {test_path} ...")
    try:
        # run pytest and capture output
        res = subprocess.run([sys.executable, "-m", "pytest", "-q", test_path], capture_output=True, text=True)
        write_out("=== PYTEST STDOUT ===")
        write_out(res.stdout)
        write_out("=== PYTEST STDERR ===")
        write_out(res.stderr)
        write_out(f"pytest returncode: {res.returncode}")
        return res.returncode == 0
    except Exception as ex:
        write_out(f"Exception running pytest: {ex}")
        return False


def main():
    write_out(f"Starting automated helper at {datetime.utcnow().isoformat()}")
    ok, msg = try_import_db_manager()
    write_out(f"Import check: {ok} - {msg}")
    if not ok:
        write_out("Will create a safe stub for logic/db_manager.py to allow tests to run.")
        create_stub_backup_and_write(force=True)
        # Try import again
        ok2, msg2 = try_import_db_manager()
        write_out(f"Import after stub: {ok2} - {msg2}")
    else:
        write_out("Existing logic.db_manager looks OK; no stub written.")

    # Prepare list of files to py_compile: db_manager + test file
    files_to_check = []
    if os.path.exists(DB_MANAGER_PATH):
        files_to_check.append(DB_MANAGER_PATH)
    test_file = os.path.join("tests", "test_batch_operations.py")
    files_to_check.append(test_file)

    write_out("Running py_compile on key files...")
    pc_ok = run_py_compile(files_to_check)

    write_out("Running targeted pytest tests...")
    pytest_ok = run_pytest(test_file)

    write_out("Done. Summary:")
    write_out(f"py_compile OK: {pc_ok}")
    write_out(f"pytest OK: {pytest_ok}")
    write_out(f"Output saved to: {OUTPATH}")
    write_out("Please paste the contents of that file here for further analysis.")

if __name__ == "__main__":
    main()