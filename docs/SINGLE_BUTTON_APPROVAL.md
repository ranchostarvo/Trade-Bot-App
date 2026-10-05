# Single-Button Approval

The operator experience should be one deliberate button press without turning approval into a safety bypass.

## Flow

1. System performs read-only preflight.
2. UI presents one approval card containing:
   - PAPER mode banner
   - action and exact scope
   - number of bots/orders
   - maximum new capital exposure
   - account/risk readiness
   - market-session status
   - kill-switch status
   - expiration time
3. Button text is explicit, e.g. **Approve Paper Batch — Max $2,500**.
4. Approval is single-use and time-limited.
5. After approval, every normal runtime risk/control gate still runs.
6. Any material change to scope requires a new approval.

## Never approved by this control

- Switching from paper to live
- Disabling the global kill switch
- Raising risk/capital limits
- Bypassing market-session validation
- Blind retry of an ambiguous broker submission
- Reusing an approval token
- Executing a materially different batch than the displayed scope

## Live trading

Paper-v1 single-button approval cannot authorize live-money trading. A future live implementation must use a separate, visibly distinct authorization design and release gate.
