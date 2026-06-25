"""
Built-in example agents (in-process) for quick evaluation demos.
"""

import random
from engine.agent import BaseAgent, AgentState, AgentSignal
from engine.scenario import Bar


class MATrendAgent(BaseAgent):
    """20/50 SMA crossover trend follower — long only."""

    def __init__(self, fast=20, slow=50):
        super().__init__("ma-trend", f"MA Crossover ({fast}/{slow})",
                         "Trend following using moving average crossovers")
        self.fast = fast
        self.slow = slow
        self.in_position = False

    def sma(self, closes, period):
        if len(closes) < period:
            return None
        return sum(closes[-period:]) / period

    def on_bar(self, bar: Bar, history: list[Bar], state: AgentState) -> AgentSignal:
        closes = [b.close for b in history]
        fast_ma = self.sma(closes, self.fast)
        slow_ma = self.sma(closes, self.slow)

        if fast_ma is None or slow_ma is None:
            return AgentSignal(action="hold", symbol=bar.timestamp, rationale="warming up")

        if fast_ma > slow_ma and not self.in_position:
            self.in_position = True
            return AgentSignal(
                action="buy", symbol="BTC/USDT", quantity=0.5, confidence=0.7,
                rationale=f"Golden cross: {self.fast}MA({fast_ma:.0f}) > {self.slow}MA({slow_ma:.0f})"
            )
        elif fast_ma < slow_ma and self.in_position:
            self.in_position = False
            return AgentSignal(
                action="close_long", symbol="BTC/USDT", confidence=0.6,
                rationale=f"Death cross: {self.fast}MA({fast_ma:.0f}) < {self.slow}MA({slow_ma:.0f})"
            )

        return AgentSignal(action="hold", symbol=bar.timestamp)


class RSIMeanReversionAgent(BaseAgent):
    """RSI(14) mean reversion with oversold/overbought thresholds."""

    def __init__(self, period=14, oversold=30, overbought=70):
        super().__init__("rsi-reversion", f"RSI Reversion ({period})",
                         "Mean reversion using RSI oversold/overbought signals")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.in_position = False

    def compute_rsi(self, closes):
        if len(closes) < self.period + 1:
            return None
        gains, losses = [], []
        for i in range(-self.period, 0):
            diff = closes[i] - closes[i - 1]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))
        avg_gain = sum(gains) / self.period
        avg_loss = sum(losses) / self.period
        if avg_loss == 0:
            return 100.0
        return 100.0 - (100.0 / (1.0 + avg_gain / avg_loss))

    def on_bar(self, bar: Bar, history: list[Bar], state: AgentState) -> AgentSignal:
        closes = [b.close for b in history]
        rsi_val = self.compute_rsi(closes)
        if rsi_val is None:
            return AgentSignal(action="hold", symbol=bar.timestamp, rationale="warming up")

        if rsi_val < self.oversold and not self.in_position:
            self.in_position = True
            return AgentSignal(
                action="buy", symbol="ETH/USDT", quantity=0.5,
                confidence=min(0.9, (self.oversold - rsi_val) / self.oversold + 0.5),
                rationale=f"RSI={rsi_val:.1f} oversold (<{self.oversold}), entering long"
            )
        elif rsi_val > self.overbought and self.in_position:
            self.in_position = False
            return AgentSignal(
                action="close_long", symbol="ETH/USDT", confidence=0.8,
                rationale=f"RSI={rsi_val:.1f} overbought (>{self.overbought}), taking profit"
            )
        return AgentSignal(action="hold", symbol=bar.timestamp)


class RandomBaselineAgent(BaseAgent):
    """Random strategy — serves as a noise-floor baseline."""

    def __init__(self, seed=42, trade_prob=0.05):
        super().__init__("random-baseline", "Random Baseline",
                         "Random entry/exit — represents noise-floor performance")
        self.rng = random.Random(seed)
        self.trade_prob = trade_prob
        self.in_position = False

    def on_bar(self, bar: Bar, history: list[Bar], state: AgentState) -> AgentSignal:
        if not self.in_position and self.rng.random() < self.trade_prob:
            self.in_position = True
            return AgentSignal(
                action=self.rng.choice(["buy"]), symbol="BTC/USDT", quantity=0.5,
                confidence=0.3, rationale="random entry"
            )
        elif self.in_position and self.rng.random() < self.trade_prob:
            self.in_position = False
            return AgentSignal(
                action="close_long", symbol="BTC/USDT", confidence=0.3,
                rationale="random exit"
            )
        return AgentSignal(action="hold", symbol=bar.timestamp)


BUILTIN_AGENTS: dict[str, BaseAgent] = {
    "ma-trend": MATrendAgent(),
    "rsi-reversion": RSIMeanReversionAgent(),
    "random-baseline": RandomBaselineAgent(),
}
