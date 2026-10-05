from fastapi.testclient import TestClient

from app.api import control


def make_client(monkeypatch):
    monkeypatch.setenv("CONTROL_API_TOKEN", "test-control-token")
    control.fleet = control.FleetOrchestrator(
        account_cash=control.Decimal("50000")
    )
    return TestClient(control.app)


def auth_headers():
    return {"Authorization": "Bearer test-control-token"}


def test_health_confirms_broker_execution_disabled(monkeypatch):
    response = make_client(monkeypatch).get("/health")
    assert response.status_code == 200
    assert response.json()["broker_execution"] is False


def test_control_plane_lifecycle(monkeypatch):
    client = make_client(monkeypatch)
    response = client.post(
        "/bots",
        json={"bot_id": "bot-1", "capital": "500"},
        headers=auth_headers(),
    )
    assert response.status_code == 200
    assert response.json()["state"] == "READY"

    response = client.post("/bots/bot-1/start", headers=auth_headers())
    assert response.json()["state"] == "RUNNING"

    response = client.post("/bots/bot-1/pause", headers=auth_headers())
    assert response.json()["state"] == "PAUSED"


def test_emergency_stop_blocks_fleet(monkeypatch):
    client = make_client(monkeypatch)
    client.post(
        "/bots",
        json={"bot_id": "bot-1", "capital": "500"},
        headers=auth_headers(),
    )
    client.post("/bots/bot-1/start", headers=auth_headers())
    response = client.post(
        "/fleet/emergency-stop",
        json={"reason": "operator test"},
        headers=auth_headers(),
    )
    assert response.status_code == 200
    assert response.json()["kill_switch"] is True

    status = client.get("/fleet/status", headers=auth_headers()).json()
    assert status["running"] == 0
    assert status["kill_switch"] is True
