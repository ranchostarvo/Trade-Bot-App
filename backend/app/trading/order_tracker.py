from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


TERMINAL_ORDER_STATUSES = {
    "filled",
    "canceled",
    "expired",
    "rejected",
}


@dataclass(frozen=True)
class OrderState:
    order_id: str
    symbol: str
    side: str
    status: str
    filled_qty: Decimal
    filled_avg_price: Decimal | None
    terminal: bool


class OrderTracker:
    def __init__(self, broker):
        self.broker = broker

    def get(self, order_id: str) -> OrderState:
        if not order_id or not order_id.strip():
            raise ValueError("Order ID is required.")

        raw = self.broker.get_order(order_id.strip())
        status = str(raw.get("status", "")).strip().lower()
        if not status:
            raise ValueError("Broker order status is missing.")

        try:
            filled_qty = Decimal(str(raw.get("filled_qty") or "0"))
            price_raw = raw.get("filled_avg_price")
            filled_avg_price = (
                Decimal(str(price_raw))
                if price_raw not in (None, "")
                else None
            )
        except (InvalidOperation, TypeError) as exc:
            raise ValueError("Broker returned invalid fill data.") from exc

        return OrderState(
            order_id=str(raw.get("id") or order_id),
            symbol=str(raw.get("symbol") or "").upper(),
            side=str(raw.get("side") or "").lower(),
            status=status,
            filled_qty=filled_qty,
            filled_avg_price=filled_avg_price,
            terminal=status in TERMINAL_ORDER_STATUSES,
        )
