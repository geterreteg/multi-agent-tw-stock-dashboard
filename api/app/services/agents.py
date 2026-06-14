from __future__ import annotations

from typing import Callable

from app.models import AgentInsight, DebateMessage, DecisionSummary, EquityResearchReport, Rating
from app.services.market_data import fmt_number


def technical_agent(context) -> AgentInsight:
    reasons: list[str] = []
    risks: list[str] = []
    score = 0.0
    available = 0

    if context.latest_close is not None and context.ma20 is not None:
        available += 1
        if context.latest_close > context.ma20:
            score += 0.5
            reasons.append(f"收盤價 {fmt_number(context.latest_close)} 高於 MA20 {fmt_number(context.ma20)}，短線價格位置偏正向。")
        elif context.latest_close < context.ma20:
            score -= 0.5
            risks.append(f"收盤價 {fmt_number(context.latest_close)} 低於 MA20 {fmt_number(context.ma20)}，短線動能轉弱。")
    else:
        risks.append("缺少收盤價或 MA20，短線技術判斷降級。")

    if context.latest_close is not None and context.ma60 is not None:
        available += 1
        if context.latest_close > context.ma60:
            score += 0.5
            reasons.append(f"收盤價高於 MA60 {fmt_number(context.ma60)}，中期趨勢位置仍在均線上方。")
        elif context.latest_close < context.ma60:
            score -= 0.5
            risks.append(f"收盤價低於 MA60 {fmt_number(context.ma60)}，中期趨勢位置偏弱。")
    else:
        risks.append("缺少 MA60，無法完整檢查中期趨勢。")

    if context.ma20 is not None and context.ma60 is not None:
        available += 1
        if context.ma20 > context.ma60:
            score += 0.5
            reasons.append("MA20 高於 MA60，短中期均線結構偏正向。")
        elif context.ma20 < context.ma60:
            score -= 0.5
            risks.append("MA20 低於 MA60，短中期均線結構偏弱。")

    if context.return_20d is not None:
        available += 1
        if context.return_20d > 8:
            score += 0.5
            reasons.append(f"20 日報酬率 {fmt_number(context.return_20d, suffix='%')} 顯示近期相對動能。")
        elif context.return_20d < -8:
            score -= 0.5
            risks.append(f"20 日報酬率 {fmt_number(context.return_20d, suffix='%')} 顯示近期價格壓力。")
        if context.return_20d > 18:
            risks.append("20 日報酬率高於 18%，短線報酬已偏集中，回檔敏感度上升。")
    else:
        risks.append("缺少 20 日報酬率，無法量化短線動能。")

    if context.average_volume is not None:
        available += 1
        if context.average_volume < 1_000_000:
            risks.append(f"近 20 日平均成交量 {fmt_number(context.average_volume, decimals=0)}，流動性偏低。")
    else:
        risks.append("缺少成交量，無法評估流動性與價格訊號品質。")

    score = clamp_score(score)
    return AgentInsight(
        name="技術分析 Agent",
        role="使用股價、均線、報酬率與成交量檢查價格結構",
        stance=score_to_rating(score),
        score=score,
        confidence=bounded_confidence(0.24 + available * 0.12 + min(abs(score), 2) * 0.08),
        summary=f"價格結構分數 {score:.2f}，依據收盤價、MA20、MA60、20 日報酬率與成交量計算。",
        narrative=(
            f"最新收盤價 {fmt_number(context.latest_close)}，MA20 {fmt_number(context.ma20)}，MA60 {fmt_number(context.ma60)}，"
            f"20 日報酬率 {fmt_number(context.return_20d, suffix='%')}，近 20 日平均成交量 "
            f"{fmt_number(context.average_volume, decimals=0)}。"
        ),
        evidence=[
            f"最新收盤價：{fmt_number(context.latest_close)}",
            f"MA20：{fmt_number(context.ma20)}",
            f"MA60：{fmt_number(context.ma60)}",
            f"20 日報酬率：{fmt_number(context.return_20d, suffix='%')}",
            f"近 20 日平均成交量：{fmt_number(context.average_volume, decimals=0)}",
        ],
        degraded=available < 5,
        reasons=reasons or ["可用價格資料未形成明確正向訊號。"],
        risks=risks or ["價格資料未顯示明確規則式風險。"],
    )


