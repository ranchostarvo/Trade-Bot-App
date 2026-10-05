from fastapi.testclient import TestClient

from app.api import control


def make_client():
    control.fleet = control.FleetOrchestrator(
        account_cash=control.Decimal("50000")
    )
    return TestClient(control.app)


def test_health_confirms_broker_execution_disabled():
    response = make_client().get("/health")
    assert response.status_code == 200
    assert response.json()["broker_execution"] is False


def test_control_plane_lifecycle():
    client = make_client()
    response = client.post(
        "/bots", json={"bot_id": "bot-1", "capital": "500"}
    )
    assert response.status_code == 200
    assert response.json()["state"] == "READY"

    response = client.post("/bots/bot-1/start")
    assert response.json()["state"] == "RUNNING"

    response = client.post("/bots/bot-1/pause")
    assert response.json()["state"] == "PAUSED"


def test_emergency_stop_blocks_fleet():
    client = make_client()
    client.post("/bots", json={"bot_id": "bot-1", "capital": "500"})
    client.post("/bots/bot-1/start")
    response = client.post(
        "/fleet/emergency-stop", json={"reason": "operator test"}
    )
    assert response.status_code == 200
    assert response.json()["kill_switch"] is True

    status = client.get("/fleet/status").json()
    assert status["running"] == 0
    assert status["kill_switch"] is True
