import unittest
import tempfile
import sqlite3
import os
import gc
import time
from unittest import mock

# Ensure project root is before tests/ in sys.path so `import logic` resolves to the real package.
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
import sys
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

# Try to import the functions under test. If not present, tests will be skipped.
try:
    from logic.db_manager import upsert_managed_bridge, delete_managed_bridges, _upsert_managed_bridge_impl
    HAS_DB_MANAGER = True
except Exception:
    HAS_DB_MANAGER = False


def call_upsert_flexible(db_path, bridge_arg=None, **kwargs):
    """
    Try calling upsert_managed_bridge with a few common signatures:
      - upsert_managed_bridge(db_path, bridge_dict)
      - upsert_managed_bridge(db_path, **kwargs)
      - upsert_managed_bridge(conn, bridge_dict)
      - upsert_managed_bridge(conn, **kwargs)
    Returns whatever the underlying function returned.
    """
    if not HAS_DB_MANAGER:
        raise RuntimeError("db_manager not available")

    # try db_path + dict
    if bridge_arg is not None:
        try:
            return upsert_managed_bridge(db_path, bridge_arg)
        except TypeError:
            pass
    # try db_path + kwargs
    if kwargs:
        try:
            return upsert_managed_bridge(db_path, **kwargs)
        except TypeError:
            pass
    # try conn variants
    try:
        conn = sqlite3.connect(db_path)
        try:
            if bridge_arg is not None:
                return upsert_managed_bridge(conn, bridge_arg)
            if kwargs:
                return upsert_managed_bridge(conn, **kwargs)
        finally:
            conn.close()
    except TypeError:
        raise


def call_delete_flexible(db_path, ids_list):
    """
    Try calling delete_managed_bridges with either db_path or conn.
    Return the tuple as defined by implementation (success, message, count).
    """
    if not HAS_DB_MANAGER:
        raise RuntimeError("db_manager not available")

    try:
        return delete_managed_bridges(db_path, ids_list)
    except TypeError:
        conn = sqlite3.connect(db_path)
        try:
            return delete_managed_bridges(conn, ids_list)
        finally:
            conn.close()


