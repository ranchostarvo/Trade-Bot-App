from decimal import Decimal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.trading.orchestrator import BotSpec, FleetOrchestrator

app = FastAPI(title="Trade Bot Control API", version="0.1.0")

# Development control plane. Broker submission remains disconnected.
fleet = FleetOrchestrator(account_cash=Decimal("50000"))


class ProvisionRequest(BaseModel):
    bot_id: str = Field(min_length=1, max_length=64)
    capital: Decimal = Field(gt=0)


class EmergencyStopRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=256)


@app.get("/health")
def health():
    return {"status": "ok", "broker_execution": False}


@app.get("/fleet/status")
def fleet_status():
    return fleet.status()


@app.post("/bots")
def provision_bot(request: ProvisionRequest):
    try:
        bot = fleet.provision(BotSpec(request.bot_id, request.capital))
        return {"bot_id": bot.bot_id, "state": bot.state.value}
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/bots/{bot_id}/start")
def start_bot(bot_id: str):
    try:
        state = fleet.start(bot_id)
        return {"bot_id": bot_id, "state": state.value}
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/bots/{bot_id}/pause")
def pause_bot(bot_id: str):
    try:
        state = fleet.pause(bot_id)
        return {"bot_id": bot_id, "state": state.value}
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/bots/{bot_id}/stop")
def stop_bot(bot_id: str):
    try:
        state = fleet.stop(bot_id)
        return {"bot_id": bot_id, "state": state.value}
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/fleet/emergency-stop")
def emergency_stop(request: EmergencyStopRequest):
    try:
        return fleet.emergency_stop(request.reason)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
