from __future__ import annotations

from app.models import AgentInsight, DebateMessage, DecisionSummary
from app.services.market_data import FINMIND_SOURCE, YFINANCE_SOURCE, fmt_number

DISCLAIMER = "本系統分析結果僅供學術研究與投資參考，不構成任何買賣建議。投資人仍應自行評估風險並承擔投資結果。"
DATA_DELAY_NOTE = "資料可能延遲或不完整，本系統不宣稱資料完全即時。"


def generate_markdown_report(
    context,
    agents: list[AgentInsight],
    final_rating: str,
    decision: DecisionSummary,
    debate: list[DebateMessage] | None = None,
) -> str:
    source_items = "\n".join(
        f"- {status.name}：{'成功' if status.ok else '降級'}，{status.message}" for status in context.source_status
    )
    agent_sections = "\n\n".join(
        f"### {agent.name}\n{agent.summary}\n\n立場：{agent.stance}\n\n信心程度：{agent.confidence:.0%}\n\n主要理由："
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

    return f"""# {context.stock_id} {context.stock_name} 多 Agent 台股研究報告

## 一、資料摘要
- 股票代號：{context.stock_id}
- 股票名稱：{context.stock_name}
- 產業分類：{context.industry}
- 最後更新時間：{context.last_updated}
- 股價資料來源：{YFINANCE_SOURCE}
- 基本面與籌碼資料來源：{FINMIND_SOURCE}
- 最新收盤價：{fmt_number(context.latest_close)}
- MA20：{fmt_number(context.ma20)}
- MA60：{fmt_number(context.ma60)}
- 20 日報酬率：{fmt_number(context.return_20d, suffix="%")}
- 平均成交量：{fmt_number(context.average_volume, decimals=0)}
- 月營收成長率：{fmt_number(context.revenue_growth, suffix="%")}
- EPS：{fmt_number(context.eps)}
- 本益比：{fmt_number(context.pe_ratio)}
- 外資買賣超：{fmt_number(context.foreign_buy, decimals=0)}
- 融資餘額變化：{fmt_number(context.margin_balance_change, decimals=0)}
- 股利資料：{context.dividend_summary}

## 二、資料來源與取得狀態
{source_items}

### FinMind 降級提示
{finmind_errors}

## 三、多 Agent 分析
{agent_sections}

## 四、Agent 辯論室
{debate_items}

## 五、最終研究結論
### 綜合評級：{final_rating}

#### 支持理由
{support_items}

#### 反方風險
{risk_items}

#### 觀察重點
{watch_items}

## 六、資料限制與免責聲明
{DATA_DELAY_NOTE}

{DISCLAIMER}
"""