def fundamental_agent(context) -> AgentInsight:
    reasons: list[str] = []
    risks: list[str] = []
    score = 0.0
    available = 0

    if context.revenue_growth is not None:
        available += 1
        if context.revenue_growth > 15:
            score += 1.0
            reasons.append(f"月營收年增率 {fmt_number(context.revenue_growth, suffix='%')}，成長強度明顯。")
        elif context.revenue_growth > 5:
            score += 0.5
            reasons.append(f"月營收年增率 {fmt_number(context.revenue_growth, suffix='%')}，營運動能為正。")
        elif context.revenue_growth < -5:
            score -= 0.5
            risks.append(f"月營收年增率 {fmt_number(context.revenue_growth, suffix='%')}，營運動能轉弱。")
    else:
        risks.append("缺少月營收成長率，無法判斷近期營運動能。")

    if context.eps is not None:
        available += 1
        if context.eps > 0:
            score += 0.5
            reasons.append(f"EPS {fmt_number(context.eps)} 為正，具基本獲利能力。")
        else:
            score -= 0.5
            risks.append(f"EPS {fmt_number(context.eps)} 非正值，獲利品質偏弱。")
    else:
        risks.append("缺少 EPS，無法評估獲利能力。")

    if context.pe_ratio is not None:
        available += 1
        if 0 < context.pe_ratio <= 25:
            score += 0.5
            reasons.append(f"本益比 {fmt_pe_metric(context)} 未落入高估值區間。")
        elif pe_not_meaningful(context):
            risks.append(f"本益比 {fmt_pe_metric(context)}，不可解讀為低估。")
        elif context.pe_ratio >= 40:
            score -= 0.5
            risks.append(f"本益比 {fmt_pe_metric(context)} 偏高，需由成長或獲利改善支撐。")
    else:
        risks.append("缺少本益比，估值判斷需降級。")

    score = clamp_score(score)
    return AgentInsight(
        name="基本面 Agent",
        role="使用月營收、EPS、本益比與產業分類檢查營運與估值",
        stance=score_to_rating(score),
        score=score,
        confidence=bounded_confidence(0.22 + available * 0.17 + min(abs(score), 2) * 0.06),
        summary=f"基本面分數 {score:.2f}，依據營收成長、EPS 與本益比計算。",
        narrative=(
            f"產業分類為 {context.industry or '資料暫無'}；月營收成長率 {fmt_number(context.revenue_growth, suffix='%')}，"
            f"EPS {fmt_number(context.eps)}，本益比 {fmt_pe_metric(context)}，最新營收 "
            f"{fmt_number(context.latest_revenue, decimals=0)}。"
        ),
        evidence=[
            f"產業分類：{context.industry or '資料暫無'}",
            f"最新月營收：{fmt_number(context.latest_revenue, decimals=0)}",
            f"月營收成長率：{fmt_number(context.revenue_growth, suffix='%')}",
            f"EPS：{fmt_number(context.eps)}",
            f"本益比：{fmt_pe_metric(context)}",
        ],
        degraded=available < 3,
        reasons=reasons or ["可用財務資料未形成明確正向訊號。"],
        risks=risks or ["財務資料未顯示明確規則式風險。"],
    )


def chip_agent(context) -> AgentInsight:
    reasons: list[str] = []
    risks: list[str] = []
    score = 0.0
    available = 0

    if context.foreign_buy is not None:
        available += 1
        if context.foreign_buy > 0:
            score += 0.5
            reasons.append(f"外資買賣超 {fmt_number(context.foreign_buy, decimals=0)}，最近一日偏買方。")
        elif context.foreign_buy < 0:
            score -= 0.5
            risks.append(f"外資買賣超 {fmt_number(context.foreign_buy, decimals=0)}，最近一日偏賣方。")
    else:
        risks.append("缺少外資買賣超，無法檢查外資方向。")

    if context.institutional_net_buy is not None:
        available += 1
        if context.institutional_net_buy > 0:
            score += 0.5
            reasons.append(f"三大法人合計 {fmt_number(context.institutional_net_buy, decimals=0)}，法人資金偏流入。")
        elif context.institutional_net_buy < 0:
            score -= 0.5
            risks.append(f"三大法人合計 {fmt_number(context.institutional_net_buy, decimals=0)}，法人資金偏流出。")
    else:
        risks.append("缺少三大法人合計買賣超，資金面判斷降級。")

    if context.margin_balance_change is not None:
        available += 1
        if context.margin_balance_change > 0 and context.latest_close is not None and context.ma20 is not None and context.latest_close < context.ma20:
            score -= 0.75
            risks.append("融資餘額增加且股價低於 MA20，信用籌碼承壓。")
        elif context.margin_balance_change < 0:
            score += 0.25
            reasons.append(f"融資餘額變化 {fmt_number(context.margin_balance_change, decimals=0)}，槓桿籌碼壓力下降。")
    else:
        risks.append("缺少融資餘額變化，無法檢查信用交易壓力。")

    score = clamp_score(score)
    return AgentInsight(
        name="籌碼分析 Agent",
        role="使用外資、三大法人與融資融券檢查資金流向",
        stance=score_to_rating(score),
        score=score,
        confidence=bounded_confidence(0.20 + available * 0.16 + min(abs(score), 2) * 0.07),
        summary=f"籌碼分數 {score:.2f}，依據法人買賣超與融資餘額變化計算。",
        narrative=(
            f"外資買賣超 {fmt_number(context.foreign_buy, decimals=0)}，三大法人合計 "
            f"{fmt_number(context.institutional_net_buy, decimals=0)}，融資餘額變化 "
            f"{fmt_number(context.margin_balance_change, decimals=0)}。"
        ),
        evidence=[
            f"外資買賣超：{fmt_number(context.foreign_buy, decimals=0)}",
            f"三大法人合計：{fmt_number(context.institutional_net_buy, decimals=0)}",
            f"融資餘額變化：{fmt_number(context.margin_balance_change, decimals=0)}",
            f"融券餘額變化：{fmt_number(context.short_balance_change, decimals=0)}",
        ],
        degraded=available < 3,
        reasons=reasons or ["可用籌碼資料未形成明確正向訊號。"],
        risks=risks or ["籌碼資料未顯示明確規則式風險。"],
    )


