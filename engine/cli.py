"""
AgentBench CLI — run evaluations from the command line.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine.scenario import load_scenario
from engine.runner import Runner
from engine.builtin_agents import BUILTIN_AGENTS


def main():
    scenarios_dir = Path(__file__).parent / "scenarios"

    scenarios = {
        "trending": load_scenario("trending", scenarios_dir),
        "ranging": load_scenario("ranging", scenarios_dir),
        "volatile": load_scenario("volatile", scenarios_dir),
    }

    agents = list(BUILTIN_AGENTS.values())

    all_results = []

    for scenario in scenarios.values():
        for agent in agents:
            print(f"\n{'='*60}")
            print(f"Agent: {agent.name}  |  Scenario: {scenario.name}")
            print(f"{'='*60}")
            runner = Runner(scenario, agent)
            result = runner.run()
            all_results.append(result)

            print(f"  Return:     {result.total_return*100:+.2f}%")
            print(f"  Sharpe:     {result.sharpe_ratio:.2f}")
            print(f"  Max DD:     {result.max_drawdown*100:.2f}%")
            print(f"  Win Rate:   {result.win_rate*100:.1f}%")
            print(f"  Profit Fac: {result.profit_factor:.2f}")
            print(f"  Trades:     {len(result.trades)}")
            print(f"  Score:      {result.composite_score:.0f}/100")

    # Output full results as JSON
    output = {
        "results": [r.to_dict() for r in all_results],
        "summary": generate_leaderboard(all_results, scenarios, agents),
    }

    out_path = Path(__file__).parent / "evaluation_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nFull results written to {out_path}")


def generate_leaderboard(results, scenarios, agents):
    from engine.scoring import score_trades

    leaderboard = []
    for agent in agents:
        agent_results = [r for r in results if r.agent_id == agent.agent_id]
        if agent_results:
            # Re-score with peer comparison
            for r in agent_results:
                r2 = type(r)(
                    agent_id=r.agent_id, agent_name=r.agent_name,
                    scenario_id=r.scenario_id, scenario_name=r.scenario_name,
                    total_return=r.total_return, sharpe_ratio=r.sharpe_ratio,
                    max_drawdown=r.max_drawdown, win_rate=r.win_rate,
                    profit_factor=r.profit_factor,
                    composite_score=r.composite_score,
                    breakdown=r.breakdown, trades=r.trades,
                    equity_curve=r.equity_curve,
                )
            avg_score = sum(r.composite_score for r in agent_results) / len(agent_results)
            leaderboard.append({
                "agent_id": agent.agent_id,
                "agent_name": agent.name,
                "avg_score": round(avg_score, 1),
                "scenarios": {r.scenario_id: round(r.composite_score, 1) for r in agent_results},
            })

    leaderboard.sort(key=lambda x: x["avg_score"], reverse=True)
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1
    return leaderboard


if __name__ == "__main__":
    main()
