#!/usr/bin/env python3
"""Small, dependency-light migration runner for the coach database.

The schema here is deliberately simple, so this replaces Alembic rather than
pulling it in: apply every *.sql file under migrations/ whose filename stem
isn't already in schema_migrations, in filename order, each in its own
transaction. A migration is expected to record its own version (see
0001_init.sql) -- this runner does not insert schema_migrations rows itself,
so a migration that forgets to record its version will simply re-run next
time, which is the safer failure mode for a hand-rolled tool like this one.

Usage:
    python migrate.py                  # apply pending migrations
    python migrate.py --check          # exit 1 if anything is pending, no changes made
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL is not set")
    return url


def applied_versions(conn: psycopg.Connection) -> set[str]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT to_regclass('public.schema_migrations') IS NOT NULL"
        )
        (exists,) = cur.fetchone()
        if not exists:
            return set()
        cur.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}


def pending_migrations(applied: set[str]) -> list[Path]:
    all_migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
    return [m for m in all_migrations if m.stem not in applied]


def main() -> int:
    check_only = "--check" in sys.argv

    with psycopg.connect(database_url(), autocommit=False) as conn:
        applied = applied_versions(conn)
        pending = pending_migrations(applied)

        if not pending:
            print("Up to date -- no pending migrations.")
            return 0

        if check_only:
            print(f"{len(pending)} pending migration(s): {', '.join(p.stem for p in pending)}")
            return 1

        for migration in pending:
            print(f"Applying {migration.name} ...")
            sql = migration.read_text()
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            print(f"  ok ({migration.stem})")

    print(f"Applied {len(pending)} migration(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
