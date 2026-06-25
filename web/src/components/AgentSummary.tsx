'use client';

import type { Metrics, ScoreBreakdown, EvalResult } from '@/lib/types';

interface Props {
  agentName: string;
  scenarioName: string;
  metrics?: Metrics;
  breakdown: ScoreBreakdown[];
  scenarioAgents: EvalResult[];
}

function generateSummary(agentName: string, scenarioName: string, metrics?: Metrics, scenarioAgents?: EvalResult[]): string {
  if (!metrics) return 'No data available yet.';

  const lines: string[] = [];
  const ret = metrics.total_return * 100;

  lines.push(`${agentName} achieved ${ret >= 0 ? 'a' : 'a'} ${ret >= 0 ? '+' : ''}${ret.toFixed(2)}% return in ${scenarioName}`);

  if (metrics.sharpe_ratio > 1.5) {
    lines.push(`with a strong Sharpe ratio of ${metrics.sharpe_ratio.toFixed(2)}, indicating excellent risk-adjusted performance.`);
  } else if (metrics.sharpe_ratio > 0.5) {
    lines.push(`with a moderate Sharpe ratio of ${metrics.sharpe_ratio.toFixed(2)}, suggesting acceptable risk-adjusted returns.`);
  } else {
    lines.push(`with a weak Sharpe ratio of ${metrics.sharpe_ratio.toFixed(2)}, meaning returns came with high risk.`);
  }

  const dd = metrics.max_drawdown * 100;
  if (dd < 10) {
    lines.push(`Maximum drawdown was tightly controlled at -${dd.toFixed(1)}%`);
  } else if (dd < 20) {
    lines.push(`Maximum drawdown was -${dd.toFixed(1)}%, within acceptable range.`);
  } else {
    lines.push(`Maximum drawdown of -${dd.toFixed(1)}% signals significant risk exposure.`);
  }

  if (metrics.win_rate > 0.6) {
    lines.push(`Win rate of ${(metrics.win_rate*100).toFixed(1)}% demonstrates consistent decision-making.`);
  } else {
    lines.push(`Win rate of ${(metrics.win_rate*100).toFixed(1)}%${metrics.win_rate < 0.5 ? ' suggests room for entry-precision improvement.' : ' is near the efficiency threshold.'}`);
  }

  const tradeCount = scenarioAgents?.map(a => a.trade_count) || [];

  // Peer comparison
  if (scenarioAgents && scenarioAgents.length > 1) {
    const sorted = [...scenarioAgents].sort((a, b) => b.metrics.composite_score - a.metrics.composite_score);
    const rank = sorted.findIndex(a => a.agent_name === agentName) + 1;
    if (rank === 1) {
      lines.push(`This agent ranked #1 among ${sorted.length} agents in this scenario.`);
    } else {
      const best = sorted[0];
      lines.push(`Ranked #${rank}/${sorted.length}. To improve, consider ${best.agent_name}'s approach which delivered a ${best.metrics.composite_score.toFixed(0)} composite score.`);
    }
  }

  return lines.join(' ');
}

export default function AgentSummary({ agentName, scenarioName, metrics, breakdown, scenarioAgents }: Props) {
  const summary = generateSummary(agentName, scenarioName, metrics, scenarioAgents);

  return (
    <div style={{ background: '#111118', borderRadius: 12, padding: 20, border: '1px solid #1e1e2e', marginBottom: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <span style={{ fontSize: 13, color: '#666' }}>AI</span>
        <h3 style={{ margin: 0, fontSize: 15, color: '#ccc' }}>Evaluation Summary</h3>
      </div>
      <p style={{ margin: 0, fontSize: 14, lineHeight: 1.7, color: '#bbb' }}>{summary}</p>

      {/* Dimension details */}
      <div style={{ marginTop: 16, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        {breakdown.map(b => (
          <div key={b.dimension} style={{
            flex: '1 1 140px',
            padding: '10px 14px',
            borderRadius: 6,
            background: '#0d0d15',
            border: '1px solid #1a1a28',
            minWidth: 130,
          }}>
            <div style={{ fontSize: 11, color: '#666', marginBottom: 4 }}>{b.dimension.replace('_', ' ')}</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: b.normalized > 70 ? '#00d4aa' : b.normalized > 50 ? '#ffb400' : '#ff5050' }}>
              {b.normalized.toFixed(0)}
            </div>
            <div style={{ fontSize: 11, color: '#555' }}>{b.interpretation}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
