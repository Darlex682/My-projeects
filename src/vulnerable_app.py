"""Intentionally vulnerable SQL helpers for demonstration."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Tuple

from db_setup import DB_PATH

Row = Tuple[int, str, str, str]


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


def lookup_user_records(conn: sqlite3.Connection, username: str) -> List[Row]:
    """Vulnerable lookup: uses string interpolation and allows SQL injection."""
    query = f"SELECT id, username, password, role FROM users WHERE username = '{username}'"
    return conn.execute(query).fetchall()


def lookup_account_balance(conn: sqlite3.Connection, username: str) -> List[Tuple[str, float]]:
    query = (
        "SELECT users.username, accounts.balance "
        "FROM users JOIN accounts ON users.id = accounts.user_id "
        f"WHERE users.username = '{username}'"
    )
    return conn.execute(query).fetchall()


def raw_executescript(conn: sqlite3.Connection, payload: str) -> None:
    """Directly feeds user input into executescript to show statement stacking risk."""
    conn.executescript(payload)
