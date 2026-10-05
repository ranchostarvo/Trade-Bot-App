from dataclasses import dataclass


@dataclass(frozen=True)
class RecoveryResult:
    checked: int
    updated: int
    terminal: int
    open: int


class RecoveryManager:
    def __init__(self, order_tracker, order_journal):
        self.order_tracker = order_tracker
        self.order_journal = order_journal

    def reconcile_open_orders(self):
        saved = self.order_journal.open_orders()
        checked = updated = terminal = open_count = 0

        for order_id, previous in saved.items():
            checked += 1
            current = self.order_tracker.get(order_id)

            if (
                current.status != previous.get("status")
                or str(current.filled_qty)
                != str(previous.get("filled_qty", "0"))
            ):
                updated += 1

            self.order_journal.record(current)

            if current.terminal:
                terminal += 1
            else:
                open_count += 1

        return RecoveryResult(
            checked=checked,
            updated=updated,
            terminal=terminal,
            open=open_count,
        )
