#!/usr/bin/env python3
r"""
Simulate pytest's import-time sys.path ordering to reproduce why tests/test_batch_operations.py
sees "db_manager module not available" during collection.

What this does:
- Shows current sys.path
- Tries importing logic.db_manager (normal)
- Prepends the tests/ directory to sys.path (pytest-like) and tries import again
- Tries importing tests.test_batch_operations to show its HAS_DB_MANAGER value when imported
- Prints full tracebacks for any exceptions

Run from project root (C:\Users\KAKA\Documents\27loto\code8):
  python tools/simulate_pytest_import_env.py

Paste the full output here.
"""
import sys
import os
import traceback
import importlib

def try_import(name):
    try:
        mod = importlib.import_module(name)
        print(f"[OK] Imported {name} from {getattr(mod,'__file__',None)}")
        return True, mod
    except Exception:
        print(f"[FAIL] Importing {name} raised:")
        traceback.print_exc()
        return False, None

def main():
    root = os.getcwd()
    print("CWD:", root)
    print("\n--- sys.path (first 10) ---")
    for i, p in enumerate(sys.path[:10]):
        print(i, repr(p))
    print("\n--- Try importing logic.db_manager with current sys.path ---")
    try_import("logic.db_manager")
    print("\n--- Try importing tests.test_batch_operations with current sys.path ---")
    try_import("tests.test_batch_operations")

    # Now simulate pytest ordering: prepend tests dir to sys.path front
    tests_dir = os.path.join(root, "tests")
    if not os.path.isdir(tests_dir):
        print(f"\n[WARN] tests/ directory not found at {tests_dir}")
        return

    print("\n--- Prepending tests/ to sys.path and retrying imports (pytest-like) ---")
    # Make a copy and manipulate
    orig_sys_path = list(sys.path)
    try:
        if tests_dir in sys.path:
            sys.path.remove(tests_dir)
        sys.path.insert(0, tests_dir)
        print("New sys.path[0:6]:")
        for i, p in enumerate(sys.path[:6]):
            print(i, repr(p))
        print("\n--- Import logic.db_manager after prepending tests/ ---")
        try_import("logic.db_manager")
        print("\n--- Import tests.test_batch_operations after prepending tests/ ---")
        ok, mod = try_import("tests.test_batch_operations")
        if ok:
            # show HAS_DB_MANAGER attr if present
            print("HAS_DB_MANAGER =", getattr(mod, "HAS_DB_MANAGER", "<missing>"))
    finally:
        sys.path[:] = orig_sys_path

if __name__ == "__main__":
    main()