def risk_agent(context, prior_agents: list[AgentInsight]) -> AgentInsight:
    risks = unique_items([risk for agent in prior_agents for risk in agent.risks])
    for status in context.source_status:
        if not status.ok:
            risks.append(status.message)
    risks.extend(context.finmind_errors[:3])
    risks = unique_items(risks)

    if context.return_20d is not None and context.return_20d > 18:
        risks.append("20 日報酬率偏高，價格對利空消息的敏感度上升。")
    if context.pe_ratio is not None and context.pe_ratio >= 40:
        risks.append("本益比偏高，若營收或 EPS 未同步改善，估值收縮風險上升。")
    if context.revenue_growth is not None and context.revenue_growth < -5:
        risks.append("月營收年增率轉弱，基本面修正風險上升。")

    risks = unique_items(risks) or ["目前規則未偵測到重大風險，但資料可能延遲或不完整。"]
    risk_score = risk_score_from_count(len(risks))
    return AgentInsight(
        name="風險控管 Agent",
        role="從反方角度檢查資料缺口、價格過熱、估值與籌碼壓力",
        stance=score_to_rating(risk_score),
        score=risk_score,
        confidence=bounded_confidence(0.38 + min(len(risks), 6) * 0.06),
        summary=f"已辨識 {len(risks)} 項風險或資料限制。",
        narrative=(
            f"風險檢查納入資料來源狀態、20 日報酬率 {fmt_number(context.return_20d, suffix='%')}、"
            f"本益比 {fmt_pe_metric(context)}、法人買賣超與融資變化。"
        ),
        evidence=[
            f"風險項目數：{len(risks)}",
            f"資料來源：{'; '.join(status.message for status in context.source_status) or '資料暫無'}",
            f"FinMind 降級提示數：{len(context.finmind_errors)}",
        ],
        degraded=any(not status.ok for status in context.source_status),
        reasons=["風險控管 Agent 僅在可量化風險較低時支撐評級。"],
        risks=risks,
    )


def decision_agent(context, prior_agents: list[AgentInsight]) -> tuple[AgentInsight, DecisionSummary, Rating]:
    report = build_equity_research_report(context, prior_agents)
    final_score = round(report.scoreBreakdown["totalScore"], 2)
    confidence = report.confidenceScore / 100
    recommendation_text = build_recommendation_text(context, report, final_score)
    decision = DecisionSummary(
        rating=report.recommendation,
        supportReasons=report.investmentThesis,
        risks=report.risks,
        watchPoints=report.dataGaps or ["本次核心資料已可用，但仍需留意資料延遲。"],
        recommendationText=recommendation_text,
        finalScore=final_score,
        scoreBreakdown=report.scoreBreakdown,
        researchReport=report,
    )
    agent = AgentInsight(
        name="總結決策 Agent",
        role="整合價格、成長、估值、催化因素與風險控制評分",
        stance=report.recommendation,
        score=score_from_total(final_score),
        confidence=confidence,
        summary=f"研究報告評級 {report.recommendation}，總分 {final_score:.1f}/100。",
        narrative=recommendation_text,
        evidence=report.keyMetrics,
        degraded=bool(report.dataGaps),
        reasons=report.investmentThesis,
        risks=report.risks,
    )
    return agent, decision, report.recommendation


def build_equity_research_report(context, agents: list[AgentInsight]) -> EquityResearchReport:
    gaps = collect_data_gaps(context)
    metrics = [
        f"產業分類：{context.industry or '資料暫無'}",
        f"最新收盤價：{fmt_number(context.latest_close)}",
        f"20 日報酬率：{fmt_number(context.return_20d, suffix='%')}",
        f"MA20 / MA60：{fmt_number(context.ma20)} / {fmt_number(context.ma60)}",
        f"近 20 日平均成交量：{fmt_number(context.average_volume, decimals=0)}",
        f"月營收成長率：{fmt_number(context.revenue_growth, suffix='%')}",
        f"EPS：{fmt_number(context.eps)}",
        f"本益比：{fmt_pe_metric(context)}",
        f"外資買賣超：{fmt_number(context.foreign_buy, decimals=0)}",
        f"三大法人合計：{fmt_number(context.institutional_net_buy, decimals=0)}",
        f"融資餘額變化：{fmt_number(context.margin_balance_change, decimals=0)}",
    ]
    category_scores = {
        "financialOrPricePerformance": score_financial_or_price(context),
        "growth": score_growth(context),
        "valuationReasonableness": score_valuation(context),
        "catalysts": score_catalysts(context),
        "riskControl": score_risk_control(context, agents, gaps),
    }
    total = round(sum(category_scores.values()), 2)
    coverage = data_coverage(context)
    source_penalty = 10 if any(not status.ok for status in context.source_status) else 0
    valuation_penalty = 8 if pe_not_meaningful(context) else 0
    confidence = int(max(0, min(100, round(coverage * 70 + min(total, 100) * 0.20 - len(gaps) * 4 - source_penalty - valuation_penalty))))
    recommendation = recommendation_from_score(total, confidence, gaps)
    if pe_not_meaningful(context) and recommendation in {"Strong Buy / 強烈看多", "Buy / 看多"}:
        recommendation = "Neutral / 中性"

    thesis = build_thesis(context, total, recommendation)
    business_quality = build_business_quality(context)
    financial_analysis = build_financial_analysis(context)
    valuation = build_valuation(context)
    catalysts = build_catalysts(context)
    risks = unique_items([risk for agent in agents for risk in agent.risks[:3]])
    if not risks:
        risks = ["資料可能延遲或不完整，且本系統未納入公司法說、供應鏈與同業估值資料。"]
    variant_view = build_variant_view(context, recommendation, risks)

    return EquityResearchReport(
        investmentThesis=thesis,
        keyMetrics=metrics,
        businessQuality=business_quality,
        financialAnalysis=financial_analysis,
        valuation=valuation,
        catalysts=catalysts,
        risks=risks,
        variantView=variant_view,
        recommendation=recommendation,
        confidenceScore=confidence,
        dataGaps=gaps,
        scoreBreakdown={
            **category_scores,
            "totalScore": total,
            "dataCoverage": round(coverage * 100, 1),
        },
    )


