"""SQLite connection and small helpers."""
import re
import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path


def get_db_path():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "app.db"
    return Path(__file__).resolve().parent.parent / "app.db"


DB_PATH = get_db_path()


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def db_cursor():
    conn = get_connection()
    try:
        yield conn.cursor()
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# Identifier helpers (CSV headers become SQL names)
def safe_name(text, fallback="col"):
    """'Seat No.' -> 'seat_no'"""
    return re.sub(r"\W+", "_", str(text).strip().lower()).strip("_") or fallback


def q(name):
    """Quote an identifier so any name is safe inside SQL."""
    return '"' + str(name).replace('"', '""') + '"'


def table_exists(name):
    with db_cursor() as cur:
        cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=? COLLATE NOCASE", (name,))
        return cur.fetchone() is not None