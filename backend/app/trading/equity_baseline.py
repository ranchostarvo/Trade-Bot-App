import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .risk import RiskRejected


class EquityBaselineStore:
    def __init__(self, path):
        self.path = Path(path)

    def _read(self):
        if not self.path.exists():
            return None

        try:
            with self.path.open(
                "r",
                encoding="utf-8",
            ) as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise RiskRejected(
                f"Unable to read equity baseline: {exc}"
            ) from exc

    def _write(self, trading_day, equity):
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "trading_day": trading_day.isoformat(),
            "start_equity": str(equity),
        }

        temp_path = self.path.with_suffix(
            self.path.suffix + ".tmp"
        )

        try:
            with temp_path.open(
                "w",
                encoding="utf-8",
            ) as handle:
                json.dump(
                    data,
                    handle,
                    indent=2,
                )
                handle.flush()

            temp_path.replace(self.path)

        except OSError as exc:
            raise RiskRejected(
                f"Unable to save equity baseline: {exc}"
            ) from exc

    def get_or_create(
        self,
        current_equity,
        trading_day=None,
    ):
        trading_day = trading_day or date.today()

        try:
            current_equity = Decimal(
                str(current_equity)
            )
        except (InvalidOperation, TypeError) as exc:
            raise RiskRejected(
                "Invalid current equity."
            ) from exc

        if current_equity <= 0:
            raise RiskRejected(
                "Current equity must be greater than zero."
            )

        data = self._read()

        if data is not None:
            stored_day = data.get("trading_day")

            if stored_day == trading_day.isoformat():
                try:
                    baseline = Decimal(
                        str(data["start_equity"])
                    )
                except (
                    KeyError,
                    InvalidOperation,
                    TypeError,
                ) as exc:
                    raise RiskRejected(
                        "Invalid persisted equity baseline."
                    ) from exc

                if baseline <= 0:
                    raise RiskRejected(
                        "Persisted equity baseline "
                        "must be greater than zero."
                    )

                return baseline

        self._write(
            trading_day,
            current_equity,
        )

        return current_equity
