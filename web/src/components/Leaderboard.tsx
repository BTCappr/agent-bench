'use client';

import type { LeaderboardEntry } from '@/lib/types';

interface Props {
  entries: LeaderboardEntry[];
  selectedAgent: string | null;
  onSelect: (id: string) => void;
}

export default function Leaderboard({ entries, selectedAgent, onSelect }: Props) {
  return (
    <div style={{ background: '#111118', borderRadius: 12, padding: 20, border: '1px solid #1e1e2e' }}>
      <h2 style={{ margin: '0 0 16px', fontSize: 18, color: '#ccc' }}>Leaderboard</h2>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        {entries.map(entry => (
          <div
            key={entry.agent_id}
            onClick={() => onSelect(entry.agent_id)}
            style={{
              flex: '1 1 200px',
              padding: '16px',
              borderRadius: 8,
              border: '1px solid',
              borderColor: entry.agent_id === selectedAgent ? '#00d4aa' : '#1e1e2e',
              background: entry.agent_id === selectedAgent ? 'rgba(0,212,170,0.08)' : '#0d0d15',
              cursor: 'pointer',
              minWidth: 180,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <span style={{ fontSize: 12, color: '#666' }}>#{entry.rank}</span>
              <span style={{
                fontSize: 13,
                fontWeight: 700,
                color: entry.avg_score > 70 ? '#00d4aa' : entry.avg_score > 50 ? '#ffb400' : '#ff5050',
              }}>
                {entry.avg_score.toFixed(0)}
              </span>
            </div>
            <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 8 }}>{entry.agent_name}</div>
            <div style={{ fontSize: 11, color: '#555' }}>
              {Object.entries(entry.scores).map(([sid, score]) => (
                <span key={sid} style={{ marginRight: 8 }}>
                  {sid}: <span style={{ color: score > 70 ? '#00d4aa' : score > 50 ? '#ffb400' : '#ff5050' }}>{score}</span>
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
