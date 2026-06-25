"""
AgentBench REST API — FastAPI server exposing evaluation endpoints.
"""

import json
import sys
from pathlib import Path

# Ensure engine is importable from this directory
sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine.scenario import load_scenario
from engine.runner import Runner
from engine.builtin_agents import BUILTIN_AGENTS

app = FastAPI(title="AgentBench API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCENARIOS_DIR = Path(__file__).parent.parent / "engine" / "scenarios"
SCENARIO_IDS = ["trending", "ranging", "volatile"]


class EvalRequest(BaseModel):
    agent_ids: list[str] | None = None
    scenario_ids: list[str] | None = None


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/scenarios")
async def list_scenarios():
    scenarios = []
    for sid in SCENARIO_IDS:
        try:
            s = load_scenario(sid, SCENARIOS_DIR)
            scenarios.append(s.to_dict())
        except Exception as e:
            scenarios.append({"id": sid, "error": str(e)})
    return {"scenarios": scenarios}


@app.get("/api/agents")
async def list_agents():
    return {
        "agents": [a.to_dict() for a in BUILTIN_AGENTS.values()]
    }


@app.post("/api/evaluate")
async def run_evaluation(req: EvalRequest):
    agent_ids = req.agent_ids or list(BUILTIN_AGENTS.keys())
    scenario_ids = req.scenario_ids or SCENARIO_IDS

    agents = []
    for aid in agent_ids:
        if aid in BUILTIN_AGENTS:
            agents.append(BUILTIN_AGENTS[aid])
        else:
            raise HTTPException(status_code=404, detail=f"Agent '{aid}' not found")

    results = []
    for sid in scenario_ids:
        try:
            scenario = load_scenario(sid, SCENARIOS_DIR)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Scenario '{sid}' not found: {e}")

        for agent in agents:
            runner = Runner(scenario, agent)
            result = runner.run()

            # Re-score with peer comparison
            all_for_scenario = [
                r for r in results if r.scenario_id == sid
            ]
            all_for_scenario.append(result)

            results.append(result)

    # Build leaderboard
    leaderboard = {}
    for r in results:
        if r.agent_id not in leaderboard:
            leaderboard[r.agent_id] = {
                "agent_id": r.agent_id,
                "agent_name": r.agent_name,
                "scores": {},
                "avg_score": 0,
            }
        leaderboard[r.agent_id]["scores"][r.scenario_id] = round(r.composite_score, 1)
    for entry in leaderboard.values():
        if entry["scores"]:
            entry["avg_score"] = round(sum(entry["scores"].values()) / len(entry["scores"]), 1)
    ranked = sorted(leaderboard.values(), key=lambda x: x["avg_score"], reverse=True)
    for i, entry in enumerate(ranked):
        entry["rank"] = i + 1

    return {
        "results": [r.to_dict() for r in results],
        "leaderboard": ranked,
    }


@app.get("/api/evaluate/{agent_id}/{scenario_id}")
async def run_single(agent_id: str, scenario_id: str):
    if agent_id not in BUILTIN_AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    if scenario_id not in SCENARIO_IDS:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")

    agent = BUILTIN_AGENTS[agent_id]
    scenario = load_scenario(scenario_id, SCENARIOS_DIR)
    runner = Runner(scenario, agent)
    result = runner.run()
    return {"result": result.to_dict()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
