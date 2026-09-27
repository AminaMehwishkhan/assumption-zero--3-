from __future__ import annotations

import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.environ.get("RAPIDRELIEF_DB_PATH", str(BASE_DIR / "rapidrelief.db"))
MIGRATION_PATH = BASE_DIR.parent / "database" / "migration.sql"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        with open(MIGRATION_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
    finally:
        conn.close()


def reset_db() -> None:
    """Used by tests to get a clean slate."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
