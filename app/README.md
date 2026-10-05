# Paper Trading Operational UI

Flutter operational console for Windows and iOS.

Features: runtime/readiness status, configured/enabled bot summary, bot enable/disable, global pause confirmation, refresh/error states, and explicit safety-mode notice.

Deliberate exclusions: no direct order entry, live-broker selector, kill-switch bypass, API-key field, or live-money control.

Build with `--dart-define=OPERATOR_API_URL=<operator-api-base-url>`. The console consumes only the frozen Paper v1 operator contract.
