from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import pandas as pd

from app.models import (
    AgentInsight,
    AnalyzeResponse,
    ChartBundle,
    ChipData,
    DataSourceStatus,
    DecisionSummary,
    EquityResearchReport,
    InstitutionalData,
    MarginData,
    MetricSnapshot,
    MovingAveragePoint,
    PricePoint,
    VolumePoint,
)
from app.services.institutional_data import get_institutional_data
from app.services.margin_data import get_margin_data
from app.services.market_data import (
    SourceStatus,
    TPEX_SOURCE,
    TWSE_SOURCE,
    fetch_finmind_bundle,
    fetch_official_price_bundle,
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
    chip_data: dict = field(default_factory=dict)
    institutional_status: str = "missing"
    institutional_data_date: Optional[str] = None
    institutional_source: str = "官方三大法人資料"
    margin_status: str = "missing"
    margin_data_date: Optional[str] = None
    margin_source: str = "官方融資融券資料"


def build_context(symbol: str, period: str = "6mo") -> StockContext:
    stock_id = normalize_symbol(symbol)
    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    token, token_mode = get_finmind_token()
    history, metrics, price_status = fetch_official_price_bundle(stock_id, period)
    finmind = fetch_finmind_bundle(stock_id, token, token_mode)
    market = infer_market_from_price_status(price_status)
    chip_data = build_chip_data(stock_id, market)
    chip_metrics = chip_metrics_from_data(chip_data)

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
        foreign_buy=safe_float(chip_metrics["foreign_buy"]),
        institutional_net_buy=safe_float(chip_metrics["institutional_net_buy"]),
        margin_balance_change=safe_float(chip_metrics["margin_balance_change"]),
        short_balance_change=safe_float(chip_metrics["short_balance_change"]),
        dividend_summary=str(finmind["dividend_summary"]),
        source_status=[price_status, finmind["status"]],
        finmind_errors=list(finmind["errors"]),
        finmind_token_mode=token_mode,
        chip_data=chip_data,
        institutional_status=str(chip_metrics["institutional_status"]),
        institutional_data_date=chip_metrics["institutional_data_date"],
        institutional_source=str(chip_metrics["institutional_source"]),
        margin_status=str(chip_metrics["margin_status"]),
        margin_data_date=chip_metrics["margin_data_date"],
        margin_source=str(chip_metrics["margin_source"]),
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
        chipData=chip_data_to_model(context.chip_data),
        reportMarkdown=report,
        disclaimer=DISCLAIMER,
    )


def build_chart_bundle(history: pd.DataFrame) -> ChartBundle:
    if history.empty or "Close" not in history.columns:
        return ChartBundle(price=[], volume=[], movingAverage=[])

    work = history.copy().reset_index()
    date_col = work.columns[0]
    dates = work[date_col].map(to_date_string)
    open_price = pd.to_numeric(work.get("Open", pd.Series(dtype=float)), errors="coerce")
    high = pd.to_numeric(work.get("High", pd.Series(dtype=float)), errors="coerce")
    low = pd.to_numeric(work.get("Low", pd.Series(dtype=float)), errors="coerce")
    close = pd.to_numeric(work["Close"], errors="coerce")
    volume = pd.to_numeric(work.get("Volume", pd.Series(dtype=float)), errors="coerce")
    ma20 = close.rolling(20).mean()
    ma60 = close.rolling(60).mean()

    price = [
        PricePoint(
            date=date,
            open=safe_float(open_value),
            high=safe_float(high_value),
            low=safe_float(low_value),
            close=safe_float(close_value),
        )
        for date, open_value, high_value, low_value, close_value in zip(dates, open_price, high, low, close)
    ]
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


def infer_market_from_price_status(status: SourceStatus) -> Optional[str]:
    if status.name == TWSE_SOURCE:
        return "TWSE"
    if status.name == TPEX_SOURCE:
        return "TPEX"
    return None


def build_chip_data(stock_id: str, market: Optional[str]) -> dict:
    try:
        institutional = get_institutional_data(stock_id, market=market)
    except Exception as exc:
        institutional = {
            "symbol": stock_id,
            "asOfDate": None,
            "dataDate": None,
            "status": "missing",
            "foreignNetBuy": None,
            "investmentTrustNetBuy": None,
            "dealerNetBuy": None,
            "institutionalNetBuyTotal": None,
            "source": "官方三大法人資料",
            "dataGaps": [{"code": "source_unavailable", "message": f"官方三大法人資料讀取失敗：{type(exc).__name__}"}],
        }

    try:
        margin = get_margin_data(stock_id, market=market)
    except Exception as exc:
        margin = {
            "symbol": stock_id,
            "asOfDate": None,
            "dataDate": None,
            "status": "missing",
            "marginBalance": None,
            "marginChange": None,
            "shortBalance": None,
            "shortChange": None,
            "marginUtilizationRate": None,
            "shortUtilizationRate": None,
            "source": "官方融資融券資料",
            "dataGaps": [{"code": "source_unavailable", "message": f"官方融資融券資料讀取失敗：{type(exc).__name__}"}],
        }

    return {
        "overallStatus": chip_overall_status(institutional, margin),
        "institutional": institutional,
        "margin": margin,
        "dataGaps": [*(institutional.get("dataGaps") or []), *(margin.get("dataGaps") or [])],
    }


