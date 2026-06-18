from app.models import (
    AgentInsight,
    AnalyzeResponse,
    ChartBundle,
    DataSourceStatus,
    DecisionSummary,
    EquityResearchReport,
    MetricSnapshot,
    MovingAveragePoint,
    PricePoint,
    VolumePoint,
)

DISCLAIMER = "本系統分析結果僅供學術研究與投資參考，不構成任何買賣建議。"

STOCK_NAMES = {
    "2330": "台積電",
    "2317": "鴻海",
    "2454": "聯發科",
}


def _series_base(symbol: str) -> tuple[float, float]:
    if symbol == "2317":
        return 188.0, 1.8
    if symbol == "2454":
        return 1280.0, 13.5
    return 2380.0, 18.0


def build_mock_analysis(symbol: str, period: str) -> AnalyzeResponse:
    normalized = symbol.strip() or "2330"
    name = STOCK_NAMES.get(normalized, "示範個股")
    base, step = _series_base(normalized)

    price = []
    volume = []
    moving_average = []
    for index in range(30):
        day = f"2026-05-{index + 1:02d}" if index < 31 else f"2026-06-{index - 30:02d}"
        close = round(base + (index - 15) * step + ((index % 5) - 2) * step * 1.2, 2)
        ma20 = round(close - step * 2 + index * 0.35, 2)
        ma60 = round(close - step * 5 + index * 0.22, 2)
        price.append(PricePoint(date=day, close=close))
        volume.append(VolumePoint(date=day, volume=18_000_000 + index * 420_000 + (index % 4) * 600_000))
        moving_average.append(MovingAveragePoint(date=day, ma20=ma20, ma60=ma60))

    metrics = MetricSnapshot(
        latestClose=price[-1].close,
        return20d=4.2,
        ma20=moving_average[-1].ma20,
        ma60=moving_average[-1].ma60,
        peRatio=28.5,
        eps=22.08,
        revenueGrowth=12.4,
        foreignBuy=18_500,
    )

    agents = [
        AgentInsight(
            name="資料蒐集 Agent",
            role="整合價格、籌碼與基本面資料狀態",
            stance="Neutral / 中性",
            score=0,
            confidence=0.92,
            summary="mock 資料已完成整合，後續可替換為 yfinance 與 FinMind 真實資料。",
            narrative="示範資料包含價格、成交量、均線、EPS、本益比、營收成長與外資買賣超，僅供前端資料格式驗收。",
            evidence=["資料型態：mock", "資料來源：FastAPI mock backend"],
            degraded=True,
            reasons=["資料格式已接近真實 API response", "前端可先完成圖表與卡片驗收"],
            risks=["資料非真實市場資料"],
        ),
        AgentInsight(
            name="技術分析 Agent",
            role="觀察趨勢、均線與短線動能",
            stance="Buy / 看多",
            score=0.5,
            confidence=0.78,
            summary="價格維持在主要均線附近，趨勢偏穩但尚未形成強烈方向。",
            narrative=f"示範最新收盤價 {metrics.latestClose}，MA20 {metrics.ma20}，MA60 {metrics.ma60}，20 日報酬率 {metrics.return20d}%。",
            evidence=[f"最新收盤價：{metrics.latestClose}", f"MA20：{metrics.ma20}", f"MA60：{metrics.ma60}", f"20 日報酬率：{metrics.return20d}%"],
            degraded=True,
            reasons=["MA20 高於 MA60", "20 日報酬為正"],
            risks=["示範資料不可代表真實技術面"],
        ),
        AgentInsight(
            name="基本面 Agent",
            role="評估營收、EPS 與本益比",
            stance="Buy / 看多",
            score=0.5,
            confidence=0.74,
            summary="營收成長與 EPS 具支撐，但評價面仍需與同業比較。",
            narrative=f"示範 EPS {metrics.eps}，本益比 {metrics.peRatio}，營收成長 {metrics.revenueGrowth}%。",
            evidence=[f"EPS：{metrics.eps}", f"本益比：{metrics.peRatio}", f"營收成長：{metrics.revenueGrowth}%"],
            degraded=True,
            reasons=["營收成長率為正", "EPS 維持獲利支撐"],
            risks=["示範資料不可代表真實基本面"],
        ),
        AgentInsight(
            name="風險控管 Agent",
            role="提出反方觀點與資料限制",
            stance="Neutral / 中性",
            score=-0.5,
            confidence=0.70,
            summary="目前資料為示範 mock data，正式分析前仍需接回真實資料源。",
            narrative="風險控管提醒目前資料並非真實 yfinance 或 FinMind 回傳，因此任何評級只可作為前端格式展示。",
            evidence=["資料狀態：mock", "風險：資料非即時且非真實"],
            degraded=True,
            reasons=["資料非即時", "模型仍為規則式研究輔助"],
            risks=["正式分析前需接回真實資料源"],
        ),
        AgentInsight(
            name="決策整合 Agent",
            role="整合多方觀點產生評級",
            stance="Neutral / 中性",
            score=0.25,
            confidence=0.82,
            summary="示範資料只能驗證格式，第一版示範評級為 Neutral / 中性。",
            narrative="示範決策整合技術、基本面與風險提醒後採 Neutral / 中性，不構成買賣建議。",
            evidence=["示範評級：Neutral / 中性", "資料狀態：mock"],
            degraded=True,
            reasons=["正向訊號與風險提醒並存", "適合持續觀察"],
            risks=["示範資料不能作為投資依據"],
        ),
    ]

    research_report = EquityResearchReport(
        investmentThesis=[
            "示範資料總分 58.0/100，僅用於驗證 Public Equity Investing 研究報告欄位。",
            f"價格面示範收盤價 {metrics.latestClose}，20 日報酬率 {metrics.return20d}%。",
            f"基本面示範 EPS {metrics.eps}，本益比 {metrics.peRatio}，營收成長 {metrics.revenueGrowth}%。",
        ],
        keyMetrics=[
            f"最新收盤價：{metrics.latestClose}",
            f"20 日報酬率：{metrics.return20d}%",
            f"MA20 / MA60：{metrics.ma20} / {metrics.ma60}",
            f"EPS：{metrics.eps}",
            f"本益比：{metrics.peRatio}",
            f"營收成長：{metrics.revenueGrowth}%",
            f"外資買賣超：{metrics.foreignBuy}",
        ],
        businessQuality=["mock 資料不可代表真實商業品質。", "正式分析需接回 FinMind 產業分類、月營收與財報。"],
        financialAnalysis=["示範價格、EPS 與營收成長欄位可被前端卡片化呈現。"],
        valuation=["示範本益比僅供格式驗收，不產生目標價。"],
        catalysts=["示範營收成長與價格動能為正，但不代表真實催化因素。"],
        risks=["目前仍為 mock data。", "正式版需驗證 yfinance 與 FinMind 資料完整度。"],
        variantView=["若接回真實資料後營收、EPS 或法人資料不支持，評級應下修。"],
        recommendation="Neutral / 中性",
        confidenceScore=35,
        dataGaps=["真實 yfinance 股價資料", "真實 FinMind 基本面資料", "真實籌碼資料"],
        scoreBreakdown={
            "financialOrPricePerformance": 16,
            "growth": 12,
            "valuationReasonableness": 10,
            "catalysts": 8,
            "riskControl": 12,
            "totalScore": 58,
            "dataCoverage": 30,
        },
    )
    decision = DecisionSummary(
        rating=research_report.recommendation,
        supportReasons=research_report.investmentThesis,
        risks=["目前仍為 mock data", "正式版需驗證 FinMind 權限與資料完整度", "不應視為買賣建議"],
        watchPoints=research_report.dataGaps,
        recommendationText="示範資料僅供格式驗收，正式研究需以 yfinance 與 FinMind 真實資料重新分析，目前採 Neutral / 中性。",
        finalScore=58,
        scoreBreakdown=research_report.scoreBreakdown,
        researchReport=research_report,
    )

    report = f"""# {normalized} {name} 多 Agent 投資分析摘要

## 綜合評級：Neutral / 中性

本報告為新版 Next.js + FastAPI 骨架示範資料，尚未接入真實 yfinance 與 FinMind 分析邏輯。

## 免責聲明

{DISCLAIMER}
"""

    return AnalyzeResponse(
        symbol=normalized,
        name=name,
        period=period,
        rating="Neutral / 中性",
        lastUpdated="2026-06-04 18:00",
        metrics=metrics,
        charts=ChartBundle(price=price, volume=volume, movingAverage=moving_average),
        agents=agents,
        decision=decision,
        sources=[
            DataSourceStatus(name="FastAPI mock backend", status="ok", message="第一版使用 mock data 驗證前端體驗。"),
            DataSourceStatus(name="yfinance / FinMind", status="planned", message="下一階段接回既有 Python 分析邏輯。"),
        ],
        reportMarkdown=report,
        disclaimer=DISCLAIMER,
    )
