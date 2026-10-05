# Paper Trading v1 — Frozen Scope

Paper Trading v1 is feature-frozen to the operational trading platform needed for safe 100-bot paper validation.

## In scope
- Up to 100 independently configured bots
- Stock, ETF, and crypto bot classes
- Conservative, moderate, and aggressive risk profiles
- Alpaca paper execution only
- Per-order risk ceiling and 2.5% daily-loss protection
- Persistent portfolio capital coordination
- Global kill switch and per-bot enabled/disabled state
- Idempotent order submission and ambiguous-submission recovery
- Persistent order/fill/position recovery across restart
- Market-session protection
- Runtime diagnostics and release readiness
- Operator API/dashboard for bots, portfolio, orders, warnings, and safety controls
- Deterministic 100-bot simulation/fault validation
- Basic ticker/asset analysis interface

## Deferred to v1.1+
- Unbounded or multi-process concurrent execution
- Additional brokers
- Live-money trading
- Advanced visualization/polish
- Strategy marketplace/plugin ecosystem
- Nonessential analytics and reporting

## Release rule
Scope additions require an explicit safety-critical reason. New convenience features are deferred until Paper v1 reaches release-candidate status.
