# Operator API Contract — Paper v1

This contract is intentionally thin. UI clients must not bypass the runtime, bot manager, or safety gates.

## Read operations

- `GET /status` — runtime readiness, kill-switch state, dry-run/trading mode, configured/enabled bot counts.
- `GET /bots` — persistent bot configurations.
- `GET /readiness` — fail-closed release/readiness checks and blockers.

## Mutating operations

- `POST /bots/{bot_id}/enable` — enable only after persistent configuration and risk profile validation.
- `POST /bots/{bot_id}/disable` — disable one bot.
- `POST /pause` — engage global kill switch and disable configured bots.

## Explicit exclusions

The Paper v1 UI has no live-money endpoint, no endpoint-selection control, no kill-switch bypass, and no direct broker-order endpoint. Orders flow only through the guarded runtime.

A release candidate remains NO-GO until required CI and virtual-day evidence is green.
