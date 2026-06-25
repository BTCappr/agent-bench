"""
Example Agent 2: Mean Reversion (RSI-based)
Uses RSI(14) with oversold/overbought thresholds to trade reversions.
"""

import json
import sys


class RSIAgent:
    """RSI(14) mean reversion trader."""

    def __init__(self, period=14, oversold=30, overbought=70):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.in_position = False
        self.entry_price = 0.0

    def rsi(self, closes):
        if len(closes) < self.period + 1:
            return None
        gains = []
        losses = []
        for i in range(-self.period, 0):
            diff = closes[i] - closes[i-1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-diff)
        avg_gain = sum(gains) / self.period
        avg_loss = sum(losses) / self.period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def step(self, bar, history, state):
        closes = [b["close"] for b in history]
        rsi_val = self.rsi(closes)

        action = "hold"
        quantity = 0.0
        rationale = f"RSI={rsi_val:.0f}" if rsi_val else "insufficient data"
        confidence = 0.0

        if rsi_val:
            if rsi_val < self.oversold and not self.in_position:
                action = "buy"
                quantity = 0.5
                rationale = f"RSI={rsi_val:.0f} oversold, entering long"
                confidence = min(0.9, (self.oversold - rsi_val) / self.oversold + 0.5)
                self.in_position = True
                self.entry_price = bar["close"]
            elif rsi_val > self.overbought and self.in_position:
                action = "close_long"
                rationale = f"RSI={rsi_val:.0f} overbought, taking profit"
                confidence = 0.8
                self.in_position = False

        return {
            "action": action,
            "symbol": "ETH/USDT",
            "price": None,
            "quantity": quantity,
            "confidence": round(confidence, 3),
            "rationale": rationale,
        }


if __name__ == "__main__":
    agent = RSIAgent()
    for line in sys.stdin:
        try:
            msg = json.loads(line.strip())
            bar = msg["bar"]
            history = []
            state = msg.get("state", {})
            resp = agent.step(bar, history, state)
            print(json.dumps(resp), flush=True)
        except (json.JSONDecodeError, KeyError):
            print(json.dumps({"action": "hold", "symbol": "", "quantity": 0, "confidence": 0, "rationale": "parse error"}), flush=True)
