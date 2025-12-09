#!/usr/bin/env python3
# Run from project root. Prints import diagnostics for logic.db_manager.
import sys, traceback, importlib, importlib.util, py_compile, os, pprint

def try_compile(path):
    try:
        py_compile.compile(path, doraise=True)
        print(f"py_compile OK: {path}")
    except Exception:
        print(f"py_compile FAILED: {path}")
        traceback.print_exc()

print("CWD:", os.getcwd())
print("\n--- sys.path (first 10 entries) ---")
pprint.pprint(sys.path[:10])

print("\n--- find_spec for 'logic' and 'logic.db_manager' ---")
try:
    print("spec logic:", importlib.util.find_spec("logic"))
    print("spec logic.db_manager:", importlib.util.find_spec("logic.db_manager"))
except Exception:
    traceback.print_exc()

print("\n--- py_compile checks (if files exist) ---")
for p in ("logic/__init__.py", "logic/db_manager.py"):
    if os.path.exists(p):
        try_compile(p)
    else:
        print("Missing file:", p)

print("\n--- try importing logic and logic.db_manager ---")
try:
    mod_logic = importlib.import_module("logic")
    print("Imported package 'logic' from:", getattr(mod_logic, "__file__", None))
except Exception:
    print("Importing package 'logic' FAILED")
    traceback.print_exc()

try:
    mod_db = importlib.import_module("logic.db_manager")
    print("Imported module 'logic.db_manager' from:", getattr(mod_db, "__file__", None))
    for name in ("upsert_managed_bridge", "delete_managed_bridges", "_upsert_managed_bridge_impl"):
        print(f"has {name}? ->", hasattr(mod_db, name))
    # show a short list of top-level names for inspection
    print("Some attributes of logic.db_manager:", [n for n in dir(mod_db) if not n.startswith("_")][:30])
except Exception:
    print("Importing module 'logic.db_manager' FAILED")
    traceback.print_exc()