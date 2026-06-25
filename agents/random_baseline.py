"""
Example Agent 3: Random strategy (baseline/placebo)
Generates random signals for baseline comparison.
"""

import json
import sys
import random


class RandomAgent:
    """Random trader — baseline to ensure the benchmark detects noise."""

    def __init__(self, seed=42, trade_prob=0.05):
        self.rng = random.Random(seed)
        self.trade_prob = trade_prob
        self.in_position = False

    def step(self, bar, history, state):
        action = "hold"
        quantity = 0.0
        rationale = ""

        if not self.in_position and self.rng.random() < self.trade_prob:
            side = self.rng.choice(["buy", "sell"])
            action = side
            quantity = 0.5
            rationale = "random entry"
            self.in_position = True
        elif self.in_position and self.rng.random() < self.trade_prob:
            action = "close_long" if self.in_position else "close_short"
            rationale = "random exit"
            self.in_position = False

        return {
            "action": action,
            "symbol": "BTC/USDT",
            "price": None,
            "quantity": quantity,
            "confidence": 0.3,
            "rationale": rationale,
        }


if __name__ == "__main__":
    agent = RandomAgent()
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
