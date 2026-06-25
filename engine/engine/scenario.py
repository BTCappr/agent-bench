"""
Scenario loader & market replay engine.

A Scenario defines a market environment with OHLCV data, metadata about
the market regime, and scoring weights for the evaluation dimensions.
"""

import json
import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import random


@dataclass
class Bar:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


@dataclass
class Scenario:
    id: str
    name: str
    description: str
    regime: str               # "trending", "ranging", "volatile"
    symbol: str
    interval: str             # "1h", "4h", "1d"
    bars: list[Bar] = field(default_factory=list)
    scoring_weights: dict = field(default_factory=lambda: {
        "total_return": 0.25,
        "sharpe_ratio": 0.20,
        "max_drawdown": 0.20,
        "win_rate": 0.15,
        "profit_factor": 0.20,
    })
    initial_capital: float = 10000.0
    maker_fee: float = 0.001   # 10 bps
    taker_fee: float = 0.002   # 20 bps

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "regime": self.regime,
            "symbol": self.symbol,
            "interval": self.interval,
            "bar_count": len(self.bars),
            "scoring_weights": self.scoring_weights,
            "initial_capital": self.initial_capital,
            "date_range": f"{self.bars[0].timestamp} → {self.bars[-1].timestamp}" if self.bars else "empty",
        }

    @staticmethod
    def from_json(path: str | Path) -> "Scenario":
        with open(path, "r") as f:
            data = json.load(f)
        scenario = Scenario(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            regime=data["regime"],
            symbol=data["symbol"],
            interval=data["interval"],
            initial_capital=data.get("initial_capital", 10000.0),
            maker_fee=data.get("maker_fee", 0.001),
            taker_fee=data.get("taker_fee", 0.002),
        )
        if "scoring_weights" in data:
            scenario.scoring_weights = data["scoring_weights"]
        return scenario

    def load_bars_from_csv(self, path: str | Path):
        self.bars = []
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.bars.append(Bar(
                    timestamp=row["timestamp"],
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                ))

    def generate_synthetic_bars(self, count: int = 200, seed: int = 42):
        """Generate synthetic OHLCV bars for a given market regime."""
        rng = random.Random(seed)
        self.bars = []
        price = 50000.0

        if self.regime == "trending":
            drift_daily = 0.002
            vol_daily = 0.015
        elif self.regime == "volatile":
            drift_daily = -0.001
            vol_daily = 0.035
        else:  # ranging
            drift_daily = 0.0
            vol_daily = 0.008

        for i in range(count):
            ts = f"2024-{1 + i // 30:02d}-{1 + i % 30:02d}T00:00:00Z"

            # Random walk with regime-specific means
            daily_ret = rng.gauss(drift_daily, vol_daily)
            close = price * (1 + daily_ret)

            intra_range = abs(close - price) * rng.uniform(0.3, 1.5)
            high = max(price, close) + intra_range * rng.random() * 0.4
            low = min(price, close) - intra_range * rng.random() * 0.4
            open_p = price
            volume = (abs(daily_ret) + 0.002) * price * rng.uniform(8, 80)

            self.bars.append(Bar(
                timestamp=ts,
                open=open_p,
                high=high,
                low=low,
                close=close,
                volume=volume,
            ))
            price = close


def load_scenario(scenario_id: str, data_dir: str | Path = "scenarios") -> Scenario:
    """Load a scenario by ID, with synthetic fallback."""
    data_dir = Path(data_dir)
    json_path = data_dir / f"{scenario_id}.json"
    csv_path = data_dir / f"{scenario_id}.csv"

    scenario = Scenario.from_json(json_path)

    if csv_path.exists():
        scenario.load_bars_from_csv(csv_path)
    else:
        count = {"trending": 200, "ranging": 200, "volatile": 150}.get(scenario.regime, 200)
        scenario.generate_synthetic_bars(count)

    return scenario
