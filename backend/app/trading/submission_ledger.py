import json
from pathlib import Path


class DuplicateOrder(RuntimeError):
    pass


class SubmissionLedger:
    def __init__(self, path):
        self.path = Path(path)

    def _read(self):
        if not self.path.exists():
            return {}
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Unable to read submission ledger: {exc}") from exc
        if not isinstance(data, dict):
            raise RuntimeError("Submission ledger must contain an object.")
        return data

    def reserve(self, client_order_id, fingerprint):
        client_order_id = str(client_order_id or "").strip()
        if not client_order_id:
            raise ValueError("client_order_id is required.")

        data = self._read()
        existing = data.get(client_order_id)
        if existing is not None:
            raise DuplicateOrder(
                f"Order {client_order_id} was already reserved."
            )

        data[client_order_id] = {"fingerprint": str(fingerprint)}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        with temp.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.flush()
        temp.replace(self.path)

    def get(self, client_order_id):
        return self._read().get(client_order_id)
