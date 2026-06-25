'use client';

import { RadarChart as RC, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts';
import type { ScoreBreakdown } from '@/lib/types';

interface Props {
  breakdown: ScoreBreakdown[];
}

const LABELS: Record<string, string> = {
  total_return: 'Return',
  sharpe_ratio: 'Sharpe',
  max_drawdown: 'Drawdown',
  win_rate: 'Win Rate',
  profit_factor: 'Profit Fac',
};

export default function RadarChartView({ breakdown }: Props) {
  const data = breakdown.map(b => ({
    dimension: LABELS[b.dimension] || b.dimension,
    score: b.normalized,
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <RC data={data}>
        <PolarGrid stroke="#1e1e2e" />
        <PolarAngleAxis dataKey="dimension" tick={{ fill: '#888', fontSize: 11 }} />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#555', fontSize: 10 }} />
        <Radar name="Score" dataKey="score" stroke="#00d4aa" fill="#00d4aa" fillOpacity={0.2} strokeWidth={2} />
      </RC>
    </ResponsiveContainer>
  );
}
