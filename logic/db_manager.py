"""
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
