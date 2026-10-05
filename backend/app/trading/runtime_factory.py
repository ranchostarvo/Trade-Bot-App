from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from app.brokers.alpaca import AlpacaClient

from .account_state import AlpacaAccountStateProvider
from .equity_baseline import EquityBaselineStore
from .execution import ExecutionEngine
from .kill_switch import KillSwitch
from .order_journal import OrderJournal
from .order_tracker import OrderTracker
from .recovery import RecoveryManager
from .risk import RiskConfig, RiskEngine
from .risk_store import RiskStateStore
from .runtime import PaperTradingRuntime
from .submission_ledger import SubmissionLedger


@dataclass(frozen=True)
class RuntimePaths:
    root: Path

    @property
    def risk_state(self):
        return self.root / "risk_state.json"

    @property
    def equity_baseline(self):
        return self.root / "equity_baseline.json"

    @property
    def order_journal(self):
        return self.root / "order_journal.json"

    @property
    def submission_ledger(self):
        return self.root / "submission_ledger.json"


def build_paper_runtime(
    state_dir,
    broker=None,
    trading_enabled=False,
    dry_run=True,
    max_order_notional=Decimal("500"),
    max_daily_loss_pct=Decimal("2.5"),
):
    paths = RuntimePaths(Path(state_dir))
    broker = broker or AlpacaClient()

    # Hard safety boundary: this factory is paper-only.
    config = getattr(broker, "config", None)
    if config is not None and not getattr(config, "paper", False):
        raise RuntimeError("Paper runtime refuses a non-paper broker.")

    kill_switch = KillSwitch(
        store=RiskStateStore(paths.risk_state),
    )
    baseline = EquityBaselineStore(paths.equity_baseline)
    account = AlpacaAccountStateProvider(
        broker,
        equity_baseline_store=baseline,
    )
    risk = RiskEngine(RiskConfig(
        max_order_notional=Decimal(str(max_order_notional)),
        max_daily_loss_pct=Decimal(str(max_daily_loss_pct)),
        trading_enabled=bool(trading_enabled),
        dry_run=bool(dry_run),
    ))
    ledger = SubmissionLedger(paths.submission_ledger)
    execution = ExecutionEngine(
        risk_engine=risk,
        kill_switch=kill_switch,
        account_state_provider=account,
        broker=broker,
        submission_ledger=ledger,
    )
    journal = OrderJournal(paths.order_journal)
    tracker = OrderTracker(broker)
    recovery = RecoveryManager(tracker, journal)

    return PaperTradingRuntime(
        execution_engine=execution,
        recovery_manager=recovery,
        kill_switch=kill_switch,
    )
