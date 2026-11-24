"""
SkillMatch – Database Connection Module
Provides SQLite connection with timeout and WAL mode for concurrent access.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "skillmatch.db")


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with timeout and row_factory."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except sqlite3.OperationalError:
        pass
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def execute_query(sql: str, params: tuple = (), fetch: str = "none"):
    """
    Execute a SQL statement and optionally fetch results.
    fetch: 'one', 'all', or 'none'
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        if fetch == "one":
            return cur.fetchone()
        elif fetch == "all":
            return cur.fetchall()
        return cur.lastrowid
    finally:
        conn.close()


def execute_many(sql: str, data: list):
    """Execute a SQL statement with multiple parameter sets."""
    if not data:
        return
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.executemany(sql, data)
        conn.commit()
    finally:
        conn.close()
