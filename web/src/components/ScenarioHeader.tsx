'use client';

interface Props {
  scenario: {
    id: string;
    name: string;
    description: string;
    regime: string;
    symbol: string;
    interval: string;
  };
}

export default function ScenarioHeader({ scenario }: Props) {
  const regimeColors: Record<string, string> = {
    trending: '#00d4aa',
    ranging: '#ffb400',
    volatile: '#ff5050',
  };

  return (
    <div style={{ background: '#111118', borderRadius: 12, padding: 20, border: '1px solid #1e1e2e', marginBottom: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
        <span style={{
          padding: '3px 10px',
          borderRadius: 4,
          background: (regimeColors[scenario.regime] || '#333') + '22',
          color: regimeColors[scenario.regime] || '#999',
          fontSize: 12,
          fontWeight: 600,
        }}>
          {scenario.regime.toUpperCase()}
        </span>
        <span style={{ fontSize: 12, color: '#555' }}>{scenario.symbol} · {scenario.interval}</span>
      </div>
      <h3 style={{ margin: '0 0 4px', fontSize: 16 }}>{scenario.name}</h3>
      <p style={{ margin: 0, fontSize: 13, color: '#777' }}>{scenario.description}</p>
    </div>
  );
}