def build_thesis(context, total: float, recommendation: Rating) -> list[str]:
    items = [
        f"目前建議：{recommendation_action_label(recommendation)}。評級為 {recommendation}，總分 {total:.1f}/100，屬規則式研究結論，不含目標價。"
    ]
    items.append(primary_reason(context, recommendation))
    if context.latest_close is not None and context.ma20 is not None and context.ma60 is not None:
        relation = "高於" if context.latest_close > context.ma20 and context.latest_close > context.ma60 else "未同時高於"
        items.append(f"價格面：收盤價 {fmt_number(context.latest_close)} {relation} MA20/MA60，形成主要趨勢判斷。")
    if context.revenue_growth is not None or context.eps is not None:
        items.append(f"基本面：月營收成長 {fmt_number(context.revenue_growth, suffix='%')}，EPS {fmt_number(context.eps)}。")
    if context.foreign_buy is not None or context.institutional_net_buy is not None:
        items.append(f"資金面：外資買賣超 {fmt_number(context.foreign_buy, decimals=0)}，三大法人合計 {fmt_number(context.institutional_net_buy, decimals=0)}。")
    return items


def build_business_quality(context) -> list[str]:
    items = [f"產業分類為 {context.industry or '資料暫無'}；若產業分類缺漏，商業品質判斷降級。"]
    if context.revenue_growth is not None:
        direction = "擴張" if context.revenue_growth > 0 else "收縮或持平"
        items.append(f"近期營運動能以月營收年增率衡量，目前為 {fmt_number(context.revenue_growth, suffix='%')}，顯示 {direction}。")
    else:
        items.append("缺少月營收成長率，無法判斷近期需求與營運品質。")
    if context.eps is not None:
        items.append(f"EPS {fmt_number(context.eps)} 用於檢查獲利能力；本系統未推估未來 EPS。")
    else:
        items.append("缺少 EPS，無法建立獲利品質判斷。")
    return items


def build_financial_analysis(context) -> list[str]:
    return [
        f"價格表現：20 日報酬率 {fmt_number(context.return_20d, suffix='%')}，用於衡量短期動能或壓力。",
        f"趨勢位置：最新收盤 {fmt_number(context.latest_close)}，MA20 {fmt_number(context.ma20)}，MA60 {fmt_number(context.ma60)}。",
        f"財務表現：最新月營收 {fmt_number(context.latest_revenue, decimals=0)}，月營收成長 {fmt_number(context.revenue_growth, suffix='%')}，EPS {fmt_number(context.eps)}。",
        f"籌碼表現：外資買賣超 {fmt_number(context.foreign_buy, decimals=0)}，三大法人合計 {fmt_number(context.institutional_net_buy, decimals=0)}，融資餘額變化 {fmt_number(context.margin_balance_change, decimals=0)}。",
    ]


def build_valuation(context) -> list[str]:
    if context.pe_ratio is None:
        return ["缺少本益比，不能判斷估值是否合理，也不產生目標價。"]
    if pe_not_meaningful(context):
        return [
            f"EPS 為 {fmt_number(context.eps)}，本益比顯示為 {fmt_number(context.pe_ratio)}；在虧損或 PE 無效情境下，PE 不具一般估值意義，也不應解讀為便宜。",
            "目前沒有同業本益比、EV/EBITDA、FCF 或 DCF 資料，因此不產生目標價。",
        ]
    if context.pe_ratio <= 25:
        view = "估值未落入高估區間，但仍需同業比較確認。"
    elif context.pe_ratio <= 40:
        view = "估值偏高，需要營收成長與 EPS 改善支持。"
    else:
        view = "估值壓力高，若成長未加速，評級會受壓抑。"
    return [f"本益比為 {fmt_number(context.pe_ratio)}；{view}", "目前沒有同業本益比、EV/EBITDA、FCF 或 DCF 資料，因此不產生目標價。"]


