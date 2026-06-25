export interface Agent {
  agent_id: string;
  name: string;
  description: string;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
  regime: string;
  symbol: string;
  interval: string;
  bar_count: number;
  date_range?: string;
}

export interface ScoreBreakdown {
  dimension: string;
  raw_value: number;
  normalized: number;
  weight: number;
  weighted: number;
  interpretation: string;
}

export interface Metrics {
  total_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  profit_factor: number;
  composite_score: number;
}

export interface EvalResult {
  agent_id: string;
  agent_name: string;
  scenario_id: string;
  scenario_name: string;
  metrics: Metrics;
  breakdown: ScoreBreakdown[];
  trade_count: number;
  trades: unknown[];
  equity_curve: { timestamp: string; equity: number }[];
  summary: string;
  rank: number;
}

export interface LeaderboardEntry {
  agent_id: string;
  agent_name: string;
  scores: Record<string, number>;
  avg_score: number;
  rank: number;
}

export interface EvaluationResponse {
  results: EvalResult[];
  leaderboard: LeaderboardEntry[];
}
