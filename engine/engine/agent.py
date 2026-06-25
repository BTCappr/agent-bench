"""
Agent adapter protocol — the standard interface agents implement to be benchmarked.

An agent receives market data (OHLCV bars) and returns trade decisions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json
import subprocess
import sys
from pathlib import Path

from .scenario import Bar


@dataclass
class AgentSignal:
    action: str           # "buy", "sell", "close_long", "close_short", "hold"
    symbol: str
    price: float | None = None   # None = use next bar open
    quantity: float = 0.0
    confidence: float = 0.0
    rationale: str = ""

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "symbol": self.symbol,
            "price": self.price,
            "quantity": self.quantity,
            "confidence": round(self.confidence, 3),
            "rationale": self.rationale,
        }


@dataclass
class AgentState:
    position: float = 0.0        # positive = long, negative = short
    entry_price: float = 0.0
    equity: float = 0.0
    cash: float = 0.0
    trade_count: int = 0

    def to_dict(self) -> dict:
        return {
            "position": round(self.position, 6),
            "entry_price": round(self.entry_price, 2),
            "equity": round(self.equity, 2),
            "cash": round(self.cash, 2),
            "trade_count": self.trade_count,
        }


class BaseAgent(ABC):
    """Agents implement this to participate in AgentBench evaluations."""

    def __init__(self, agent_id: str, name: str, description: str = ""):
        self.agent_id = agent_id
        self.name = name
        self.description = description

    @abstractmethod
    def on_bar(self, bar: Bar, history: list[Bar], state: AgentState) -> AgentSignal:
        """Called for each new bar. Return a trading signal."""
        ...

    def on_start(self, initial_capital: float):
        """Called before the scenario starts."""
        pass

    def on_finish(self):
        """Called after the scenario ends."""
        pass

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
        }


class ExternalAgent(BaseAgent):
    """Agent that runs as a subprocess, communicating via stdin/stdout JSON lines."""

    def __init__(self, agent_id: str, name: str, command: list[str], description: str = ""):
        super().__init__(agent_id, name, description)
        self.command = command
        self._proc: subprocess.Popen | None = None

    def on_start(self, initial_capital: float):
        self._proc = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def on_bar(self, bar: Bar, history: list[Bar], state: AgentState) -> AgentSignal:
        if self._proc is None or self._proc.stdin is None or self._proc.stdout is None:
            return AgentSignal(action="hold", symbol=bar.timestamp, rationale="process not running")

        request = json.dumps({
            "bar": bar.to_dict(),
            "state": state.to_dict(),
            "history_len": len(history),
        })
        try:
            self._proc.stdin.write(request + "\n")
            self._proc.stdin.flush()
            resp_line = self._proc.stdout.readline()
            data = json.loads(resp_line)
            return AgentSignal(
                action=data.get("action", "hold"),
                symbol=data.get("symbol", ""),
                price=data.get("price"),
                quantity=data.get("quantity", 0),
                confidence=data.get("confidence", 0),
                rationale=data.get("rationale", ""),
            )
        except (json.JSONDecodeError, BrokenPipeError, OSError):
            return AgentSignal(action="hold", symbol="", rationale="error")

    def on_finish(self):
        if self._proc:
            try:
                self._proc.stdin.close()
                self._proc.wait(timeout=5)
            except (subprocess.TimeoutExpired, OSError):
                self._proc.kill()
            self._proc = None