def pe_not_meaningful(context) -> bool:
    return (context.eps is not None and context.eps < 0) or (context.pe_ratio is not None and context.pe_ratio <= 0)


def fmt_pe_metric(context) -> str:
    if context.pe_ratio is None:
        return "資料暫無"
    if pe_not_meaningful(context):
        return f"不適用（EPS {fmt_number(context.eps)}，PE 不具一般估值意義）"
    return fmt_number(context.pe_ratio)


def build_catalysts(context) -> list[str]:
    items: list[str] = []
    if context.revenue_growth is not None and context.revenue_growth > 5:
        items.append(f"月營收年增率 {fmt_number(context.revenue_growth, suffix='%')}，可作為短期基本面催化。")
    if context.latest_close is not None and context.ma20 is not None and context.latest_close > context.ma20:
        items.append("股價站上 MA20，若成交量同步放大，價格動能可延續。")
    if context.foreign_buy is not None and context.foreign_buy > 0:
        items.append(f"外資買超 {fmt_number(context.foreign_buy, decimals=0)}，短期資金面偏正向。")
    if context.institutional_net_buy is not None and context.institutional_net_buy > 0:
        items.append(f"三大法人合計買超 {fmt_number(context.institutional_net_buy, decimals=0)}，法人資金方向提供支撐。")
    return items or ["目前缺少可量化正面催化因素；不以敘事假設補充。"]


def build_variant_view(context, recommendation: Rating, risks: list[str]) -> list[str]:
    items = [f"若後續資料證明目前訊號不可持續，{recommendation} 評級需要下修。"]
    items.append(f"轉強條件：{'; '.join(strengthening_conditions(context)[:3])}")
    items.append(f"轉弱條件：{'; '.join(weakening_conditions(context)[:3])}")
    if pe_not_meaningful(context):
        items.append("EPS 為負或 PE 無效時，反方可主張目前不宜積極布局；除非 EPS 轉正、營收改善或籌碼明顯轉強，否則應維持保守。")
    if context.pe_ratio is not None and context.pe_ratio > 30:
        items.append("反方可主張估值已提前反映成長，營收或 EPS 不如預期會造成估值收縮。")
    if context.return_20d is not None and context.return_20d > 15:
        items.append("反方可主張短線漲幅已集中，風險報酬比不再對多方有利。")
    if risks:
        items.append(f"最直接的反方依據：{risks[0]}")
    return items


def build_recommendation_text(context, report: EquityResearchReport, final_score: float) -> str:
    action = recommendation_action_label(report.recommendation)
    reason = primary_reason(context, report.recommendation)
    strategy = operation_strategy(context, report.recommendation)
    stronger = "；".join(strengthening_conditions(context))
    weaker = "；".join(weakening_conditions(context))
    risks = sentence_join(report.risks[:3]) if report.risks else "資料不足，需保守解讀。"
    indicators = "；".join(key_observation_indicators(context))
    gaps = f" 資料缺口：{sentence_join(report.dataGaps[:3])}" if report.dataGaps else ""
    pe_note = " EPS 為負或 PE 無效，因此本益比不具一般估值意義，不能解讀為便宜。" if pe_not_meaningful(context) else ""
    return (
        f"核心結論：{context.stock_id} {context.stock_name} 目前建議為「{action}」，規則式評級為 {report.recommendation}，"
        f"finalScore {final_score:.1f}/100，confidenceScore {report.confidenceScore}/100。{reason}{pe_note}\n"
        f"操作策略：{strategy}\n"
        f"轉強條件：{stronger}\n"
        f"轉弱條件：{weaker}\n"
        f"主要風險：{risks}\n"
        f"關鍵觀察指標：{indicators}。{gaps}"
        "本結論僅供課程研究與資料分析展示，不構成正式投資建議或獲利保證。"
    )


def recommendation_action_label(recommendation: Rating) -> str:
    if recommendation == "Strong Buy / 強烈看多":
        return "具較高吸引力，但仍應設定停損與風險上限"
    if recommendation == "Buy / 看多":
        return "偏正向，可分批觀察或等待合理價位布局"
    if recommendation == "Neutral / 中性":
        return "觀望、不建議追價，等待更明確訊號"
    if recommendation == "Sell / 看空":
        return "偏保守，建議降低曝險或暫停新增布局"
    return "高風險，避免積極布局並等待基本面或趨勢改善"


def primary_reason(context, recommendation: Rating) -> str:
    trend_text = trend_summary(context)
    growth_text = growth_summary(context)
    chip_text = chip_summary(context)
    if recommendation in {"Strong Buy / 強烈看多", "Buy / 看多"}:
        return f"偏正向的主要原因是{trend_text}，且{growth_text}，同時需確認{chip_text}是否延續。"
    if recommendation == "Neutral / 中性":
        return f"採觀望的主要原因是多空訊號未形成一致結論：{trend_text}，{growth_text}，但{chip_text}。"
    return f"偏保守的主要原因是{trend_text}，且{chip_text}；若基本面沒有明顯改善，風險報酬比不宜積極承擔。"


