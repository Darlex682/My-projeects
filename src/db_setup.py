"""Create and populate a demo SQLite database for security testing."""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "vulnerable.db"

SCHEMA = """
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL
);

CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    balance REAL NOT NULL
);
"""

USERS = [
    ("alice", "alicepass", "user", 1250.0),
    ("bob", "bobpass", "user", 880.4),
    ("carol", "carolpass", "auditor", 12790.8),
    ("dave", "davepass", "admin", 500000.0),
]


def initialize_database(db_path: Path = DB_PATH) -> Path:
    """Create a fresh database with predictable sample data."""
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        for username, password, role, balance in USERS:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role),
            )
            user_id = conn.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO accounts (user_id, balance) VALUES (?, ?)",
                (user_id, balance),
            )
        conn.commit()

    return db_path


if __name__ == "__main__":
    path = initialize_database()
    print(f"Database created at: {path}")
