"""Общая подготовка тестов: отдельная пустая база и клиент API."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

# База для тестов создаётся во временной папке, рабочая rbac.db не затрагивается
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def login(client):
    """Возвращает функцию: логин и пароль -> заголовок Authorization."""
    def _login(username, password):
        response = client.post("/api/v1/login", json={"username": username, "password": password})
        assert response.status_code == 200
        return {"Authorization": "Bearer " + response.json()["access_token"]}
    return _login
