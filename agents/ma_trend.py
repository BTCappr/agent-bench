"""
Example Agent 1: Trend Following (MA Crossover)
Uses 20/50-period SMA crossover to generate long-only signals.
"""

import json
import sys

class MATrendAgent:
    """20/50 SMA crossover trend follower."""

    def __init__(self, fast=20, slow=50):
        self.fast = fast
        self.slow = slow
        self.in_position = False
        self.entry_price = 0.0

    def sma(self, closes, period):
        if len(closes) < period:
            return None
        return sum(closes[-period:]) / period

    def step(self, bar, history, state):
        closes = [b["close"] for b in history]
        fast_ma = self.sma(closes, self.fast)
        slow_ma = self.sma(closes, self.slow)

        action = "hold"
        quantity = 0.0
        rationale = ""

        if fast_ma and slow_ma:
            if fast_ma > slow_ma and not self.in_position:
                action = "buy"
                quantity = 0.5  # 50% of capital in position
                rationale = f"Golden cross: {self.fast}MA > {self.slow}MA"
                self.in_position = True
                self.entry_price = bar["close"]
            elif fast_ma < slow_ma and self.in_position:
                action = "close_long"
                rationale = f"Death cross: {self.fast}MA < {self.slow}MA"
                self.in_position = False

        return {
            "action": action,
            "symbol": "BTC/USDT",
            "price": None,
            "quantity": quantity,
            "confidence": 0.7 if action != "hold" else 0.0,
            "rationale": rationale,
        }


if __name__ == "__main__":
    agent = MATrendAgent()
    for line in sys.stdin:
        try:
            msg = json.loads(line.strip())
            bar = msg["bar"]
            history = []  # history not passed via stdin protocol; agent tracks internally
            state = msg.get("state", {})
            resp = agent.step(bar, history, state)
            print(json.dumps(resp), flush=True)
        except (json.JSONDecodeError, KeyError):
            print(json.dumps({"action": "hold", "symbol": "", "quantity": 0, "confidence": 0, "rationale": "parse error"}), flush=True)
