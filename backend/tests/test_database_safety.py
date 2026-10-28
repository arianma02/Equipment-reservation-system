from contextlib import contextmanager

import pytest

import conftest


def test_database_guard_refuses_unexpected_connected_database(monkeypatch):
    statements = []

    class Cursor:
        def execute(self, sql):
            statements.append(sql)

        def fetchone(self):
            return {"name": "equipment_reservation"}

    class Connection:
        @contextmanager
        def cursor(self):
            yield Cursor()

    @contextmanager
    def wrong_connection():
        yield Connection()

    monkeypatch.setattr(conftest, "get_connection", wrong_connection)
    fixture = conftest.clean_database.__wrapped__()
    with pytest.raises(pytest.UsageError, match="Refusing destructive tests"):
        next(fixture)
    assert statements == ["SELECT current_database() AS name"]
