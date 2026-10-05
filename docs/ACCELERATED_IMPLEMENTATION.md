# Accelerated Implementation Plan

Work proceeds in four overlapping tracks.

## Track A — Trading Core
Bot registry, risk profiles, bot manager, strategy contract, capital and order lifecycle.

## Track B — Operations
Operator API, global/per-bot controls, diagnostics, readiness, logs and alerts.

## Track C — App
Operational dashboard, bot list/detail, portfolio, orders, warnings and safety controls.

## Track D — Verification
100-bot virtual trading day, fault injection, restart testing, tiered CI and release gate.

## CI policy
1. Fast safety/unit tests for core changes.
2. Subsystem integration tests at coherent checkpoints.
3. Full 100-bot/fault/recovery release gate for release candidates.

## Development rules
- Paper-only broker boundary remains mandatory.
- Structural batch validation occurs before execution.
- Sequential v1 orchestration prevents shared-capital races.
- Live trading is outside Paper v1.
- Real Alpaca paper orders require explicit authorization.
- Validation evidence, not calendar pressure, controls live-money progression.
