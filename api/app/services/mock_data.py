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
        moving_average.append(MovingAveragePoint(date=day, close=close, ma20=ma20, ma60=ma60))

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
            view="mock 資料已完成整合，後續可替換為 yfinance 與 FinMind 真實資料。",
            confidence=92,
            reasons=["資料格式已接近真實 API response", "前端可先完成圖表與卡片驗收"],
        ),
        AgentInsight(
            name="技術分析 Agent",
            role="觀察趨勢、均線與短線動能",
            view="價格維持在主要均線附近，趨勢偏穩但尚未形成強烈方向。",
            confidence=78,
            reasons=["MA20 高於 MA60", "20 日報酬為正"],
        ),
        AgentInsight(
            name="基本面 Agent",
            role="評估營收、EPS 與本益比",
            view="營收成長與 EPS 具支撐，但評價面仍需與同業比較。",
            confidence=74,
            reasons=["營收成長率為正", "EPS 維持獲利支撐"],
        ),
        AgentInsight(
            name="風險控管 Agent",
            role="提出反方觀點與資料限制",
            view="目前資料為示範 mock data，正式分析前仍需接回真實資料源。",
            confidence=70,
            reasons=["資料非即時", "模型仍為規則式研究輔助"],
        ),
        AgentInsight(
            name="決策整合 Agent",
            role="整合多方觀點產生評級",
            view="整體訊號偏穩，第一版示範評級為中立。",
            confidence=82,
            reasons=["正向訊號與風險提醒並存", "適合持續觀察"],
        ),
    ]

    decision = DecisionSummary(
        supportReasons=["短期趨勢維持穩定", "營收與 EPS mock 指標呈現支撐", "法人買賣超示範值為正"],
        risks=["目前仍為 mock data", "正式版需驗證 FinMind 權限與資料完整度", "不應視為買賣建議"],
        watchPoints=["接回真實 yfinance 歷史價格", "接回 FinMind 月營收與法人資料", "建立 API 錯誤與降級狀態"],
    )

    report = f"""# {normalized} {name} 多 Agent 投資分析摘要

## 綜合評級：中立

本報告為新版 Next.js + FastAPI 骨架示範資料，尚未接入真實 yfinance 與 FinMind 分析邏輯。

## 免責聲明

{DISCLAIMER}
"""

    return AnalyzeResponse(
        symbol=normalized,
        name=name,
        period=period,
        rating="中立",
        lastUpdated="2026-06-04 18:00",
        metrics=metrics,
        charts=ChartBundle(price=price, volume=volume, movingAverage=moving_average),
        agents=agents,
        decision=decision,
        sources=[
            DataSourceStatus(name="FastAPI mock backend", status="正常", message="第一版使用 mock data 驗證前端體驗。"),
            DataSourceStatus(name="yfinance / FinMind", status="規劃中", message="下一階段接回既有 Python 分析邏輯。"),
        ],
        reportMarkdown=report,
        disclaimer=DISCLAIMER,
    )
