"""
Replay runner — executes an agent against a scenario bar-by-bar and records trades.
"""

import json
from pathlib import Path

from .scenario import Scenario, Bar
from .agent import BaseAgent, AgentState, AgentSignal
from .scoring import Trade
from .scoring import score_trades, EvaluationResult


class Runner:
    def __init__(self, scenario: Scenario, agent: BaseAgent, initial_capital: float | None = None):
        self.scenario = scenario
        self.agent = agent
        self.initial_capital = initial_capital or scenario.initial_capital
        self.trades: list[Trade] = []
        self.equity_curve: list[dict] = []
        self.state = AgentState(cash=self.initial_capital, equity=self.initial_capital)

    def run(self) -> EvaluationResult:
        agent = self.agent
        scenario = self.scenario
        bars = scenario.bars

        agent.on_start(self.initial_capital)

        position_dollars = 0.0
        entry_price = 0.0
        history: list[Bar] = []

        for i, bar in enumerate(bars):
            history.append(bar)
            # Equity = cash + unrealized position value
            unrealized = 0.0
            if position_dollars != 0:
                unrealized = position_dollars * (bar.close / entry_price - 1)
                if position_dollars < 0:
                    unrealized = abs(position_dollars) * (1 - bar.close / entry_price)
            total_equity = self.state.cash + unrealized
            self.state.equity = total_equity

            signal = agent.on_bar(bar, history, self.state)

            if signal.action in ("buy", "sell") and signal.quantity > 0:
                exec_price = signal.price if signal.price else bar.close
                side = signal.action

                # Close existing position first
                if position_dollars != 0:
                    realized = position_dollars * (exec_price / entry_price - 1)
                    if position_dollars < 0:
                        realized = abs(position_dollars) * (1 - exec_price / entry_price)
                    pnl_pct = realized / abs(position_dollars) if position_dollars != 0 else 0

                    self.trades.append(Trade(
                        entry_time=history[max(0, i-10)].timestamp,
                        exit_time=bar.timestamp,
                        side="long" if position_dollars > 0 else "short",
                        entry_price=entry_price,
                        exit_price=exec_price,
                        quantity=abs(position_dollars),
                        pnl=realized,
                        pnl_pct=pnl_pct,
                    ))
                    self.state.cash += realized
                    position_dollars = 0.0

                # Allocate capital fraction as position size
                allocated = self.state.cash * signal.quantity
                position_dollars = allocated if side == "buy" else -allocated
                entry_price = exec_price
                fee = allocated * scenario.taker_fee
                self.state.cash -= fee
                self.state.trade_count += 1

            elif signal.action in ("close_long", "close_short") and position_dollars != 0:
                exec_price = signal.price if signal.price else bar.close
                realized = position_dollars * (exec_price / entry_price - 1)
                if position_dollars < 0:
                    realized = abs(position_dollars) * (1 - exec_price / entry_price)
                pnl_pct = realized / abs(position_dollars) if position_dollars != 0 else 0

                self.trades.append(Trade(
                    entry_time=history[max(0, i-10)].timestamp,
                    exit_time=bar.timestamp,
                    side="long" if position_dollars > 0 else "short",
                    entry_price=entry_price,
                    exit_price=exec_price,
                    quantity=abs(position_dollars),
                    pnl=realized,
                    pnl_pct=pnl_pct,
                ))
                self.state.cash += realized
                position_dollars = 0.0

            self.state.position = position_dollars
            self.state.entry_price = entry_price

            # Recalculate equity at bar close
            unrealized = 0.0
            if position_dollars != 0:
                unrealized = position_dollars * (bar.close / entry_price - 1)
                if position_dollars < 0:
                    unrealized = abs(position_dollars) * (1 - bar.close / entry_price)
            self.state.equity = self.state.cash + unrealized

            # Record equity curve point every 5 bars
            if i % 5 == 0:
                self.equity_curve.append({
                    "timestamp": bar.timestamp,
                    "equity": round(self.state.equity, 2),
                    "cash": round(self.state.cash, 2),
                    "position": round(position_dollars, 2),
                })

        # Close any remaining position at last bar price
        if position_dollars != 0:
            last_price = bars[-1].close
            realized = position_dollars * (last_price / entry_price - 1)
            if position_dollars < 0:
                realized = abs(position_dollars) * (1 - last_price / entry_price)
            pnl_pct = realized / abs(position_dollars) if position_dollars != 0 else 0
            self.trades.append(Trade(
                entry_time=history[-10].timestamp if len(history) >= 10 else history[0].timestamp,
                exit_time=bars[-1].timestamp,
                side="long" if position_dollars > 0 else "short",
                entry_price=entry_price,
                exit_price=last_price,
                quantity=abs(position_dollars),
                pnl=realized,
                pnl_pct=pnl_pct,
            ))
            self.state.cash += realized
            self.state.equity = self.state.cash

        agent.on_finish()

        equity_values = [p["equity"] for p in self.equity_curve]
        if not equity_values:
            equity_values = [self.initial_capital]

        composite, breakdown, total_ret, sharpe, dd, win_rate, pf = score_trades(
            self.trades, equity_values, self.initial_capital, self.scenario.scoring_weights
        )

        return EvaluationResult(
            agent_id=agent.agent_id,
            agent_name=agent.name,
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            total_return=total_ret,
            sharpe_ratio=sharpe,
            max_drawdown=dd,
            win_rate=win_rate,
            profit_factor=pf if pf != float('inf') else 10.0,
            composite_score=composite,
            breakdown=breakdown,
            trades=self.trades,
            equity_curve=self.equity_curve,
        )


def run_evaluation(scenario_path: str | Path, agent: BaseAgent, data_dir: str | Path = ".") -> EvaluationResult:
    """Convenience: load a scenario and run an agent against it."""
    from .scenario import load_scenario

    scenario_dir = Path(scenario_path).parent if Path(scenario_path).is_file() else Path(scenario_path)
    scenario_id = Path(scenario_path).stem if Path(scenario_path).is_file() else "trending"

    scenario = load_scenario(scenario_id, scenario_dir)
    runner = Runner(scenario, agent)
    return runner.run()
