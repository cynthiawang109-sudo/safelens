import uuid
from pathlib import Path

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from safelens.config import Settings
from safelens.migrate import migrate


@pytest.fixture
def database():
    """A real PostgreSQL schema per test; never change the validation slice."""
    settings = Settings.from_env()
    schema = "test_" + uuid.uuid4().hex
    with psycopg.connect(settings.database_url, autocommit=True, connect_timeout=10) as admin:
        admin.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        dsn = make_conninfo(settings.database_url, options=f"-c search_path={schema},public")
        try:
            with psycopg.connect(dsn, autocommit=True, connect_timeout=10) as conn:
                migrate(conn, Path("db/migrations"))
                yield conn, dsn, settings
        finally:
            admin.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
