from app.trading.release_gate import PaperV1ReleaseGate

gate = PaperV1ReleaseGate()
evidence = {name: True for name in gate.REQUIRED}
report = gate.assess(evidence)
assert report.go
assert report.blockers == ()

evidence["sell_recovery"] = False
report = gate.assess(evidence)
assert not report.go
assert report.blockers == ("sell_recovery",)

evidence.pop("hundred_bot_virtual_day")
report = gate.assess(evidence)
assert not report.go
assert "hundred_bot_virtual_day" in report.blockers

print("PAPER V1 RELEASE GATE: PASS")
print("All evidence required for GO: PASS")
print("Missing/failed evidence => NO-GO: PASS")
print("Real Alpaca order submitted: NO")
