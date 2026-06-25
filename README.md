# AgentBench

AI Trading Agent Benchmark Platform — objectively evaluate AI trading agents through standardized scenario replay and multi-dimensional scoring.

## Overview

AgentBench runs trading agents against curated market scenarios (trending, ranging, volatile) and produces:
- **5-dimension performance scores** (Return, Sharpe, Max Drawdown, Win Rate, Profit Factor)
- **Visual leaderboard** with cross-scenario ranking
- **AI-generated evaluation summaries** highlighting strengths and weaknesses
- **Reproducible evidence** — every evaluation is deterministic and re-runnable

## Quick Start

### Docker

```bash
docker compose up
# API: http://localhost:8000
# Web: http://localhost:3000
```

### Local

```bash
# Terminal 1: API
cd api && pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Web
cd web && npm install && npm run dev
```

### CLI (no UI)

```bash
cd engine && python cli.py
# Outputs evaluation_results.json
```

## Architecture

```
api/         FastAPI REST server — evaluation endpoints
engine/      Core Python engine — scenario replay, scoring, agent protocol
  engine/      Library modules
  scenarios/   Standardized evaluation scenarios (JSON + CSV)
web/         Next.js dashboard — leaderboard, radar chart, equity curve, AI summary
agents/      Example agents (MA trend, RSI reversion, random baseline)
```

## Agent Protocol

Agents implement a simple bar-by-bar interface. See `engine/engine/agent.py` for the `BaseAgent` class. Built-in agents are in `engine/engine/builtin_agents.py`.

## Built-in Agents

| Agent | Strategy | Best For |
|-------|----------|----------|
| MA Crossover | 20/50 SMA golden/death cross | Trend following |
| RSI Reversion | RSI(14) oversold/overbought | Mean reversion |
| Random Baseline | Random entries/exits | Noise floor comparison |

## Scenarios

| Scenario | Regime | Symbol | Tests |
|----------|--------|--------|-------|
| Trending Bull Market | trending | BTC/USDT | Trend capture, patience |
| Sideways Consolidation | ranging | ETH/USDT | Entry timing, false breakout avoidance |
| High Volatility Crash/Recovery | volatile | BTC/USDT | Risk management, stop-loss discipline |

## Scoring

Each agent is scored 0-100 on composite, composed of 5 weighted dimensions:
- Total Return (25%)
- Sharpe Ratio (20%)
- Max Drawdown (20%)
- Win Rate (15%)
- Profit Factor (20%)

Weights are configurable per scenario via `scoring_weights` in the scenario JSON.

## License

MIT
