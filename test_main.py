import os
from unittest.mock import MagicMock

import psycopg
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "hello docker"}


def test_database_not_configured(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    response = client.get("/db")
    assert response.status_code == 503
    assert response.json()["detail"] == "DATABASE_URL is not configured"


def test_database_unavailable(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")

    def fail(*args, **kwargs):
        raise psycopg.OperationalError("connection failed")

    monkeypatch.setattr("main.psycopg.connect", fail)
    response = client.get("/db")
    assert response.status_code == 503
    assert response.json()["detail"] == "Database is unavailable"


def test_database_response(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    connection = MagicMock()
    cursor = connection.__enter__.return_value.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (1,)
    monkeypatch.setattr("main.psycopg.connect", lambda *args, **kwargs: connection)

    response = client.get("/db")
    assert response.status_code == 200
    assert response.json() == {"database": "ok", "value": 1}
    cursor.execute.assert_called_once_with("SELECT 1")


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="PostgreSQL integration requires DATABASE_URL",
)
def test_real_database():
    response = client.get("/db")
    assert response.status_code == 200
    assert response.json() == {"database": "ok", "value": 1}