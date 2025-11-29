"""Entry point to build the database, exercise vulnerabilities, and toggle fixes."""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import db_setup
import patched_app
import vulnerability_tests
import vulnerable_app


def format_results(title: str, results: list[tuple[str, bool]]) -> str:
    lines = [title]
    for name, success in results:
        emoji = "✅" if success else "❌"
        lines.append(f"  {emoji} {name}")
    return "\n".join(lines)


def demonstrate_vulnerabilities(conn: sqlite3.Connection) -> list[tuple[str, bool]]:
    return vulnerability_tests.run_all(conn)


def demonstrate_patches(conn: sqlite3.Connection) -> list[tuple[str, bool]]:
    results: list[tuple[str, bool]] = []

    payloads = {
        "Boolean-based injection is neutralized": (
            patched_app.lookup_user_records,
            "alice' OR '1'='1",
            lambda rows: len(rows) == 0,
        ),
        "UNION injection does not leak credentials": (
            patched_app.lookup_user_records,
            "nonexistent' UNION SELECT id, username, password, role FROM users --",
            lambda rows: len(rows) == 0,
        ),
        "Stacked statements are rejected": (
            patched_app.safe_executescript,
            "DELETE FROM accounts WHERE 1=1; DROP TABLE audit_log;",
            lambda _: False,  # we expect an exception
        ),
    }

    for name, (func, payload, validator) in payloads.items():
        try:
            result = func(conn, payload)
            results.append((name, validator(result)))
        except Exception:
            results.append((name, True))
    return results


def get_connection(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh-db",
        action="store_true",
        help="Пересоздать базу данных перед запуском проверок",
    )
    parser.add_argument(
        "--apply-patch",
        action="store_true",
        help=(
            "Применить исправления и показать, что инъекции больше не срабатывают."
            " По умолчанию демонстрируются только уязвимые сценарии."
        ),
    )
    parser.add_argument(
        "--show-both",
        action="store_true",
        help="Вывести и уязвимый, и исправленный сценарии в одном запуске",
    )
    args = parser.parse_args()

    if args.refresh_db or not db_setup.DB_PATH.exists():
        db_setup.initialize_database()

    show_patched = args.apply_patch or args.show_both
    show_vulnerable = not args.apply_patch or args.show_both

    if show_vulnerable:
        with vulnerable_app.connect() as conn:
            vulnerable_results = demonstrate_vulnerabilities(conn)
        print(format_results("Vulnerable query results", vulnerable_results))
        if show_patched:
            print()

    if show_patched:
        with patched_app.connect() as conn:
            patched_results = demonstrate_patches(conn)
        print(format_results("Patched query results", patched_results))


if __name__ == "__main__":
    main()
