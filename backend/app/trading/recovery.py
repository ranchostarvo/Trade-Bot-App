from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RecoveryResult:
    checked: int
    updated: int
    terminal: int
    open: int


class RecoveryManager:
    def __init__(self, order_tracker, order_journal, fill_accounting=None, fill_checkpoint_store=None):
        self.order_tracker = order_tracker
        self.order_journal = order_journal
        self.fill_accounting = fill_accounting
        self.fill_checkpoint_store = fill_checkpoint_store

    def reconcile_open_orders(self):
        saved = self.order_journal.open_orders()
        checked = updated = terminal = open_count = 0

        for order_id, previous in saved.items():
            checked += 1
            current = self.order_tracker.get(order_id)
            journal_filled = Decimal(str(previous.get("filled_qty", "0")))
            accounted_filled = (
                self.fill_checkpoint_store.get(order_id)
                if self.fill_checkpoint_store is not None
                else journal_filled
            )
            if accounted_filled > current.filled_qty:
                raise RuntimeError(
                    f"Accounted fill exceeds broker fill for order {order_id}."
                )
            fill_delta = current.filled_qty - accounted_filled

            if fill_delta < 0:
                raise RuntimeError(
                    f"Broker fill quantity regressed for order {order_id}."
                )

            if (
                current.status != previous.get("status")
                or fill_delta != 0
            ):
                updated += 1

            if fill_delta and self.fill_accounting is not None:
                snapshot_store = getattr(
                    self.fill_accounting, "snapshot_store", None
                )
                atomic_apply = getattr(
                    snapshot_store, "apply_fill_once", None
                )
                if atomic_apply is not None:
                    _, applied_delta = atomic_apply(
                        order_id,
                        current.symbol,
                        current.side,
                        current.filled_qty,
                    )
                    if applied_delta != fill_delta:
                        raise RuntimeError(
                            f"Atomic fill delta mismatch for order {order_id}."
                        )
                else:
                    delta_state = type(current)(
                        order_id=current.order_id,
                        symbol=current.symbol,
                        side=current.side,
                        status=current.status,
                        filled_qty=fill_delta,
                        filled_avg_price=current.filled_avg_price,
                        terminal=current.terminal,
                    )
                    self.fill_accounting.apply(delta_state)

                if self.fill_checkpoint_store is not None:
                    self.fill_checkpoint_store.set(
                        order_id,
                        current.filled_qty,
                    )

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
