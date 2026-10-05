from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.api.auth import require_control_token
from app.audit import AuditLog
from app.trading.orchestrator import BotSpec, FleetOrchestrator

app = FastAPI(title="Trade Bot Control API", version="0.1.0")

# Development control plane. Broker submission remains disconnected.
fleet = FleetOrchestrator(account_cash=Decimal("50000"))
audit = AuditLog()


class ProvisionRequest(BaseModel):
    bot_id: str = Field(min_length=1, max_length=64)
    capital: Decimal = Field(gt=0)


class EmergencyStopRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=256)


class ReauthorizeRequest(BaseModel):
    confirmation: str = Field(min_length=1, max_length=64)
    operator_note: str = Field(min_length=1, max_length=256)


@app.get("/health")
def health():
    return {"status": "ok", "broker_execution": False}


@app.get("/fleet/status", dependencies=[Depends(require_control_token)])
def fleet_status():
    return fleet.status()


@app.post("/bots", dependencies=[Depends(require_control_token)])
def provision_bot(request: ProvisionRequest):
    try:
        bot = fleet.provision(BotSpec(request.bot_id, request.capital))
        audit.record("BOT_PROVISION", "SUCCESS", bot.bot_id, str(request.capital))
        return {"bot_id": bot.bot_id, "state": bot.state.value}
    except Exception as exc:
        audit.record("BOT_PROVISION", "REJECTED", request.bot_id, str(exc))
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/bots/{bot_id}/start", dependencies=[Depends(require_control_token)])
def start_bot(bot_id: str):
    try:
        state = fleet.start(bot_id)
        audit.record("BOT_START", "SUCCESS", bot_id)
        return {"bot_id": bot_id, "state": state.value}
    except Exception as exc:
        audit.record("BOT_START", "REJECTED", bot_id, str(exc))
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/bots/{bot_id}/pause", dependencies=[Depends(require_control_token)])
def pause_bot(bot_id: str):
    try:
        state = fleet.pause(bot_id)
        audit.record("BOT_PAUSE", "SUCCESS", bot_id)
        return {"bot_id": bot_id, "state": state.value}
    except Exception as exc:
        audit.record("BOT_PAUSE", "REJECTED", bot_id, str(exc))
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/bots/{bot_id}/stop", dependencies=[Depends(require_control_token)])
def stop_bot(bot_id: str):
    try:
        state = fleet.stop(bot_id)
        audit.record("BOT_STOP", "SUCCESS", bot_id)
        return {"bot_id": bot_id, "state": state.value}
    except Exception as exc:
        audit.record("BOT_STOP", "REJECTED", bot_id, str(exc))
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/fleet/emergency-stop", dependencies=[Depends(require_control_token)])
def emergency_stop(request: EmergencyStopRequest):
    try:
        result = fleet.emergency_stop(request.reason)
        audit.record("EMERGENCY_STOP", "SUCCESS", "fleet", request.reason)
        return result
    except Exception as exc:
        audit.record("EMERGENCY_STOP", "REJECTED", "fleet", str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/fleet/reauthorize", dependencies=[Depends(require_control_token)])
def reauthorize(request: ReauthorizeRequest):
    try:
        fleet.kill_switch.reset(request.confirmation)
        audit.record(
            "FLEET_REAUTHORIZE", "SUCCESS", "fleet", request.operator_note
        )
        return {
            "kill_switch": False,
            "bots_started": 0,
            "message": "Fleet re-authorized. Bots remain stopped.",
        }
    except Exception as exc:
        audit.record(
            "FLEET_REAUTHORIZE", "REJECTED", "fleet", request.operator_note
        )
        raise HTTPException(status_code=409, detail=str(exc)) from exc
