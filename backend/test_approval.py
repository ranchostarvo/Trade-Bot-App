from datetime import datetime, timedelta, timezone

from app.trading.approval import SingleButtonApproval
from app.trading.risk import RiskRejected

approvals = SingleButtonApproval()
expiry = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
item = approvals.request(
    "paper_order_batch", "bots:1-5|max:$2500",
    "5 paper orders, maximum new exposure $2,500", expiry,
)
result = approvals.approve(item.approval_id)
assert result["approved"] is True

try:
    approvals.approve(item.approval_id)
    raise AssertionError("Approval reuse must fail closed.")
except RiskRejected:
    pass

expired = approvals.request(
    "start_paper_batch", "bot:1", "one paper bot",
    (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
)
try:
    approvals.approve(expired.approval_id)
    raise AssertionError("Expired approval must fail closed.")
except RiskRejected:
    pass

try:
    approvals.request("enable_live_trading", "all", "live", expiry)
    raise AssertionError("Live authorization must not be supported.")
except RiskRejected:
    pass

print("SINGLE-BUTTON APPROVAL: PASS")
print("Single use: PASS")
print("Expiry: PASS")
print("Live authorization prohibited: PASS")
print("Real Alpaca order submitted: NO")
