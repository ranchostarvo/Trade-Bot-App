# Paper Trading v1 Release Candidate Gate

Paper Trading v1 is **NO-GO by default**. A release candidate may be designated only when every required evidence item is green.

## Required evidence

- Backend CI green at the candidate commit.
- Runtime startup and restart recovery pass.
- Persistent kill switch passes.
- Daily-loss and per-order limits pass.
- Combined reserved + invested capital ceiling passes.
- Submission idempotency and ambiguous-transmission recovery pass.
- Exchange-session/calendar gate passes.
- Fill accounting, sell transition recovery, and position recovery pass.
- 100-bot whole-batch preflight passes.
- Deterministic 100-bot virtual trading day passes with zero duplicate submissions.
- Paper-only broker boundary passes.

## Progression

A green RC authorizes **controlled Alpaca paper validation only**. It does not authorize live-money trading. Real Alpaca paper orders remain subject to explicit operator authorization. Live trading remains outside Paper v1.

## Failure policy

A missing result is a failure. A corrupt persistent state fails closed. Tests are fixed at the model or implementation layer; safety invariants are not weakened to obtain green CI.


## Cross-ledger crash recovery
Buy fills use a persistent write-ahead transition journal. Runtime readiness is blocked until interrupted buy transitions are either deterministically reconciled or rejected fail-closed. CI exercises prepared, exposure-applied, allocation-applied, conflicting-state, and repeated-restart behavior.
