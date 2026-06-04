from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import pandas as pd

from app.models import (
    AgentInsight,
    AnalyzeResponse,
    ChartBundle,
    DataSourceStatus,
    DecisionSummary,
    MetricSnapshot,
    MovingAveragePoint,
    PricePoint,
    VolumePoint,
)
from app.services.market_data import (
    SourceStatus,
    fetch_finmind_bundle,
    fetch_yfinance_bundle,
    get_finmind_token,
    normalize_symbol,
    safe_float,
    safe_int,
)
from app.services.agents import run_agents
from app.services.reports import generate_markdown_report


DISCLAIMER = "本系統分析結果僅供學術研究與投資參考，不構成任何買賣建議。投資人仍應自行評估風險並承擔投資結果。"
DATA_DELAY_NOTE = "資料可能延遲或不完整，本系統不宣稱資料完全即時。"


@dataclass
class StockContext:
    stock_id: str
    stock_name: str
    industry: str
    last_updated: str
    price_history: pd.DataFrame = field(default_factory=pd.DataFrame)
    latest_close: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    return_20d: Optional[float] = None
    average_volume: Optional[float] = None
    revenue_growth: Optional[float] = None
    latest_revenue: Optional[float] = None
    eps: Optional[float] = None
    pe_ratio: Optional[float] = None
    foreign_buy: Optional[float] = None
    institutional_net_buy: Optional[float] = None
    margin_balance_change: Optional[float] = None
    short_balance_change: Optional[float] = None
    dividend_summary: str = "股利資料暫無"
    source_status: list[SourceStatus] = field(default_factory=list)
    finmind_errors: list[str] = field(default_factory=list)
    finmind_token_mode: str = ""


def build_context(symbol: str, period: str = "6mo") -> StockContext:
    stock_id = normalize_symbol(symbol)
    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    token, token_mode = get_finmind_token()
    history, metrics, y_status = fetch_yfinance_bundle(stock_id, period)
    finmind = fetch_finmind_bundle(stock_id, token, token_mode)

    return StockContext(
        stock_id=stock_id,
        stock_name=str(finmind["stock_name"]),
        industry=str(finmind["industry"]),
        last_updated=last_updated,
        price_history=history,
        latest_close=safe_float(metrics["latest_close"]),
        ma20=safe_float(metrics["ma20"]),
        ma60=safe_float(metrics["ma60"]),
        return_20d=safe_float(metrics["return_20d"]),
        average_volume=safe_float(metrics["average_volume"]),
        latest_revenue=safe_float(finmind["latest_revenue"]),
        revenue_growth=safe_float(finmind["revenue_growth"]),
        eps=safe_float(finmind["eps"]),
        pe_ratio=safe_float(finmind["pe_ratio"]),
        foreign_buy=safe_float(finmind["foreign_buy"]),
        institutional_net_buy=safe_float(finmind["institutional_net_buy"]),
        margin_balance_change=safe_float(finmind["margin_balance_change"]),
        short_balance_change=safe_float(finmind["short_balance_change"]),
        dividend_summary=str(finmind["dividend_summary"]),
        source_status=[y_status, finmind["status"]],
        finmind_errors=list(finmind["errors"]),
        finmind_token_mode=token_mode,
    )


def analyze_symbol(symbol: str, period: str) -> AnalyzeResponse:
    try:
        context = build_context(symbol, period)
    except Exception as exc:
        return build_failed_response(symbol, period, f"資料服務發生未預期錯誤：{type(exc).__name__}")

    agents, debate, decision, rating = run_agents(context)
    report = generate_markdown_report(context, agents, rating, decision, debate)

    return AnalyzeResponse(
        symbol=context.stock_id,
        name=context.stock_name,
        period=period,
        rating=rating,
        lastUpdated=context.last_updated,
        metrics=MetricSnapshot(
            latestClose=context.latest_close,
            return20d=context.return_20d,
            ma20=context.ma20,
            ma60=context.ma60,
            peRatio=context.pe_ratio,
            eps=context.eps,
            revenueGrowth=context.revenue_growth,
            foreignBuy=safe_int(context.foreign_buy),
        ),
        charts=build_chart_bundle(context.price_history),
        agents=agents,
        debate=debate,
        decision=decision,
        sources=[source_to_api_status(status) for status in context.source_status],
        reportMarkdown=report,
        disclaimer=DISCLAIMER,
    )


def build_chart_bundle(history: pd.DataFrame) -> ChartBundle:
    if history.empty or "Close" not in history.columns:
        return ChartBundle(price=[], volume=[], movingAverage=[])

    work = history.copy().reset_index()
    date_col = work.columns[0]
    dates = work[date_col].map(to_date_string)
    close = pd.to_numeric(work["Close"], errors="coerce")
    volume = pd.to_numeric(work.get("Volume", pd.Series(dtype=float)), errors="coerce")
    ma20 = close.rolling(20).mean()
    ma60 = close.rolling(60).mean()

    price = [PricePoint(date=date, close=safe_float(value)) for date, value in zip(dates, close)]
    volume_points = [VolumePoint(date=date, volume=safe_int(value)) for date, value in zip(dates, volume)]
    moving_average = [
        MovingAveragePoint(date=date, ma20=safe_float(ma20_value), ma60=safe_float(ma60_value))
        for date, ma20_value, ma60_value in zip(dates, ma20, ma60)
    ]
    return ChartBundle(price=price, volume=volume_points, movingAverage=moving_average)


def to_date_string(value) -> str:
    if hasattr(value, "date"):
        return value.date().isoformat()
    return str(value)[:10]


def source_to_api_status(status: SourceStatus) -> DataSourceStatus:
    return DataSourceStatus(
        name=status.name,
        status="ok" if status.ok else "degraded",
        message=status.message,
    )


def build_failed_response(symbol: str, period: str, message: str) -> AnalyzeResponse:
    normalized = symbol.strip() or "UNKNOWN"
    decision = DecisionSummary(
        supportReasons=["目前無法形成有效支持理由。"],
        risks=[message],
        watchPoints=["請稍後重試，或檢查資料來源與網路狀態。"],
        recommendationText="資料服務發生錯誤，目前僅能採中立觀察；請稍後重試，或檢查資料來源與網路狀態。",
        finalScore=0,
        scoreBreakdown={},
    )
    return AnalyzeResponse(
        symbol=normalized,
        name=f"{normalized}.TW",
        period=period,
        rating="中立",
        lastUpdated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        metrics=MetricSnapshot(),
        charts=ChartBundle(price=[], volume=[], movingAverage=[]),
        agents=[
            AgentInsight(
                name="資料蒐集 Agent",
                role="資料錯誤攔截",
                stance="中立",
                score=0,
                confidence=0.12,
                summary=message,
                narrative=f"資料蒐集階段發生錯誤：{message}。目前無法形成完整分析，系統採中立觀察並保留降級提示。",
                evidence=["資料服務錯誤"],
                degraded=True,
                reasons=["資料不足"],
                risks=[message],
            )
        ],
        debate=[],
        decision=decision,
        sources=[DataSourceStatus(name="FastAPI", status="failed", message=message)],
        reportMarkdown=f"# {normalized} 分析暫停\n\n{message}\n\n{DISCLAIMER}",
        disclaimer=DISCLAIMER,
    )
