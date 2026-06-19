export type Rating =
  | "Strong Buy / 強烈看多"
  | "Buy / 看多"
  | "Neutral / 中性"
  | "Sell / 看空"
  | "Strong Sell / 強烈看空";

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
  open: number | null;
  high: number | null;
  low: number | null;
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
  score: number;
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
  role?: string;
  stance: Rating;
  message: string;
  content?: string;
  tone: "support" | "risk" | "summary" | "neutral";
  evidenceTags?: string[];
};

export type TargetPrice = {
  currentPrice: number | null;
  baseTargetPrice: number | null;
  bearTargetPrice: number | null;
  bullTargetPrice: number | null;
  impliedUpsidePct: number | null;
  valuationMethod: "RULE_BASED_PE_MULTIPLE" | "INSUFFICIENT_DATA";
  epsBasis: "FORWARD" | "TTM" | "FOUR_QUARTERS" | "SINGLE_QUARTER" | "UNAVAILABLE";
  epsUsed: number | null;
  fairPERatio: number | null;
  bearPERatio: number | null;
  bullPERatio: number | null;
  confidence: number;
  assumptions: string[];
  limitations: string[];
  peSource: "EXTERNAL" | "DERIVED" | "UNAVAILABLE";
};

export type ChipDataGap = {
  code?: string;
  message?: string;
  source?: string;
};

export type ChipDataStatus = "current" | "latest_available" | "missing";
export type ChipDataOverallStatus = ChipDataStatus | "partial";

export type InstitutionalChipData = {
  symbol: string;
  asOfDate: string | null;
  dataDate: string | null;
  status: ChipDataStatus;
  foreignNetBuy: number | null;
  investmentTrustNetBuy: number | null;
  dealerNetBuy: number | null;
  institutionalNetBuyTotal: number | null;
  source: string | null;
  dataGaps: ChipDataGap[];
};

export type MarginChipData = {
  symbol: string;
  asOfDate: string | null;
  dataDate: string | null;
  status: ChipDataStatus;
  marginBalance: number | null;
  marginChange: number | null;
  shortBalance: number | null;
  shortChange: number | null;
  marginUtilizationRate: number | null;
  shortUtilizationRate: number | null;
  source: string | null;
  dataGaps: ChipDataGap[];
};

export type ChipData = {
  overallStatus: ChipDataOverallStatus;
  institutional: InstitutionalChipData | null;
  margin: MarginChipData | null;
  dataGaps: ChipDataGap[];
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
    rating?: Rating;
    supportReasons: string[];
    risks: string[];
    watchPoints: string[];
    recommendationText: string;
    finalScore: number;
    scoreBreakdown: Record<string, number>;
    researchReport?: {
      investmentThesis?: string[];
      keyMetrics?: string[];
      businessQuality?: string[];
      financialAnalysis?: string[];
      valuation?: string[];
      catalysts?: string[];
      risks?: string[];
      variantView?: string[];
      recommendation?: Rating;
      confidenceScore?: number;
      dataGaps?: string[];
      scoreBreakdown?: Record<string, number>;
    };
  };
  sources: Array<{
    name: string;
    status: string;
    message: string;
  }>;
  chipData?: ChipData;
  targetPrice?: TargetPrice;
  reportMarkdown: string;
  disclaimer: string;
};
