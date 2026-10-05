from fastapi.testclient import TestClient

from app.api import control


def test_health_remains_public(monkeypatch):
    monkeypatch.delenv("CONTROL_API_TOKEN", raising=False)
    response = TestClient(control.app).get("/health")
    assert response.status_code == 200


def test_control_endpoint_fails_closed_without_server_token(monkeypatch):
    monkeypatch.delenv("CONTROL_API_TOKEN", raising=False)
    response = TestClient(control.app).get("/fleet/status")
    assert response.status_code == 503


def test_missing_bearer_token_is_rejected(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", "server-secret")
    response = TestClient(control.app).get("/fleet/status")
    assert response.status_code == 401


def test_wrong_bearer_token_is_rejected(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", "server-secret")
    response = TestClient(control.app).get(
        "/fleet/status",
        headers={"Authorization": "Bearer wrong-secret"},
    )
    assert response.status_code == 403


def test_valid_bearer_token_can_read_status(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", "server-secret")
    response = TestClient(control.app).get(
        "/fleet/status",
        headers={"Authorization": "Bearer server-secret"},
    )
    assert response.status_code == 200
