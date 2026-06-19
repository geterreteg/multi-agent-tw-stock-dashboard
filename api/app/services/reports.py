from __future__ import annotations

from app.models import AgentInsight, DebateMessage, DecisionSummary
from app.services.market_data import FINMIND_SOURCE, YFINANCE_SOURCE, fmt_number
from app.services.target_price import TargetPriceResult

DISCLAIMER = "本系統分析結果僅供學術研究與投資參考，不構成任何買賣建議。投資人仍應自行評估風險並承擔投資結果。"
DATA_DELAY_NOTE = "資料可能延遲或不完整，本系統不宣稱資料完全即時。"


def generate_markdown_report(
    context,
    agents: list[AgentInsight],
    final_rating: str,
    decision: DecisionSummary,
    debate: list[DebateMessage] | None = None,
    target_price: TargetPriceResult | None = None,
) -> str:
    source_items = "\n".join(
        f"- {status.name}：{'成功' if status.ok else '降級'}，{status.message}" for status in context.source_status
    )
    agent_sections = "\n\n".join(
        f"### {agent.name}\n{agent.summary}\n\n{agent.narrative}\n\n"
        f"立場：{agent.stance}\n\n分數：{agent.score:.2f}\n\n信心程度：{agent.confidence:.0%}\n\n"
        f"資料狀態：{'降級' if agent.degraded else '完整'}\n\n使用數據："
        + "\n".join(f"- {item}" for item in agent.evidence)
        + "\n\n主要理由："
        + "\n".join(f"- {reason}" for reason in agent.reasons)
        + "\n\n主要風險："
        + "\n".join(f"- {risk}" for risk in agent.risks)
        for agent in agents
    )
    debate_items = "\n".join(
        f"- **{item.speaker}（{item.stance}）**：{item.message}" for item in (debate or [])
    ) or "- 本次無辯論紀錄。"
    support_items = "\n".join(f"- {item}" for item in decision.supportReasons)
    risk_items = "\n".join(f"- {item}" for item in decision.risks)
    watch_items = "\n".join(f"- {item}" for item in decision.watchPoints)
    finmind_errors = "\n".join(f"- {error}" for error in context.finmind_errors) or "- 無"
    research = decision.researchReport
    target_price_section = format_target_price_section(target_price)
    research_sections = f"""## 三、Public Equity Investing 結構化研究報告

### investmentThesis：投資論點
{list_markdown(research.investmentThesis)}

### keyMetrics：關鍵數據
{list_markdown(research.keyMetrics)}

### businessQuality：商業品質
{list_markdown(research.businessQuality)}

### financialAnalysis：財務或價格分析
{list_markdown(research.financialAnalysis)}

### valuation：估值判斷
{list_markdown(research.valuation)}

### catalysts：正面催化因素
{list_markdown(research.catalysts)}

### risks：主要風險
{list_markdown(research.risks)}

### variantView：反方觀點
{list_markdown(research.variantView)}

### recommendation / confidenceScore
- recommendation：{research.recommendation}
- confidenceScore：{research.confidenceScore}/100
- scoreBreakdown：{research.scoreBreakdown}

### dataGaps：資料缺口
{list_markdown(research.dataGaps or ["未偵測到核心資料缺口，但資料仍可能延遲或不完整。"])}
"""

    return f"""# {context.stock_id} {context.stock_name} 多 Agent 台股研究報告

## 一、資料摘要
- 股票代號：{context.stock_id}
- 股票名稱：{context.stock_name}
- 產業分類：{context.industry}
- 最後更新時間：{context.last_updated}
- 股價資料來源：{YFINANCE_SOURCE}
- 基本面資料來源：{FINMIND_SOURCE}
- 籌碼資料來源：{context.institutional_source}
- 籌碼資料狀態：{context.institutional_status}
- 法人資料日期：{context.institutional_data_date or '資料暫無'}
- 融資融券資料來源：{context.margin_source}
- 融資融券資料狀態：{context.margin_status}
- 融資融券資料日期：{context.margin_data_date or '資料暫無'}
- 最新收盤價：{fmt_price(context.latest_close)}
- MA20：{fmt_price(context.ma20)}
- MA60：{fmt_price(context.ma60)}
- 20 日報酬率：{fmt_number(context.return_20d, suffix="%")}
- 平均成交量：{fmt_number(context.average_volume, decimals=0)}
- 月營收成長率：{fmt_number(context.revenue_growth, suffix="%")}
- EPS：{fmt_number(context.eps)}
- 本益比：{fmt_pe_metric(context)}
- 外資買賣超：{fmt_number(context.foreign_buy, decimals=0)}
- 融資餘額變化：{fmt_number(context.margin_balance_change, decimals=0)}
- 股利資料：{context.dividend_summary}

## 二、資料來源與取得狀態
{source_items}

### FinMind 降級提示
{finmind_errors}

{research_sections}

## 四、規則式估值區間與歷史 PE 估值參考
{target_price_section}

## 五、多 Agent 分析
{agent_sections}

## 六、Agent 辯論室
{debate_items}

## 七、最終研究結論

### 結論
綜合評級：{final_rating}。本評級仍綜合技術面、基本面、籌碼、風險與資料品質；規則式估值區間不單獨主導評級。

finalScore：{decision.finalScore:.2f}

scoreBreakdown：{decision.scoreBreakdown}

### 依據
{support_items}

### 風險
{risk_items}

### 資料限制
{watch_items}

#### 投資建議與操作條件
{decision.recommendationText}

## 八、資料限制與免責聲明
{DATA_DELAY_NOTE}

{DISCLAIMER}
"""


def list_markdown(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) or "- 資料暫無"


def fmt_pe_metric(context) -> str:
    if context.pe_ratio is None:
        return "資料暫無"
    if (context.eps is not None and context.eps < 0) or context.pe_ratio <= 0:
        return f"不適用（EPS {fmt_number(context.eps)}，PE 不具一般估值意義）"
    return fmt_number(context.pe_ratio)


def format_target_price_section(target_price: TargetPriceResult | None) -> str:
    if target_price is None or target_price.valuationMethod == "INSUFFICIENT_DATA":
        limitations = target_price.limitations if target_price is not None else ["後端未提供 targetPrice 契約。"]
        return "資料不足，暫不產生規則式估值區間。\n\n" + list_markdown(limitations)
    return (
        f"- Bear：{target_price.bearTargetPrice}\n"
        f"- Base：{target_price.baseTargetPrice}\n"
        f"- Bull：{target_price.bullTargetPrice}\n"
        f"- Base 隱含空間：{target_price.impliedUpsidePct:.1f}%\n"
        f"- 目前 PE：{format_pe(target_price.fairPERatio)}\n"
        f"- EPS basis：{target_price.epsBasis}\n"
        f"- PE source：{target_price.peSource}\n"
        f"- confidence：{target_price.confidence}/65\n\n"
        + list_markdown(target_price.assumptions)
        + "\n\n限制：\n"
        + list_markdown(target_price.limitations)
    )


def format_pe(value: float | None) -> str:
    if value is None:
        return "資料暫無"
    formatted = f"{value:.2f}".rstrip("0").rstrip(".")
    return formatted if "." in formatted else f"{formatted}.0"


def fmt_price(value: float | None) -> str:
    return fmt_number(value, decimals=0)