@unittest.skipUnless(HAS_DB_MANAGER, "db_manager module not available")
class TestBatchOperations(unittest.TestCase):
    def setUp(self):
        # create a temp sqlite file
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        # create schema
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ManagedBridges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                type TEXT,
                current_streak INTEGER
            );
            """
        )
        conn.commit()
        conn.close()
        # optional handle reference used by some tests
        self.conn = None

    def tearDown(self):
        """
        Ensure any sqlite3 connections are closed before removing the temporary DB file.
        On Windows a file cannot be unlinked while a handle is open, so tests must
        explicitly close connections. We try to close:
          - self.conn when present
          - any sqlite3.Connection objects discovered via the GC
        Finally attempt to unlink; if PermissionError occurs, print a warning but do not fail teardown.
        """
        try:
            # Close known connection stored on the test instance
            if hasattr(self, "conn") and self.conn:
                try:
                    self.conn.close()
                except Exception:
                    pass

            # Close any other sqlite3.Connection objects found by GC
            # This helps when module-under-test created connections that were not closed.
            for obj in gc.get_objects():
                try:
                    if isinstance(obj, sqlite3.Connection):
                        try:
                            obj.close()
                        except Exception:
                            pass
                except Exception:
                    # Some objects may raise during GC inspection; ignore them.
                    continue

            # Allow a short time for OS to release file handles on Windows
            time.sleep(0.05)
        finally:
            try:
                os.unlink(self.db_path)
            except PermissionError as e:
                # Warn instead of failing teardown to avoid masking test results with cleanup errors.
                print(f"[WARN] Could not remove temp DB {self.db_path}: {e}")

    def _count_rows(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(1) FROM ManagedBridges;")
        r = cur.fetchone()[0]
        conn.close()
        return r

    def test_upsert_with_dict(self):
        # Upsert using a dict argument
        bridge = {"name": "B1", "type": "DE_SET", "current_streak": 5}
        call_upsert_flexible(self.db_path, bridge_arg=bridge)
        self.assertEqual(self._count_rows(), 1)

    def test_upsert_with_kwargs(self):
        # Upsert using kwargs
        call_upsert_flexible(self.db_path, name="B2", type="DE_SET", current_streak=3)
        self.assertEqual(self._count_rows(), 1)

    def test_upsert_key_normalization(self):
        # Using alternative keys like 'ten' and 'loai' should normalize to name/type
        bridge_dict = {"ten": "B3", "loai": "DE_SET", "current_streak": 2}
        call_upsert_flexible(self.db_path, bridge_arg=bridge_dict)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT name, type FROM ManagedBridges LIMIT 1;")
        row = cur.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "B3")
        self.assertTrue(row[1].upper().startswith("DE_"))

    def test_delete_multiple_bridges(self):
        # Insert 3 rows then delete two of them
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.executemany("INSERT INTO ManagedBridges (name, type, current_streak) VALUES (?, ?, ?);",
                        [("x1", "DE_SET", 1), ("x2", "DE_DYN", 2), ("x3", "DE_SET", 3)])
        conn.commit()
        conn.close()
        # get ids
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT id FROM ManagedBridges ORDER BY id;")
        ids = [r[0] for r in cur.fetchall()]
        conn.close()
        self.assertEqual(len(ids), 3)
        success, msg, deleted = call_delete_flexible(self.db_path, ids_list=ids[:2])
        self.assertTrue(success)
        self.assertEqual(deleted, 2)
        # remaining rows count
        self.assertEqual(self._count_rows(), 1)

    def test_delete_empty_list(self):
        success, msg, deleted = call_delete_flexible(self.db_path, ids_list=[])
        # Implementation may return True/False; ensure no exception and count 0
        self.assertTrue(isinstance(deleted, int))
        self.assertEqual(deleted, 0)

    def test_batch_add_with_errors(self):
        # Simulate _upsert_managed_bridge_impl failing for a specific name by mocking it
        inserts = [
            {"name": "ok1", "type": "DE_SET", "current_streak": 1},
            {"name": "fail-me", "type": "DE_SET", "current_streak": 1},
            {"name": "ok2", "type": "DE_SET", "current_streak": 1},
        ]

        # Patch the internal impl to raise when name == "fail-me"
        if hasattr(__import__("logic.db_manager", fromlist=["_upsert_managed_bridge_impl"]), "_upsert_managed_bridge_impl"):
            target = "logic.db_manager._upsert_managed_bridge_impl"
        else:
            target = None

        if target:
            def side_effect(conn_or_dbpath, bridge):
                # normalize bridge dict if kwargs style
                b = bridge if isinstance(bridge, dict) else {}
                name = b.get("name") or b.get("ten")
                if name == "fail-me":
                    raise RuntimeError("simulated failure")
                # fallback: insert directly using simple SQL for test purpose
                # Determine db_path
                db_path = conn_or_dbpath if isinstance(conn_or_dbpath, str) else None
                if db_path is None:
                    # assume connection provided
                    conn = conn_or_dbpath
                    cur = conn.cursor()
                    cur.execute("INSERT INTO ManagedBridges (name, type, current_streak) VALUES (?, ?, ?);",
                                (b.get("name"), b.get("type"), b.get("current_streak")))
                    conn.commit()
                else:
                    conn = sqlite3.connect(db_path)
                    cur = conn.cursor()
                    cur.execute("INSERT INTO ManagedBridges (name, type, current_streak) VALUES (?, ?, ?);",
                                (b.get("name"), b.get("type"), b.get("current_streak")))
                    conn.commit()
                    conn.close()

            with mock.patch("logic.db_manager._upsert_managed_bridge_impl", side_effect=side_effect):
                # call wrapper for each insert (simulate batch add)
                successes = 0
                failures = 0
                for b in inserts:
                    try:
                        call_upsert_flexible(self.db_path, bridge_arg=b)
                        successes += 1
                    except Exception:
                        failures += 1
                # Two successes, one failure
                self.assertEqual(successes, 2)
                self.assertEqual(failures, 1)
                # check DB has two rows
                self.assertEqual(self._count_rows(), 2)
        else:
            self.skipTest("Internal impl not found to patch; skipping batch add error simulation.")


if __name__ == "__main__":
    unittest.main()