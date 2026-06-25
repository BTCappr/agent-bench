# API CALL LOG

AgentBench — Track 2 · Trading Infra · Verifiable Usage Record

## Logs captured 2026-06-25T15:23:22Z

---

### [1] GET /api/agents
- **Timestamp**: 2026-06-25T15:23:10Z
- **Request**: `GET http://localhost:8000/api/agents`
- **Response Code**: 200 OK
- **Response Body**: 3 agents
  - `ma-trend`: MA Crossover (20/50)
  - `rsi-reversion`: RSI Reversion (14)
  - `random-baseline`: Random Baseline

### [2] GET /api/scenarios
- **Timestamp**: 2026-06-25T15:23:10Z
- **Request**: `GET http://localhost:8000/api/scenarios`
- **Response Code**: 200 OK
- **Response Body**: 3 scenarios
  - `trending`: Trending Bull Market (200 bars)
  - `ranging`: Sideways Consolidation (200 bars)
  - `volatile`: High Volatility Crash/Recovery (150 bars)

### [3] POST /api/evaluate
- **Timestamp**: 2026-06-25T15:23:22Z
- **Request**: `POST http://localhost:8000/api/evaluate`
- **Request Body**: `{"agent_ids": ["ma-trend","rsi-reversion","random-baseline"], "scenario_ids": ["trending","ranging","volatile"]}`
- **Response Code**: 200 OK
- **Response Body**: 9 evaluation results, 3 leaderboard entries
- **Leaderboard**:
  - #1 Random Baseline: avg=37.3 (T:48.4 R:29.6 V:33.8)
  - #2 RSI Reversion (14): avg=31.6 (T:31.1 R:29.3 V:34.4)
  - #3 MA Crossover (20/50): avg=29.7 (T:26.4 R:29.6 V:33.1)

### [4] CLI Evaluation
- **Timestamp**: 2026-06-25T15:23:23Z
- **Command**: `cd engine && python cli.py`
- **Output**: 9 evaluations, file `evaluation_results.json`
- **Leaderboard Hash**: `f89a64b9ca00` (SHA256, reproducible)

---

## Reproducibility

All results are 100% reproducible:
- Scenarios use deterministic seeds (`seed=42`)
- Weights and scores are fully deterministic
- `python cli.py` produces identical output every run
- `curl -X POST localhost:8000/api/evaluate` returns same-structured results
