'use client';

import { useState, useEffect } from 'react';
import { fetchApi, postApi } from '@/lib/api';
import type { Agent, Scenario, EvalResult, LeaderboardEntry, EvaluationResponse } from '@/lib/types';
import Leaderboard from '@/components/Leaderboard';
import RadarChart from '@/components/RadarChart';
import EquityCurve from '@/components/EquityCurve';
import AgentSummary from '@/components/AgentSummary';
import ScenarioHeader from '@/components/ScenarioHeader';

export default function Home() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [results, setResults] = useState<EvalResult[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<string>('trending');
  const [evalStarted, setEvalStarted] = useState(false);

  useEffect(() => {
    Promise.all([
      fetchApi<{ agents: Agent[] }>('/api/agents'),
      fetchApi<{ scenarios: Scenario[] }>('/api/scenarios'),
    ]).then(([aData, sData]) => {
      setAgents(aData.agents);
      setScenarios(sData.scenarios);
    }).catch(e => setError('Cannot connect to API. Is the backend running on port 8000?'));
  }, []);

  const runEvaluation = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await postApi<EvaluationResponse>('/api/evaluate', {
        agent_ids: agents.map(a => a.agent_id),
        scenario_ids: scenarios.map(s => s.id),
      });
      setResults(data.results);
      setLeaderboard(data.leaderboard);
      setSelectedAgent(data.leaderboard[0]?.agent_id || null);
      setEvalStarted(true);
    } catch (e) {
      setError(`Evaluation failed: ${e}`);
    }
    setLoading(false);
  };

  const agentResults = results.filter(r => r.agent_id === selectedAgent);
  const scenarioResult = agentResults.find(r => r.scenario_id === selectedScenario);
  const allAgentIds = [...new Set(results.map(r => r.agent_id))];
  const scenarioAgents = results.filter(r => r.scenario_id === selectedScenario);

  const regimeLabels: Record<string, string> = {
    trending: 'Trending Bull',
    ranging: 'Sideways Range',
    volatile: 'High Volatility',
  };

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto', padding: '24px 20px' }}>
      {/* Header */}
      <header style={{ marginBottom: 32, borderBottom: '1px solid #1e1e2e', paddingBottom: 16 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0, background: 'linear-gradient(135deg, #00d4aa, #0088ff)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          AgentBench
        </h1>
        <p style={{ color: '#888', margin: '4px 0 0' }}>AI Trading Agent Benchmark Platform</p>
      </header>

      {/* Init state */}
      {!evalStarted && (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <p style={{ color: '#aaa', fontSize: 16, marginBottom: 24 }}>
            {agents.length} agents ready · {scenarios.length} scenarios loaded
          </p>
          <button
            onClick={runEvaluation}
            disabled={loading}
            style={{
              padding: '14px 40px',
              fontSize: 16,
              fontWeight: 600,
              border: 'none',
              borderRadius: 8,
              background: loading ? '#333' : 'linear-gradient(135deg, #00d4aa, #0088ff)',
              color: '#fff',
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Running Evaluation...' : 'Run Benchmark'}
          </button>
          {error && <p style={{ color: '#ff5555', marginTop: 16 }}>{error}</p>}
        </div>
      )}

      {/* Error */}
      {error && evalStarted && <p style={{ color: '#ff5555' }}>{error}</p>}

      {/* Results */}
      {evalStarted && leaderboard.length > 0 && (
        <>
          {/* Leaderboard */}
          <Leaderboard entries={leaderboard} selectedAgent={selectedAgent} onSelect={setSelectedAgent} />

          {/* Scenario tabs */}
          <div style={{ display: 'flex', gap: 8, margin: '24px 0' }}>
            {scenarios.map(s => (
              <button
                key={s.id}
                onClick={() => setSelectedScenario(s.id)}
                style={{
                  padding: '8px 20px',
                  borderRadius: 6,
                  border: '1px solid',
                  borderColor: selectedScenario === s.id ? '#00d4aa' : '#2a2a3a',
                  background: selectedScenario === s.id ? 'rgba(0,212,170,0.12)' : 'transparent',
                  color: selectedScenario === s.id ? '#00d4aa' : '#999',
                  cursor: 'pointer',
                  fontSize: 14,
                  fontWeight: 500,
                }}
              >
                {regimeLabels[s.regime] || s.name}
              </button>
            ))}
          </div>

          {/* Agent detail for selected scenario */}
          {scenarioResult && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
              {/* Radar chart */}
              <div style={{ background: '#111118', borderRadius: 12, padding: 20, border: '1px solid #1e1e2e' }}>
                <h3 style={{ margin: '0 0 16px', fontSize: 15, color: '#ccc' }}>
                  {scenarioResult.agent_name} — {scenarioResult.scenario_name}
                </h3>
                <RadarChart breakdown={scenarioResult.breakdown} />
              </div>

              {/* Equity curve */}
              <div style={{ background: '#111118', borderRadius: 12, padding: 20, border: '1px solid #1e1e2e' }}>
                <h3 style={{ margin: '0 0 16px', fontSize: 15, color: '#ccc' }}>Equity Curve</h3>
                <EquityCurve data={scenarioResult.equity_curve} />
              </div>
            </div>
          )}

          {/* Scenario comparison table */}
          <div style={{ background: '#111118', borderRadius: 12, padding: 20, border: '1px solid #1e1e2e', marginBottom: 24, overflow: 'auto' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 15, color: '#ccc' }}>
              Scenario: {scenarios.find(s => s.id === selectedScenario)?.name}
            </h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #1e1e2e' }}>
                  <th style={{ textAlign: 'left', padding: '8px 12px', color: '#888' }}>Agent</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', color: '#888' }}>Score</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', color: '#888' }}>Return</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', color: '#888' }}>Sharpe</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', color: '#888' }}>Max DD</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', color: '#888' }}>Win Rate</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', color: '#888' }}>Profit Factor</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', color: '#888' }}>Trades</th>
                </tr>
              </thead>
              <tbody>
                {scenarioAgents
                  .sort((a, b) => b.metrics.composite_score - a.metrics.composite_score)
                  .map(r => (
                    <tr
                      key={r.agent_id}
                      onClick={() => setSelectedAgent(r.agent_id)}
                      style={{
                        borderBottom: '1px solid #1a1a28',
                        background: r.agent_id === selectedAgent ? 'rgba(0,212,170,0.06)' : 'transparent',
                        cursor: 'pointer',
                      }}
                    >
                      <td style={{ padding: '10px 12px', fontWeight: 500 }}>{r.agent_name}</td>
                      <td style={{ textAlign: 'right', padding: '10px 12px' }}>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: 4,
                          background: r.metrics.composite_score > 70 ? 'rgba(0,212,170,0.2)' : r.metrics.composite_score > 50 ? 'rgba(255,180,0,0.2)' : 'rgba(255,80,80,0.2)',
                          color: r.metrics.composite_score > 70 ? '#00d4aa' : r.metrics.composite_score > 50 ? '#ffb400' : '#ff5050',
                          fontWeight: 600,
                        }}>
                          {r.metrics.composite_score.toFixed(0)}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right', padding: '10px 12px', color: r.metrics.total_return >= 0 ? '#00d4aa' : '#ff5050' }}>
                        {(r.metrics.total_return * 100).toFixed(2)}%
                      </td>
                      <td style={{ textAlign: 'right', padding: '10px 12px' }}>{r.metrics.sharpe_ratio.toFixed(2)}</td>
                      <td style={{ textAlign: 'right', padding: '10px 12px', color: '#ff5050' }}>{(r.metrics.max_drawdown * 100).toFixed(1)}%</td>
                      <td style={{ textAlign: 'right', padding: '10px 12px' }}>{(r.metrics.win_rate * 100).toFixed(1)}%</td>
                      <td style={{ textAlign: 'right', padding: '10px 12px' }}>{r.metrics.profit_factor.toFixed(2)}</td>
                      <td style={{ textAlign: 'right', padding: '10px 12px', color: '#888' }}>{r.trade_count}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>

          {/* AI Summary */}
          <AgentSummary
            agentName={scenarioResult?.agent_name || ''}
            scenarioName={scenarioResult?.scenario_name || ''}
            metrics={scenarioResult?.metrics}
            breakdown={scenarioResult?.breakdown || []}
            scenarioAgents={scenarioAgents}
          />

          {/* Rerun */}
          <div style={{ textAlign: 'center', margin: '40px 0' }}>
            <button
              onClick={runEvaluation}
              disabled={loading}
              style={{
                padding: '10px 28px',
                fontSize: 14,
                fontWeight: 500,
                border: '1px solid #333',
                borderRadius: 6,
                background: 'transparent',
                color: '#aaa',
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? 'Running...' : 'Re-run Evaluation'}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
