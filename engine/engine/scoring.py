"""
Scoring engine for agent evaluation.

Computes 5 standard dimensions from a trade log:
  1. Total Return (%)
  2. Sharpe Ratio (annualized, assuming 0% risk-free rate)
  3. Max Drawdown (%)
  4. Win Rate (%)
  5. Profit Factor

Outputs a normalized 0-100 score per dimension and a weighted composite.
"""

import math
from dataclasses import dataclass, field


@dataclass
class Trade:
    entry_time: str
    exit_time: str
    side: str            # "long" or "short"
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float

    def to_dict(self) -> dict:
        return {
            "entry_time": self.entry_time,
            "exit_time": self.exit_time,
            "side": self.side,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "quantity": self.quantity,
            "pnl": round(self.pnl, 2),
            "pnl_pct": round(self.pnl_pct, 4),
        }


@dataclass
class ScoreBreakdown:
    dimension: str
    raw_value: float
    normalized: float       # 0-100
    weight: float
    weighted: float
    interpretation: str

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension,
            "raw_value": round(self.raw_value, 4),
            "normalized": round(self.normalized, 1),
            "weight": round(self.weight, 2),
            "weighted": round(self.weighted, 2),
            "interpretation": self.interpretation,
        }


@dataclass
class EvaluationResult:
    agent_id: str
    agent_name: str
    scenario_id: str
    scenario_name: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    composite_score: float
    breakdown: list[ScoreBreakdown] = field(default_factory=list)
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[dict] = field(default_factory=list)
    summary: str = ""
    rank: int = 0

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "metrics": {
                "total_return": round(self.total_return, 4),
                "sharpe_ratio": round(self.sharpe_ratio, 2),
                "max_drawdown": round(self.max_drawdown, 4),
                "win_rate": round(self.win_rate, 4),
                "profit_factor": round(self.profit_factor, 2),
                "composite_score": round(self.composite_score, 1),
            },
            "breakdown": [b.to_dict() for b in self.breakdown],
            "trade_count": len(self.trades),
            "trades": [t.to_dict() for t in self.trades[:20]],
            "equity_curve": self.equity_curve[:100],
            "summary": self.summary,
            "rank": self.rank,
        }


def compute_returns(equity: list[float]) -> list[float]:
    return [(equity[i] - equity[i-1]) / equity[i-1] for i in range(1, len(equity)) if equity[i-1] > 0]


def annualized_sharpe(returns: list[float], periods_per_year: int = 365) -> float:
    if len(returns) < 2:
        return 0.0
    # Use population std for consistency
    mean_ret = sum(returns) / len(returns)
    var = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
    std = math.sqrt(var)
    if std == 0:
        return 0.0
    return (mean_ret / std) * math.sqrt(periods_per_year)


def max_drawdown(equity: list[float]) -> float:
    peak = equity[0]
    max_dd = 0.0
    for val in equity:
        if val > peak:
            peak = val
        dd = (peak - val) / peak if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
    return max_dd


def profit_factor(trades: list[Trade]) -> float:
    gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
    gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
    if gross_loss == 0:
        return float('inf') if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def normalize(value: float, best: float, worst: float, higher_is_better: bool = True) -> float:
    """Clamp to 0-100 scale relative to a reference range."""
    if best == worst:
        return 50.0
    if higher_is_better:
        clamped = max(worst, min(best, value))
        return (clamped - worst) / (best - worst) * 100
    else:
        clamped = max(worst, min(best, value))
        return (best - clamped) / (best - worst) * 100


def score_trades(
    trades: list[Trade],
    equity_curve: list[float],
    initial_capital: float,
    weights: dict,
    all_results: list["EvaluationResult"] | None = None,
) -> tuple[float, list[ScoreBreakdown], float, float, float, float, float]:
    """Compute all metrics and composite score from a trade log."""

    # Raw metrics
    if equity_curve and len(equity_curve) > 1:
        final_equity = equity_curve[-1]
        total_return = (final_equity - initial_capital) / initial_capital
        returns = compute_returns(equity_curve)
        sharpe = annualized_sharpe(returns)
        dd = max_drawdown(equity_curve)
    else:
        total_return = 0.0
        sharpe = 0.0
        dd = 0.0

    win_rate = sum(1 for t in trades if t.pnl > 0) / len(trades) if trades else 0.0
    pf = profit_factor(trades)
    pf_clamped = min(pf, 10.0)  # cap extreme profit factors

    # Normalize against peer results if available
    if all_results and len(all_results) > 1:
        returns_all = [r.total_return for r in all_results]
        sharpes_all = [r.sharpe_ratio for r in all_results]
        dds_all = [r.max_drawdown for r in all_results]
        wins_all = [r.win_rate for r in all_results]
        pfs_all = [min(r.profit_factor, 10.0) for r in all_results]

        ret_score = normalize(total_return, max(returns_all), min(returns_all))
        sharpe_score = normalize(sharpe, max(sharpes_all), min(sharpes_all))
        dd_score = normalize(dd, min(dds_all), max(dds_all), higher_is_better=False)
        win_score = normalize(win_rate, max(wins_all), min(wins_all))
        pf_score = normalize(pf_clamped, max(pfs_all), min(pfs_all))
    else:
        # Absolute reference scales
        ret_score = normalize(total_return, 1.0, -0.5)
        sharpe_score = normalize(sharpe, 3.0, -1.0)
        dd_score = normalize(dd, 0.05, 0.50, higher_is_better=False)
        win_score = normalize(win_rate, 0.80, 0.30)
        pf_score = normalize(pf_clamped, 3.0, 0.5)

    breakdown = [
        ScoreBreakdown("total_return", total_return, ret_score, weights.get("total_return", 0.25), ret_score * weights.get("total_return", 0.25),
                       "Outstanding" if total_return > 0.3 else "Good" if total_return > 0.1 else "Below average" if total_return < 0 else "Negative"),
        ScoreBreakdown("sharpe_ratio", sharpe, sharpe_score, weights.get("sharpe_ratio", 0.20), sharpe_score * weights.get("sharpe_ratio", 0.20),
                       "Excellent" if sharpe > 2.0 else "Good" if sharpe > 1.0 else "Fair" if sharpe > 0.5 else "Weak"),
        ScoreBreakdown("max_drawdown", dd, dd_score, weights.get("max_drawdown", 0.20), dd_score * weights.get("max_drawdown", 0.20),
                       "Very low risk" if dd < 0.05 else "Controlled" if dd < 0.15 else "Moderate" if dd < 0.25 else "High risk"),
        ScoreBreakdown("win_rate", win_rate, win_score, weights.get("win_rate", 0.15), win_score * weights.get("win_rate", 0.15),
                       "Elite" if win_rate > 0.7 else "Solid" if win_rate > 0.5 else "Average" if win_rate > 0.4 else "Low"),
        ScoreBreakdown("profit_factor", pf, pf_score, weights.get("profit_factor", 0.20), pf_score * weights.get("profit_factor", 0.20),
                       "Excellent" if pf > 2.0 else "Good" if pf > 1.5 else "Marginal" if pf > 1.0 else "Losing"),
    ]

    composite = sum(b.weighted for b in breakdown)
    return composite, breakdown, total_return, sharpe, dd, win_rate, pf
