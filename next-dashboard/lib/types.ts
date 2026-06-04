export type Rating = "偏多" | "中立" | "偏空";

export type MetricSnapshot = {
  latestClose: number | null;
  return20d: number | null;
  ma20: number | null;
  ma60: number | null;
  peRatio: number | null;
  eps: number | null;
  revenueGrowth: number | null;
  foreignBuy: number | null;
};

export type PricePoint = {
  date: string;
  close: number | null;
};

export type VolumePoint = {
  date: string;
  volume: number | null;
};

export type MovingAveragePoint = {
  date: string;
  ma20: number | null;
  ma60: number | null;
};

export type AgentInsight = {
  name: string;
  role: string;
  stance: Rating;
  confidence: number;
  summary: string;
  narrative: string;
  evidence: string[];
  degraded: boolean;
  reasons: string[];
  risks: string[];
};

export type DebateMessage = {
  speaker: string;
  stance: Rating;
  message: string;
  tone: "support" | "risk" | "summary" | "neutral";
};

export type AnalyzeResponse = {
  symbol: string;
  name: string;
  period: string;
  rating: Rating;
  lastUpdated: string;
  metrics: MetricSnapshot;
  charts: {
    price: PricePoint[];
    volume: VolumePoint[];
    movingAverage: MovingAveragePoint[];
  };
  agents: AgentInsight[];
  debate: DebateMessage[];
  decision: {
    supportReasons: string[];
    risks: string[];
    watchPoints: string[];
    recommendationText: string;
  };
  sources: Array<{
    name: string;
    status: string;
    message: string;
  }>;
  reportMarkdown: string;
  disclaimer: string;
};