def operation_strategy(context, recommendation: Rating) -> str:
    if recommendation == "Strong Buy / 強烈看多":
        return "若已持有，可續抱但應以 MA20 或近期支撐作為風險控管；若尚未持有，仍建議分批，不宜一次重倉。"
    if recommendation == "Buy / 看多":
        return "可偏正向追蹤，但以逢回分批觀察為主，避免在短線急漲後追價。"
    if recommendation == "Neutral / 中性":
        return "以觀望為主，不建議追價；等待價格重新站回關鍵均線、EPS 或營收訊號改善、籌碼轉強後再提高關注。"
    if recommendation == "Sell / 看空":
        return "建議降低曝險或暫停新增布局；若已有部位，應檢查是否跌破均線或基本面惡化而需要控管風險。"
    return "建議避免積極布局；除非價格趨勢、EPS、營收與籌碼至少兩項明顯改善，否則維持保守。"


def strengthening_conditions(context) -> list[str]:
    conditions: list[str] = []
    if context.latest_close is None or context.ma20 is None:
        conditions.append("補齊收盤價與 MA20 後再確認短線趨勢")
    elif context.latest_close <= context.ma20:
        conditions.append(f"收盤價重新站回 MA20 {fmt_number(context.ma20)}")
    else:
        conditions.append("收盤價維持在 MA20 之上")
    if context.latest_close is None or context.ma60 is None:
        conditions.append("補齊 MA60 後再確認中期趨勢")
    elif context.latest_close <= context.ma60:
        conditions.append(f"收盤價重新站回 MA60 {fmt_number(context.ma60)}")
    else:
        conditions.append("收盤價維持在 MA60 之上")
    if context.eps is None:
        conditions.append("EPS 資料補齊且轉為正向")
    elif context.eps <= 0:
        conditions.append("EPS 轉正，讓 PE 重新具備一般估值意義")
    else:
        conditions.append("EPS 維持正值")
    if context.revenue_growth is None:
        conditions.append("月營收成長資料補齊")
    elif context.revenue_growth <= 5:
        conditions.append("月營收年增率回到 5% 以上")
    else:
        conditions.append("月營收年增率維持正成長")
    if context.foreign_buy is None and context.institutional_net_buy is None:
        conditions.append("法人買賣超資料補齊")
    elif (context.foreign_buy or 0) <= 0 and (context.institutional_net_buy or 0) <= 0:
        conditions.append("外資或三大法人買賣超轉正")
    else:
        conditions.append("法人買盤延續")
    return unique_items(conditions)


def weakening_conditions(context) -> list[str]:
    conditions: list[str] = []
    if context.latest_close is not None and context.ma20 is not None:
        conditions.append(f"收盤價跌破或持續低於 MA20 {fmt_number(context.ma20)}")
    else:
        conditions.append("價格與 MA20 資料不足，無法確認短線風險")
    if context.latest_close is not None and context.ma60 is not None:
        conditions.append(f"收盤價跌破或持續低於 MA60 {fmt_number(context.ma60)}")
    else:
        conditions.append("MA60 資料不足，無法確認中期趨勢")
    if context.revenue_growth is None:
        conditions.append("月營收資料不足，營運動能需降級判讀")
    elif context.revenue_growth < 0:
        conditions.append("月營收年增率維持負成長")
    else:
        conditions.append("月營收年增率明顯放緩")
    if context.eps is None:
        conditions.append("EPS 資料不足")
    elif context.eps <= 0:
        conditions.append("EPS 持續為負")
    else:
        conditions.append("EPS 轉弱或低於預期")
    if context.foreign_buy is None and context.institutional_net_buy is None:
        conditions.append("法人籌碼資料不足")
    elif (context.foreign_buy or 0) < 0 or (context.institutional_net_buy or 0) < 0:
        conditions.append("外資或三大法人持續賣超")
    else:
        conditions.append("法人買盤轉為賣超")
    return unique_items(conditions)


def key_observation_indicators(context) -> list[str]:
    return [
        f"收盤價 {fmt_number(context.latest_close)}",
        f"MA20 {fmt_number(context.ma20)}",
        f"MA60 {fmt_number(context.ma60)}",
        f"20 日報酬率 {fmt_number(context.return_20d, suffix='%')}",
        f"EPS {fmt_number(context.eps)}",
        f"本益比 {fmt_pe_metric(context)}",
        f"月營收成長 {fmt_number(context.revenue_growth, suffix='%')}",
        f"外資買賣超 {fmt_number(context.foreign_buy, decimals=0)}",
        f"三大法人合計 {fmt_number(context.institutional_net_buy, decimals=0)}",
        f"融資餘額變化 {fmt_number(context.margin_balance_change, decimals=0)}",
    ]


def trend_summary(context) -> str:
    if context.latest_close is None:
        return "缺少最新收盤價，價格趨勢資料不足"
    if context.ma20 is None or context.ma60 is None:
        return "均線資料不足，趨勢判讀需降級"
    if context.latest_close > context.ma20 and context.latest_close > context.ma60:
        return "價格同時站上 MA20 與 MA60"
    if context.latest_close < context.ma20 and context.latest_close < context.ma60:
        return "價格同時低於 MA20 與 MA60"
    if context.latest_close < context.ma20:
        return "價格低於 MA20，短線動能偏弱"
    return "價格高於 MA20 但中期趨勢仍需確認"


