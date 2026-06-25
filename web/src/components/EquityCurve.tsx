'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface Props {
  data: { timestamp: string; equity: number }[];
}

export default function EquityCurve({ data }: Props) {
  if (!data || data.length === 0) {
    return <div style={{ color: '#555', textAlign: 'center', padding: 40 }}>No equity data</div>;
  }

  const initial = data[0]?.equity || 10000;

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data}>
        <CartesianGrid stroke="#1e1e2e" strokeDasharray="3 3" />
        <XAxis dataKey="timestamp" tick={{ fill: '#555', fontSize: 9 }} interval="preserveStartEnd" />
        <YAxis
          domain={['auto', 'auto']}
          tick={{ fill: '#555', fontSize: 10 }}
          tickFormatter={(v: number) => `$${(v/1000).toFixed(1)}k`}
        />
        <Tooltip
          contentStyle={{ background: '#1a1a28', border: '1px solid #333', borderRadius: 6, fontSize: 12 }}
          formatter={(value: number) => [`$${value.toFixed(2)}`, 'Equity']}
        />
        <Line type="monotone" dataKey="equity" stroke="#0088ff" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
