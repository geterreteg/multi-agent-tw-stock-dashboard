from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


Rating = Literal["Strong Buy / 強烈看多", "Buy / 看多", "Neutral / 中性", "Sell / 看空", "Strong Sell / 強烈看空"]


class AnalyzeRequest(BaseModel):
    symbol: str = Field(..., min_length=4, max_length=6)
    period: str = "6mo"


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class MetricSnapshot(BaseModel):
    latestClose: Optional[float] = None
    return20d: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    peRatio: Optional[float] = None
    eps: Optional[float] = None
    revenueGrowth: Optional[float] = None
    foreignBuy: Optional[int] = None


class PricePoint(BaseModel):
    date: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None


class VolumePoint(BaseModel):
    date: str
    volume: Optional[int] = None


class MovingAveragePoint(BaseModel):
    date: str
    ma20: Optional[float] = None
    ma60: Optional[float] = None


class ChartBundle(BaseModel):
    price: list[PricePoint]
    volume: list[VolumePoint]
    movingAverage: list[MovingAveragePoint]


class AgentInsight(BaseModel):
    name: str
    role: str
    stance: Rating
    score: float = Field(..., ge=-2, le=2)
    confidence: float = Field(..., ge=0, le=1)
    summary: str
    narrative: str
    evidence: list[str]
    degraded: bool = False
    reasons: list[str]
    risks: list[str]


class DebateMessage(BaseModel):
    speaker: str
    role: str = ""
    stance: Rating
    message: str
    content: str = ""
    tone: Literal["support", "risk", "summary", "neutral"]
    evidenceTags: list[str] = Field(default_factory=list)


class TargetPrice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    currentPrice: Optional[int] = None
    baseTargetPrice: Optional[int] = None
    bearTargetPrice: Optional[int] = None
    bullTargetPrice: Optional[int] = None
    impliedUpsidePct: Optional[float] = None
    valuationMethod: Literal["RULE_BASED_PE_MULTIPLE", "INSUFFICIENT_DATA"] = "INSUFFICIENT_DATA"
    epsBasis: Literal["FORWARD", "TTM", "TTM_EPS", "FOUR_QUARTERS", "SINGLE_QUARTER", "UNAVAILABLE"] = "UNAVAILABLE"
    epsUsed: Optional[float] = None
    fairPERatio: Optional[float] = None
    bearPERatio: Optional[float] = None
    bullPERatio: Optional[float] = None
    confidence: int = Field(default=0, ge=0, le=65)
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=lambda: ["資料不足，暫不產生規則式估值區間。"])
    peSource: Literal["HISTORICAL_TWSE", "EXTERNAL", "DERIVED", "UNAVAILABLE"] = "UNAVAILABLE"


class HistoricalPE(BaseModel):
    model_config = ConfigDict(extra="forbid")

    minPE: Optional[float] = None
    p25PE: Optional[float] = None
    medianPE: Optional[float] = None
    p75PE: Optional[float] = None
    maxPE: Optional[float] = None
    validSampleCount: int = 0
    source: str = "TWSE 個股日本益比、殖利率及股價淨值比"
    cacheStatus: Literal["live", "cache", "missing"] = "missing"
    dataLimitations: list[str] = Field(default_factory=list)


class EquityResearchReport(BaseModel):
    investmentThesis: list[str]
    keyMetrics: list[str]
    businessQuality: list[str]
    financialAnalysis: list[str]
    valuation: list[str]
    catalysts: list[str]
    risks: list[str]
    variantView: list[str]
    recommendation: Rating
    confidenceScore: int = Field(..., ge=0, le=100)
    dataGaps: list[str]
    scoreBreakdown: dict[str, float]


class DecisionSummary(BaseModel):
    rating: Rating
    supportReasons: list[str]
    risks: list[str]
    watchPoints: list[str]
    recommendationText: str
    finalScore: float
    scoreBreakdown: dict[str, float]
    researchReport: EquityResearchReport


class DataSourceStatus(BaseModel):
    name: str
    status: Literal["ok", "degraded", "failed", "planned"]
    message: str


class ChipDataGap(BaseModel):
    code: str
    message: str


class InstitutionalData(BaseModel):
    symbol: str = ""
    asOfDate: Optional[str] = None
    dataDate: Optional[str] = None
    status: Literal["current", "latest_available", "missing"] = "missing"
    foreignNetBuy: Optional[int] = None
    investmentTrustNetBuy: Optional[int] = None
    dealerNetBuy: Optional[int] = None
    institutionalNetBuyTotal: Optional[int] = None
    source: str = "官方三大法人資料"
    dataGaps: list[ChipDataGap] = Field(default_factory=list)


class MarginData(BaseModel):
    symbol: str = ""
    asOfDate: Optional[str] = None
    dataDate: Optional[str] = None
    status: Literal["current", "latest_available", "missing"] = "missing"
    marginBalance: Optional[int] = None
    marginChange: Optional[int] = None
    shortBalance: Optional[int] = None
    shortChange: Optional[int] = None
    marginUtilizationRate: Optional[float] = None
    shortUtilizationRate: Optional[float] = None
    source: str = "官方融資融券資料"
    dataGaps: list[ChipDataGap] = Field(default_factory=list)


class ChipData(BaseModel):
    overallStatus: Literal["current", "latest_available", "partial", "missing"] = "missing"
    institutional: InstitutionalData = Field(default_factory=InstitutionalData)
    margin: MarginData = Field(default_factory=MarginData)
    dataGaps: list[ChipDataGap] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    name: str
    period: str
    rating: Rating
    lastUpdated: str
    metrics: MetricSnapshot
    charts: ChartBundle
    agents: list[AgentInsight]
    debate: list[DebateMessage] = Field(default_factory=list)
    decision: DecisionSummary
    sources: list[DataSourceStatus]
    chipData: ChipData = Field(default_factory=ChipData)
    targetPrice: TargetPrice = Field(default_factory=TargetPrice)
    historicalPE: HistoricalPE = Field(default_factory=HistoricalPE)
    reportMarkdown: str
    disclaimer: str
