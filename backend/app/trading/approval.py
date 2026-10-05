from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from .risk import RiskRejected


@dataclass(frozen=True)
class ApprovalRequest:
    approval_id: str
    action: str
    scope: str
    summary: str
    expires_at: str


class SingleButtonApproval:
    """One-button approval with narrow scope; never bypasses runtime safety gates."""

    ALLOWED_ACTIONS = {"start_paper_batch", "enable_paper_bot", "paper_order_batch"}

    def __init__(self):
        self._pending = {}
        self._consumed = set()

    def request(self, action, scope, summary, expires_at):
        action = str(action or "").strip()
        scope = str(scope or "").strip()
        summary = str(summary or "").strip()
        if action not in self.ALLOWED_ACTIONS:
            raise RiskRejected("Approval action is not permitted.")
        if not scope or not summary or not expires_at:
            raise RiskRejected("Approval scope, summary, and expiry are required.")
        approval = ApprovalRequest(
            approval_id=str(uuid4()),
            action=action,
            scope=scope,
            summary=summary,
            expires_at=str(expires_at),
        )
        self._pending[approval.approval_id] = approval
        return approval

    def approve(self, approval_id, now=None):
        approval_id = str(approval_id or "").strip()
        if approval_id in self._consumed:
            raise RiskRejected("Approval has already been consumed.")
        approval = self._pending.get(approval_id)
        if approval is None:
            raise RiskRejected("Approval request does not exist.")
        now = now or datetime.now(timezone.utc)
        expiry = datetime.fromisoformat(approval.expires_at.replace("Z", "+00:00"))
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if now >= expiry:
            raise RiskRejected("Approval request has expired.")
        self._consumed.add(approval_id)
        self._pending.pop(approval_id, None)
        return {
            "approved": True,
            "approval_id": approval_id,
            "action": approval.action,
            "scope": approval.scope,
        }
