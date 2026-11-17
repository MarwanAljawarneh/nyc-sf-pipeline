"""Database transaction tests using fake connections (no Supabase access)."""

import pytest
import psycopg2

from scripts.load_weather import load_weather
from scripts.load_cpi import load_cpi
from scripts.load_housing import load_housing


class FakeCursor:
    def __init__(self, fail_on=None):
        self.commands = []
        self.rowcount = 1
        self.fail_on = fail_on

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, values):
        self.commands.append((sql, values))
        if self.fail_on is not None and len(self.commands) == self.fail_on:
            raise psycopg2.DatabaseError("simulated insert failure")


class FakeConnection:
    def __init__(self, fail_on=None):
        self.cursor_instance = FakeCursor(fail_on)
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self.cursor_instance

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is None:
            self.committed = True
        else:
            self.rolled_back = True
        return False

    def close(self):
        self.closed = True


@pytest.mark.parametrize(
    ("loader", "rows"),
    [
        (load_weather, [
            {"city": "nyc", "date": "2026-11-15", "temp_max_c": 20, "temp_min_c": 10,
             "temp_max_f": 68, "temp_min_f": 50, "precipitation_mm": 0},
            {"city": "sf", "date": "2026-11-15", "temp_max_c": 21, "temp_min_c": 11,
             "temp_max_f": 69.8, "temp_min_f": 51.8, "precipitation_mm": 0},
        ]),
        (load_cpi, [
            {"city": "nyc", "date": "2026-10-01", "cpi": 325.1, "period_name": "October"},
            {"city": "sf", "date": "2026-10-01", "cpi": 345.2, "period_name": "October"},
        ]),
        (load_housing, [
            {"city": "nyc", "date": "2026-10-31", "median_rent": 3100},
            {"city": "sf", "date": "2026-10-31", "median_rent": 3650},
        ]),
    ],
)
def test_loaders_commit_complete_batch(monkeypatch, loader, rows):
    conn = FakeConnection()
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://test-only")
    monkeypatch.setattr(psycopg2, "connect", lambda url: conn)

    loader(rows)

    assert len(conn.cursor_instance.commands) == 2
    assert conn.committed
    assert not conn.rolled_back
    assert conn.closed


@pytest.mark.parametrize(
    ("loader", "row"),
    [
        (load_weather, {"city": "nyc", "date": "2026-11-15", "temp_max_c": 20,
                        "temp_min_c": 10, "temp_max_f": 68, "temp_min_f": 50,
                        "precipitation_mm": 0}),
        (load_cpi, {"city": "nyc", "date": "2026-10-01",
                    "cpi": 325.1, "period_name": "October"}),
        (load_housing, {"city": "nyc", "date": "2026-10-31", "median_rent": 3100}),
    ],
)
def test_loaders_rollback_and_raise_on_failure(monkeypatch, loader, row):
    conn = FakeConnection(fail_on=1)
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://test-only")
    monkeypatch.setattr(psycopg2, "connect", lambda url: conn)

    with pytest.raises(psycopg2.DatabaseError, match="simulated insert failure"):
        loader([row])

    assert not conn.committed
    assert conn.rolled_back
    assert conn.closed
