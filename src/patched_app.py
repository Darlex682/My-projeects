"""Patched, parameterized versions of the vulnerable queries."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Tuple

from db_setup import DB_PATH

Row = Tuple[int, str, str, str]


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


def lookup_user_records(conn: sqlite3.Connection, username: str) -> List[Row]:
    query = "SELECT id, username, password, role FROM users WHERE username = ?"
    return conn.execute(query, (username,)).fetchall()


def lookup_account_balance(conn: sqlite3.Connection, username: str) -> List[Tuple[str, float]]:
    query = (
        "SELECT users.username, accounts.balance "
        "FROM users JOIN accounts ON users.id = accounts.user_id "
        "WHERE users.username = ?"
    )
    return conn.execute(query, (username,)).fetchall()


def safe_executescript(conn: sqlite3.Connection, payload: str) -> None:
    """Reject stacked statements by restricting to a single safe query."""
    if ";" in payload.strip().rstrip(";"):
        raise ValueError("Refusing to execute stacked statements")
    conn.execute(payload)