def chip_overall_status(institutional: dict, margin: dict) -> str:
    statuses = {institutional.get("status", "missing"), margin.get("status", "missing")}
    if statuses == {"current"}:
        return "current"
    if statuses == {"missing"}:
        return "missing"
    if "missing" in statuses:
        return "partial"
    if "latest_available" in statuses:
        return "latest_available"
    return "missing"


def chip_metrics_from_data(chip_data: dict) -> dict:
    institutional = chip_data.get("institutional") or {}
    margin = chip_data.get("margin") or {}
    institutional_available = institutional.get("status") in {"current", "latest_available"}
    margin_available = margin.get("status") in {"current", "latest_available"}
    return {
        "foreign_buy": institutional.get("foreignNetBuy") if institutional_available else None,
        "institutional_net_buy": institutional.get("institutionalNetBuyTotal") if institutional_available else None,
        "margin_balance_change": margin.get("marginChange") if margin_available else None,
        "short_balance_change": margin.get("shortChange") if margin_available else None,
        "institutional_status": institutional.get("status", "missing"),
        "institutional_data_date": institutional.get("dataDate") or institutional.get("asOfDate"),
        "institutional_source": institutional.get("source", "官方三大法人資料"),
        "margin_status": margin.get("status", "missing"),
        "margin_data_date": margin.get("dataDate") or margin.get("asOfDate"),
        "margin_source": margin.get("source", "官方融資融券資料"),
    }


def chip_data_to_model(chip_data: dict) -> ChipData:
    return ChipData(
        overallStatus=chip_data.get("overallStatus", "missing"),
        institutional=InstitutionalData(**(chip_data.get("institutional") or {})),
        margin=MarginData(**(chip_data.get("margin") or {})),
        dataGaps=chip_data.get("dataGaps") or [],
    )


def build_failed_response(symbol: str, period: str, message: str) -> AnalyzeResponse:
    normalized = symbol.strip() or "UNKNOWN"
    chip_data = build_chip_data(normalized, None)
    research_report = EquityResearchReport(
        investmentThesis=["資料服務失敗，無法形成投資論點。"],
        keyMetrics=["資料不足"],
        businessQuality=["資料不足"],
        financialAnalysis=["資料不足"],
        valuation=["資料不足，不產生目標價。"],
        catalysts=["資料不足"],
        risks=[message],
        variantView=["資料恢復前，所有研究結論需採保守解讀。"],
        recommendation="Neutral / 中性",
        confidenceScore=10,
        dataGaps=["股價資料", "基本面資料", "籌碼資料", message],
        scoreBreakdown={
            "financialOrPricePerformance": 0,
            "growth": 0,
            "valuationReasonableness": 0,
            "catalysts": 0,
            "riskControl": 0,
            "totalScore": 0,
            "dataCoverage": 0,
        },
    )
    decision = DecisionSummary(
        rating=research_report.recommendation,
        supportReasons=research_report.investmentThesis,
        risks=[message],
        watchPoints=research_report.dataGaps,
        recommendationText="資料服務發生錯誤，目前僅能採 Neutral / 中性；請稍後重試，或檢查資料來源與網路狀態。",
        finalScore=0,
        scoreBreakdown=research_report.scoreBreakdown,
        researchReport=research_report,
    )
    return AnalyzeResponse(
        symbol=normalized,
        name=f"{normalized}.TW",
        period=period,
        rating="Neutral / 中性",
        lastUpdated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        metrics=MetricSnapshot(),
        charts=ChartBundle(price=[], volume=[], movingAverage=[]),
        agents=[
            AgentInsight(
                name="資料蒐集 Agent",
                role="資料錯誤攔截",
                stance="Neutral / 中性",
                score=0,
                confidence=0.12,
                summary=message,
                narrative=f"資料蒐集階段發生錯誤：{message}。目前無法形成完整分析，系統採 Neutral / 中性並保留降級提示。",
                evidence=["資料服務錯誤"],
                degraded=True,
                reasons=["資料不足"],
                risks=[message],
            )
        ],
        debate=[],
        decision=decision,
        sources=[DataSourceStatus(name="FastAPI", status="failed", message=message)],
        chipData=chip_data_to_model(chip_data),
        reportMarkdown=f"# {normalized} 分析暫停\n\n{message}\n\n{DISCLAIMER}",
        disclaimer=DISCLAIMER,
    )
