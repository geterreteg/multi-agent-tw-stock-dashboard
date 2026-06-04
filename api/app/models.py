from typing import Literal, Optional

from pydantic import BaseModel, Field


Rating = Literal["偏多", "中立", "偏空"]


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
    confidence: float = Field(..., ge=0, le=1)
    summary: str
    narrative: str
    evidence: list[str]
    degraded: bool = False
    reasons: list[str]
    risks: list[str]


class DebateMessage(BaseModel):
    speaker: str
    stance: Rating
    message: str
    tone: Literal["support", "risk", "summary", "neutral"]


class DecisionSummary(BaseModel):
    supportReasons: list[str]
    risks: list[str]
    watchPoints: list[str]
    recommendationText: str


class DataSourceStatus(BaseModel):
    name: str
    status: Literal["ok", "degraded", "failed", "planned"]
    message: str


class AnalyzeResponse(BaseModel):
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
    reportMarkdown: str
    disclaimer: str