def growth_summary(context) -> str:
    revenue = "月營收資料不足" if context.revenue_growth is None else f"月營收年增率 {fmt_number(context.revenue_growth, suffix='%')}"
    eps = "EPS 資料不足" if context.eps is None else f"EPS {fmt_number(context.eps)}"
    return f"{revenue}，{eps}"


def chip_summary(context) -> str:
    if context.foreign_buy is None and context.institutional_net_buy is None:
        return "法人籌碼資料不足"
    return f"外資買賣超 {fmt_number(context.foreign_buy, decimals=0)}、三大法人合計 {fmt_number(context.institutional_net_buy, decimals=0)}"


def sentence_join(items: list[str]) -> str:
    cleaned = [item.rstrip("。；; ") for item in items if item]
    if not cleaned:
        return "資料不足。"
    return "；".join(cleaned) + "。"


def collect_data_gaps(context) -> list[str]:
    checks = [
        ("最新收盤價", context.latest_close),
        ("20 日報酬率", context.return_20d),
        ("MA20", context.ma20),
        ("MA60", context.ma60),
        ("近 20 日平均成交量", context.average_volume),
        ("月營收成長率", context.revenue_growth),
        ("EPS", context.eps),
        ("本益比", context.pe_ratio),
        ("外資買賣超", context.foreign_buy),
        ("三大法人合計買賣超", context.institutional_net_buy),
        ("融資餘額變化", context.margin_balance_change),
    ]
    gaps = [f"缺少{label}" for label, value in checks if value is None]
    if not context.industry or context.industry == "未分類":
        gaps.append("缺少可用產業分類")
    gaps.extend(context.finmind_errors[:3])
    return unique_items(gaps)


def data_coverage(context) -> float:
    values = [
        context.latest_close,
        context.return_20d,
        context.ma20,
        context.ma60,
        context.average_volume,
        context.revenue_growth,
        context.eps,
        context.pe_ratio,
        context.foreign_buy,
        context.institutional_net_buy,
        context.margin_balance_change,
    ]
    return sum(value is not None for value in values) / len(values)


def score_financial_or_price(context) -> float:
    score = 0.0
    if context.latest_close is not None and context.ma20 is not None:
        score += 5 if context.latest_close > context.ma20 else 1
    if context.latest_close is not None and context.ma60 is not None:
        score += 5 if context.latest_close > context.ma60 else 1
    if context.return_20d is not None:
        score += 5 if context.return_20d > 5 else 3 if context.return_20d >= -5 else 1
    if context.eps is not None:
        score += 5 if context.eps > 0 else 0
    if context.revenue_growth is not None:
        score += 5 if context.revenue_growth > 5 else 3 if context.revenue_growth >= 0 else 1
    return min(score, 25)


def score_growth(context) -> float:
    score = 0.0
    if context.revenue_growth is not None:
        score += 12 if context.revenue_growth > 15 else 8 if context.revenue_growth > 5 else 4 if context.revenue_growth >= 0 else 1
    if context.return_20d is not None:
        score += 5 if context.return_20d > 5 else 3 if context.return_20d >= -5 else 1
    if context.eps is not None:
        score += 3 if context.eps > 0 else 0
    return min(score, 20)


def score_valuation(context) -> float:
    if context.pe_ratio is None:
        return 4
    if context.pe_ratio <= 0:
        return 2
    if context.pe_ratio <= 20:
        return 18
    if context.pe_ratio <= 30:
        return 14
    if context.pe_ratio <= 40:
        return 9
    return 4


def score_catalysts(context) -> float:
    score = 0.0
    if context.revenue_growth is not None and context.revenue_growth > 5:
        score += 4
    if context.latest_close is not None and context.ma20 is not None and context.latest_close > context.ma20:
        score += 3
    if context.latest_close is not None and context.ma60 is not None and context.latest_close > context.ma60:
        score += 3
    if context.foreign_buy is not None and context.foreign_buy > 0:
        score += 2.5
    if context.institutional_net_buy is not None and context.institutional_net_buy > 0:
        score += 2.5
    return min(score, 15)


def score_risk_control(context, agents: list[AgentInsight], gaps: list[str]) -> float:
    score = 20.0
    risk_count = len(unique_items([risk for agent in agents for risk in agent.risks]))
    score -= min(risk_count, 6) * 1.5
    score -= min(len(gaps), 6) * 1.0
    if context.return_20d is not None and context.return_20d > 18:
        score -= 3
    if context.pe_ratio is not None and context.pe_ratio > 40:
        score -= 3
    if context.margin_balance_change is not None and context.margin_balance_change > 0 and context.latest_close is not None and context.ma20 is not None and context.latest_close < context.ma20:
        score -= 3
    return max(0, round(score, 2))


def recommendation_from_score(total: float, confidence: int, gaps: list[str]) -> Rating:
    core_gap = any("最新收盤價" in gap or "EPS" in gap or "本益比" in gap or "月營收" in gap for gap in gaps)
    if confidence < 45 or core_gap and total >= 62:
        return "Neutral / 中性"
    if total >= 82 and confidence >= 75 and len(gaps) <= 2:
        return "Strong Buy / 強烈看多"
    if total >= 62:
        return "Buy / 看多"
    if total >= 45:
        return "Neutral / 中性"
    if total >= 30:
        return "Sell / 看空"
    return "Strong Sell / 強烈看空"


