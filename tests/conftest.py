import pytest
from backend.app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "unit-test-key-not-for-production",
            "DATABASE": str(tmp_path / "test.db"),
            "RATE_LIMIT_ENABLED": False,
        }
    )


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def api(client):
    headers = {"X-ShellArena": "1"}
    result = client.post("/api/session", json={}, headers=headers)
    headers["X-CSRF-Token"] = result.json["csrf"]

    def call(path, data=None, method=None):
        return client.open(
            "/api" + path, method=method or ("GET" if data is None else "POST"), json=data, headers=headers
        )

    call.headers = headers
    call.client = client
    return call
