import json
from pathlib import Path


class RiskStateStore:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        if not self.path.exists():
            return {
                "kill_switch_active": False,
                "kill_switch_reason": "",
            }

        try:
            with self.path.open(
                "r",
                encoding="utf-8",
            ) as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            # FAIL CLOSED:
            # unreadable safety state means trading must stop.
            return {
                "kill_switch_active": True,
                "kill_switch_reason":
                    f"Risk-state storage failure: {exc}",
            }

        return {
            "kill_switch_active": bool(
                data.get("kill_switch_active", True)
            ),
            "kill_switch_reason": str(
                data.get(
                    "kill_switch_reason",
                    "Invalid persisted risk state.",
                )
            ),
        }

    def save_kill_switch(self, active, reason=""):
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        state = {
            "kill_switch_active": bool(active),
            "kill_switch_reason": str(reason),
        }

        temp_path = self.path.with_suffix(
            self.path.suffix + ".tmp"
        )

        with temp_path.open(
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                state,
                handle,
                indent=2,
            )
            handle.flush()

        temp_path.replace(self.path)