def run_agents(context) -> tuple[list[AgentInsight], list[DebateMessage], DecisionSummary, Rating]:
    technical = safe_agent_call(technical_agent, context, "技術分析 Agent", "技術分析失敗，已改以資料不足處理。")
    fundamental = safe_agent_call(fundamental_agent, context, "基本面 Agent", "基本面分析失敗，已改以資料不足處理。")
    chip = safe_agent_call(chip_agent, context, "籌碼分析 Agent", "籌碼分析失敗，已改以資料不足處理。")
    prior_agents = [technical, fundamental, chip]
    risk = safe_risk_agent(context, prior_agents)
    decision, summary, rating = safe_decision_agent(context, prior_agents + [risk])
    agents = prior_agents + [risk, decision]
    return agents, build_debate(agents, rating), summary, rating


def safe_agent_call(builder: Callable, context, name: str, message: str) -> AgentInsight:
    try:
        return builder(context)
    except Exception as exc:
        return fallback_agent(name, message, exc)


def safe_risk_agent(context, prior_agents: list[AgentInsight]) -> AgentInsight:
    try:
        return risk_agent(context, prior_agents)
    except Exception as exc:
        return fallback_agent("風險控管 Agent", "風險控管失敗，已保留反方降級提示。", exc)


def safe_decision_agent(context, agents: list[AgentInsight]) -> tuple[AgentInsight, DecisionSummary, Rating]:
    try:
        return decision_agent(context, agents)
    except Exception as exc:
        fallback = fallback_agent("總結決策 Agent", "總結決策失敗，已採中性。", exc)
        report = EquityResearchReport(
            investmentThesis=["決策模型降級，無法形成完整投資論點。"],
            keyMetrics=["資料不足"],
            businessQuality=["資料不足"],
            financialAnalysis=["資料不足"],
            valuation=["資料不足，不產生目標價。"],
            catalysts=["資料不足"],
            risks=fallback.risks,
            variantView=["資料服務恢復前，所有評級需採保守解讀。"],
            recommendation="Neutral / 中性",
            confidenceScore=12,
            dataGaps=["決策模型降級"],
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
        summary = DecisionSummary(
            rating=report.recommendation,
            supportReasons=report.investmentThesis,
            risks=fallback.risks,
            watchPoints=report.dataGaps,
            recommendationText=f"總結決策發生降級：{type(exc).__name__}。目前採 Neutral / 中性。",
            finalScore=0,
            scoreBreakdown=report.scoreBreakdown,
            researchReport=report,
        )
        return fallback, summary, "Neutral / 中性"


def fallback_agent(name: str, message: str, exc: Exception) -> AgentInsight:
    return AgentInsight(
        name=name,
        role="規則式分析降級",
        stance="Neutral / 中性",
        score=0,
        confidence=0.12,
        summary=message,
        narrative=f"{name} 無法完成完整規則式分析，錯誤類型為 {type(exc).__name__}；目前不補造資料並採中性處理。",
        evidence=["資料不足"],
        degraded=True,
        reasons=["資料不足"],
        risks=[f"{message} 錯誤類型：{type(exc).__name__}"],
    )


def build_debate(agents: list[AgentInsight], rating: Rating) -> list[DebateMessage]:
    debate: list[DebateMessage] = []
    for agent in agents:
        if agent.name == "總結決策 Agent":
            tone = "summary"
            message = f"整合價格、成長、估值、催化與風險控制後，研究評級為 {rating}。"
        elif agent.name == "風險控管 Agent":
            tone = "risk"
            message = "反方觀點：" + "；".join(agent.risks[:3])
        elif agent.score < 0:
            tone = "risk"
            message = f"{agent.summary} 主要疑慮：" + "；".join(agent.risks[:2])
        elif agent.score > 0:
            tone = "support"
            message = f"{agent.summary} 支持理由：" + "；".join(agent.reasons[:2])
        else:
            tone = "neutral"
            message = f"{agent.summary} 目前可用證據不足以支持更高或更低評級。"

        debate.append(DebateMessage(speaker=agent.name, stance=agent.stance, message=message, tone=tone))
    return debate


def score_to_rating(score: float) -> Rating:
    if score >= 1.5:
        return "Strong Buy / 強烈看多"
    if score >= 0.5:
        return "Buy / 看多"
    if score <= -1.5:
        return "Strong Sell / 強烈看空"
    if score <= -0.5:
        return "Sell / 看空"
    return "Neutral / 中性"


def score_from_total(total: float) -> float:
    return clamp_score((total - 50) / 25)


def clamp_score(value: float) -> float:
    return round(max(-2.0, min(2.0, value)), 2)


def risk_score_from_count(risk_count: int) -> float:
    if risk_count >= 7:
        return -1.5
    if risk_count >= 4:
        return -1.0
    if risk_count >= 2:
        return -0.5
    return 0.0


def bounded_confidence(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 2)


def unique_items(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            result.append(item)
            seen.add(item)
    return result
