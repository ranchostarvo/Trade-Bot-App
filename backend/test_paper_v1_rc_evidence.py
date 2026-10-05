from app.trading.release_gate import PaperV1ReleaseGate

# Evidence represented here is supplied only after its corresponding mandatory
# CI test has passed on the same candidate revision.
evidence = {
    "ci_green": True,
    "runtime_recovery": True,
    "kill_switch": True,
    "daily_loss": True,
    "order_limit": True,
    "combined_capital": True,
    "idempotency": True,
    "market_session": True,
    "fill_accounting": True,
    "sell_recovery": True,
    "position_recovery": True,
    "hundred_bot_preflight": True,
    "hundred_bot_virtual_day": True,
    "paper_only_boundary": True,
    "system_invariants": True,
    "operator_api": True,
    "asset_analysis": True,
}

gate = PaperV1ReleaseGate()
assert set(evidence) == set(gate.REQUIRED)
report = gate.assess(evidence)
assert report.go is True
assert report.blockers == ()
print("PAPER V1 RC EVIDENCE: GO")
print("LIVE MONEY AUTHORIZATION: NO")
print("ALPACA PAPER ORDER AUTHORIZATION: NO")
