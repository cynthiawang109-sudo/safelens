"""Apply ordered SQL migrations atomically with checksum verification."""

import argparse
import hashlib
from pathlib import Path

import psycopg

from safelens.config import Settings


def migrate(conn, directory: Path) -> list[str]:
    applied = []
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(742801)")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(name text PRIMARY KEY, sha256 text NOT NULL)"
        )
        for path in sorted(directory.glob("*.sql")):
            sql = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
            existing = conn.execute(
                "SELECT sha256 FROM schema_migrations WHERE name = %s", (path.name,)
            ).fetchone()
            if existing:
                if existing[0] != checksum:
                    raise ValueError(f"Applied migration changed: {path.name}")
                continue
            conn.execute(sql)
            conn.execute("INSERT INTO schema_migrations VALUES (%s, %s)", (path.name, checksum))
            applied.append(path.name)
    return applied


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("db/migrations"))
    args = parser.parse_args()
    if not args.directory.is_dir() or not list(args.directory.glob("*.sql")):
        parser.error("Migration directory must contain SQL files")
    with psycopg.connect(Settings.from_env().database_url, autocommit=True, connect_timeout=10) as conn:
        print({"applied": migrate(conn, args.directory)})


if __name__ == "__main__":
    main()
