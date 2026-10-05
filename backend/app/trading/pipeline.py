from dataclasses import dataclass

from .execution import ExecutionEngine
from .signal import MarketSnapshot, ThresholdStrategy


@dataclass
class ProposalPipeline:
    strategy: ThresholdStrategy
    execution: ExecutionEngine

    @classmethod
    def development(cls, risk_engine=None):
        return cls(
            strategy=ThresholdStrategy(),
            execution=ExecutionEngine(risk_engine=risk_engine),
        )

    def process(self, market: MarketSnapshot, account_state=None):
        signal = self.strategy.evaluate(market)
        order = self.strategy.propose_order(signal)

        if order is None:
            return {
                "signal": signal.action,
                "reason": signal.reason,
                "order_proposed": False,
                "submitted": False,
                "status": "NO_ACTION",
            }

        result = self.execution.execute(order, account_state=account_state)
        return {
            "signal": signal.action,
            "reason": signal.reason,
            "order_proposed": True,
            **result,
        }
