from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from app.brokers.alpaca import AlpacaClient

from .account_state import AlpacaAccountStateProvider
from .capital_coordinator import CapitalConfig, PortfolioCapitalCoordinator
from .capital_lifecycle import CapitalLifecycle
from .capital_transition import CapitalTransition
from .exposure_ledger import PortfolioExposureLedger
from .equity_baseline import EquityBaselineStore
from .execution import ExecutionEngine
from .fill_accounting import FillAccounting
from .fill_checkpoint import FillCheckpointStore
from .exchange_calendar import AlpacaExchangeCalendar
from .market_session import USMarketSessionClock
from .session_guard import MarketSessionGuard
from .kill_switch import KillSwitch
from .lifecycle import OrderLifecycleService
from .order_journal import OrderJournal
from .order_tracker import OrderTracker
from .position_reconciler import PositionReconciler
from .position_recovery import PositionRecoveryManager
from .position_snapshot import PositionSnapshotStore
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

    @property
    def position_snapshot(self):
        return self.root / "position_snapshot.json"

    @property
    def fill_checkpoint(self):
        return self.root / "fill_checkpoint.json"

    @property
    def capital_reservations(self):
        return self.root / "capital_reservations.json"

    @property
    def portfolio_exposure(self):
        return self.root / "portfolio_exposure.json"


def build_paper_runtime(
    state_dir,
    broker=None,
    trading_enabled=False,
    dry_run=True,
    max_order_notional=Decimal("500"),
    max_daily_loss_pct=Decimal("2.5"),
    max_total_allocated=Decimal("50000"),
    reserve_cash=Decimal("5000"),
    allow_test_broker=False,
):
    paths = RuntimePaths(Path(state_dir))
    broker = broker or AlpacaClient()

    # Hard safety boundary: this factory is paper-only.
    config = getattr(broker, "config", None)
    if config is None:
        if not allow_test_broker:
            raise RuntimeError(
                "Paper runtime requires a broker with explicit paper-mode configuration."
            )
    elif not getattr(config, "paper", False):
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
    session_guard = MarketSessionGuard(
        USMarketSessionClock(),
        AlpacaExchangeCalendar(broker),
    )
    capital = PortfolioCapitalCoordinator(
        CapitalConfig(
            max_total_allocated=Decimal(str(max_total_allocated)),
            reserve_cash=Decimal(str(reserve_cash)),
        ),
        paths.capital_reservations,
    )
    exposure = PortfolioExposureLedger(
        paths.portfolio_exposure,
        Decimal(str(max_total_allocated)),
    )
    capital_transition = CapitalTransition(capital, exposure)
    execution = ExecutionEngine(
        risk_engine=risk,
        kill_switch=kill_switch,
        account_state_provider=account,
        broker=broker,
        submission_ledger=ledger,
        session_guard=session_guard,
        capital_coordinator=capital,
        available_cash_provider=account.get_available_cash,
        invested_capital_provider=lambda: exposure.total_invested,
    )
    journal = OrderJournal(paths.order_journal)
    tracker = OrderTracker(broker)
    position_store = PositionSnapshotStore(paths.position_snapshot)
    fill_accounting = FillAccounting(position_store)
    fill_checkpoint = FillCheckpointStore(paths.fill_checkpoint)
    recovery = RecoveryManager(
        tracker,
        journal,
        fill_accounting=fill_accounting,
        fill_checkpoint_store=fill_checkpoint,
    )
    position_recovery = PositionRecoveryManager(
        PositionReconciler(broker),
        position_store,
    )
    lifecycle = OrderLifecycleService(
        execution,
        journal,
        tracker,
        fill_accounting,
        capital_lifecycle=CapitalLifecycle(capital),
        capital_transition=capital_transition,
    )

    return PaperTradingRuntime(
        execution_engine=execution,
        recovery_manager=recovery,
        kill_switch=kill_switch,
        position_recovery_manager=position_recovery,
        lifecycle_service=lifecycle,
    )
