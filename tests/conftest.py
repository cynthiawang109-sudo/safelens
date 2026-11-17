import os
import socket
import uuid
from pathlib import Path

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from safelens.config import Settings
from safelens.migrate import migrate


def pytest_collection_modifyitems(items):
    for item in items:
        if "database" in item.fixturenames:
            item.add_marker(pytest.mark.postgres)


@pytest.fixture(autouse=True)
def hermetic_network(monkeypatch):
    """PR tests can reach only their synthetic local Postgres service."""
    if os.getenv("SAFELENS_HERMETIC") != "1":
        return
    original = socket.socket.connect

    def connect(sock, address):
        if not isinstance(address, tuple) or address[0] not in ("127.0.0.1", "::1", "localhost"):
            raise RuntimeError("External network disabled in hermetic tests")
        return original(sock, address)

    monkeypatch.setattr(socket.socket, "connect", connect)


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
