from app.trading.release_gate import PaperV1ReleaseGate

gate=PaperV1ReleaseGate()
complete={name: True for name in gate.REQUIRED}
report=gate.assess(complete)
assert report.go is True and report.blockers == ()

for required in gate.REQUIRED:
    evidence=dict(complete)
    evidence.pop(required)
    report=gate.assess(evidence)
    assert report.go is False
    assert required in report.blockers

for required in ("system_invariants","operator_api","asset_analysis"):
    evidence=dict(complete)
    evidence[required]=False
    report=gate.assess(evidence)
    assert report.go is False and required in report.blockers

assert gate.assess({}).go is False
assert set(gate.assess({}).blockers)==set(gate.REQUIRED)
print("PAPER V1 RELEASE EVIDENCE MATRIX: PASS")
