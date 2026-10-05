from dataclasses import asdict

from .risk import RiskRejected


class OperatorAPI:
    """Framework-neutral Paper v1 API adapter."""

    def __init__(self, service):
        self.service = service

    def handle(self, method, path, body=None):
        method = str(method).upper()
        path = str(path)
        body = body or {}

        if method == "GET" and path == "/status":
            return 200, self.service.status()
        if method == "GET" and path == "/bots":
            return 200, self.service.bots()
        if method == "GET" and path == "/readiness":
            return 200, self.service.release_readiness()
        if method == "POST" and path == "/analyze":
            return 200, self.service.analyze_asset(body.get("symbol"), body.get("asset_class"), body.get("price"), body.get("max_order_notional"))
        if method == "POST" and path == "/pause":
            count = self.service.bot_manager.pause_all(str(body.get("reason") or "operator pause"))
            return 200, {"paused": True, "enabled_bots": count}
        if method == "POST" and path.startswith("/bots/"):
            parts = [part for part in path.split("/") if part]
            if len(parts) == 3 and parts[2] in {"enable", "disable"}:
                enabled = parts[2] == "enable"
                return 200, self.service.set_bot_enabled(parts[1], enabled)
        raise RiskRejected("Unsupported operator API route.")
