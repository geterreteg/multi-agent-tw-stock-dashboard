from __future__ import annotations

from typing import Callable

from app.models import AgentInsight, DebateMessage, DecisionSummary, Rating
from app.services.market_data import fmt_number


def technical_agent(context) -> AgentInsight:
    reasons: list[str] = []
    risks: list[str] = []
    score = 0
    available = 0

    if context.latest_close is not None and context.ma20 is not None:
        available += 1
        if context.latest_close >= context.ma20:
            score += 1
            reasons.append("收盤價站上 MA20，短線價格結構偏強。")
        else:
            score -= 1
            risks.append("收盤價跌破 MA20，短線動能偏弱。")
    else:
        risks.append("收盤價或 MA20 資料不足，技術面判斷降級。")

    if context.ma20 is not None and context.ma60 is not None:
        available += 1
        if context.ma20 >= context.ma60:
            score += 1
            reasons.append("MA20 高於 MA60，中期趨勢仍有支撐。")
        else:
            score -= 1
            risks.append("MA20 低於 MA60，中期趨勢偏弱。")

    if context.return_20d is not None:
        available += 1
        if context.return_20d > 18:
            score -= 1
            risks.append("20 日報酬率過高，短線追價風險升高。")
        elif context.return_20d > 5:
            score += 1
            reasons.append("20 日報酬率為正且具動能。")
        elif context.return_20d < -5:
            score -= 1
            risks.append("20 日報酬率明顯轉弱。")

    if context.average_volume is not None and context.average_volume < 1_000_000:
        risks.append("近 20 日平均成交量偏低，流動性需要留意。")

    evidence = [
        f"最新收盤價：{fmt_number(context.latest_close)}",
        f"20 日報酬率：{fmt_number(context.return_20d, suffix='%')}",
        f"MA20：{fmt_number(context.ma20)}",
        f"MA60：{fmt_number(context.ma60)}",
        f"近 20 日平均成交量：{fmt_number(context.average_volume, decimals=0)}",
    ]
    degraded = any(
        value is None
        for value in [context.latest_close, context.return_20d, context.ma20, context.ma60, context.average_volume]
    )
    narrative = (
        f"技術面觀察最新收盤價 {fmt_number(context.latest_close)}，相較 MA20 {fmt_number(context.ma20)} "
        f"與 MA60 {fmt_number(context.ma60)} 用來判斷短中期趨勢位置；近 20 日報酬率為 "
        f"{fmt_number(context.return_20d, suffix='%')}，代表短線動能強弱；近 20 日平均成交量為 "
        f"{fmt_number(context.average_volume, decimals=0)}，用來檢查流動性是否足以支撐價格變化。"
    )

    if available == 0:
        return AgentInsight(
            name="技術分析 Agent",
            role="使用價格、報酬率、MA20、MA60 與成交量判斷趨勢",
            stance="中立",
            confidence=0.25,
            summary="資料不足，技術分析暫採中立。",
            narrative=narrative,
            evidence=evidence,
            degraded=True,
            reasons=["yfinance 價格或均線資料暫無。"],
            risks=risks or ["資料不足導致技術面可靠度下降。"],
        )

    stance = score_to_stance(score, bullish_threshold=2, bearish_threshold=-1)
    return AgentInsight(
        name="技術分析 Agent",
        role="使用價格、報酬率、MA20、MA60 與成交量判斷趨勢",
        stance=stance,
        confidence=bounded_confidence(0.42 + available * 0.13 + min(abs(score), 3) * 0.04),
        summary=(
            f"最新收盤 {fmt_number(context.latest_close)}，MA20 {fmt_number(context.ma20)}，"
            f"MA60 {fmt_number(context.ma60)}，20 日報酬 {fmt_number(context.return_20d, suffix='%')}。"
        ),
        narrative=narrative,
        evidence=evidence,
        degraded=degraded,
        reasons=reasons or ["技術指標未形成明確偏多訊號。"],
        risks=risks or ["未出現重大技術面風險，但仍需留意市場波動。"],
    )


def fundamental_agent(context) -> AgentInsight:
    reasons: list[str] = []
    risks: list[str] = []
    score = 0
    available = 0

    if context.revenue_growth is not None:
        available += 1
        if context.revenue_growth > 5:
            score += 1
            reasons.append("月營收年增率高於 5%，營運動能具支撐。")
        elif context.revenue_growth > 0:
            reasons.append("月營收年增率為正，但成長強度仍需追蹤。")
        else:
            score -= 1
            risks.append("月營收年增率不佳，營運動能偏保守。")
    else:
        risks.append("月營收成長資料不足。")

    if context.eps is not None:
        available += 1
        if context.eps > 3:
            score += 1
            reasons.append("EPS 表現具獲利支撐。")
        elif context.eps > 0:
            reasons.append("EPS 為正，具基本獲利能力。")
        else:
            score -= 1
            risks.append("EPS 偏弱或為負，基本面需保守解讀。")
    else:
        risks.append("EPS 資料不足。")

    if context.pe_ratio is not None:
        available += 1
        if context.pe_ratio >= 30:
            score -= 1
            risks.append("本益比偏高，評價可能已反映較多成長預期。")
        elif context.pe_ratio > 0:
            reasons.append("本益比資料可用，可作為評價面追蹤基準。")
    else:
        risks.append("本益比資料不足。")

    evidence = [
        f"EPS：{fmt_number(context.eps)}",
        f"本益比：{fmt_number(context.pe_ratio)}",
        f"月營收成長率：{fmt_number(context.revenue_growth, suffix='%')}",
    ]
    degraded = any(value is None for value in [context.eps, context.pe_ratio, context.revenue_growth])
    narrative = (
        f"基本面以 EPS {fmt_number(context.eps)} 檢查獲利能力，以本益比 {fmt_number(context.pe_ratio)} "
        f"觀察評價壓力，再用月營收成長率 {fmt_number(context.revenue_growth, suffix='%')} 判斷近期營運動能。"
        f"{'目前部分基本面資料暫無，因此結論需降級解讀。' if degraded else '目前三項基本面指標皆可用，能形成較完整的營運與評價觀察。'}"
    )

    if available == 0:
        return AgentInsight(
            name="基本面 Agent",
            role="使用 EPS、本益比與月營收成長檢查營運品質",
            stance="中立",
            confidence=0.22,
            summary="資料不足，基本面分析暫採中立。",
            narrative=narrative,
            evidence=evidence,
            degraded=True,
            reasons=["FinMind 基本面資料暫無。"],
            risks=risks or ["基本面資料不足導致可靠度下降。"],
        )

    stance = score_to_stance(score, bullish_threshold=2, bearish_threshold=-1)
    return AgentInsight(
        name="基本面 Agent",
        role="使用 EPS、本益比與月營收成長檢查營運品質",
        stance=stance,
        confidence=bounded_confidence(0.36 + available * 0.14 + min(abs(score), 3) * 0.04),
        summary=(
            f"EPS {fmt_number(context.eps)}，本益比 {fmt_number(context.pe_ratio)}，"
            f"月營收成長 {fmt_number(context.revenue_growth, suffix='%')}。"
        ),
        narrative=narrative,
        evidence=evidence,
        degraded=degraded,
        reasons=reasons or ["基本面資料未形成明確偏多訊號。"],
        risks=risks or ["未出現重大基本面風險，但需追蹤後續營收與財報。"],
    )


def chip_agent(context) -> AgentInsight:
    reasons: list[str] = []
    risks: list[str] = []
    score = 0
    available = 0

    if context.foreign_buy is not None:
        available += 1
        if context.foreign_buy > 0:
            score += 1
            reasons.append("外資最近一日呈現買超，籌碼面偏正向。")
        elif context.foreign_buy < 0:
            score -= 1
            risks.append("外資最近一日呈現賣超，籌碼面偏保守。")
    else:
        risks.append("外資買賣超資料不足。")

    if context.institutional_net_buy is not None:
        available += 1
        if context.institutional_net_buy > 0:
            score += 1
            reasons.append("三大法人合計偏買超，資金面具支撐。")
        elif context.institutional_net_buy < 0:
            score -= 1
            risks.append("三大法人合計偏賣超，需留意籌碼壓力。")

    if context.margin_balance_change is not None:
        available += 1
        if (
            context.margin_balance_change > 0
            and context.latest_close is not None
            and context.ma20 is not None
            and context.latest_close < context.ma20
        ):
            score -= 1
            risks.append("融資增加但股價跌破 MA20，可能代表追價後轉弱。")
        elif context.margin_balance_change < 0:
            reasons.append("融資餘額下降，槓桿籌碼壓力相對降低。")
    else:
        risks.append("融資融券資料不足，信用交易風險已降級。")

    evidence = [
        f"外資買賣超：{fmt_number(context.foreign_buy, decimals=0)}",
        f"三大法人合計：{fmt_number(context.institutional_net_buy, decimals=0)}",
        f"融資餘額變化：{fmt_number(context.margin_balance_change, decimals=0)}",
    ]
    degraded = any(
        value is None for value in [context.foreign_buy, context.institutional_net_buy, context.margin_balance_change]
    )
    narrative = (
        f"籌碼面觀察外資買賣超 {fmt_number(context.foreign_buy, decimals=0)}，用來判斷外資短線方向；"
        f"三大法人合計 {fmt_number(context.institutional_net_buy, decimals=0)} 可補充整體法人資金態度；"
        f"融資餘額變化 {fmt_number(context.margin_balance_change, decimals=0)} 用來檢查信用交易是否增加槓桿壓力。"
        f"{'目前籌碼或融資融券資料不完整，因此信心程度已下修。' if degraded else '目前主要籌碼指標皆可用。'}"
    )

    if available == 0:
        return AgentInsight(
            name="籌碼分析 Agent",
            role="使用外資買賣超、三大法人與融資融券觀察資金流向",
            stance="中立",
            confidence=0.22,
            summary="資料不足，籌碼分析暫採中立並標記降級。",
            narrative=narrative,
            evidence=evidence,
            degraded=True,
            reasons=["FinMind 法人或融資融券資料暫無。"],
            risks=risks or ["籌碼資料不足導致分析降級。"],
        )

    stance = score_to_stance(score, bullish_threshold=2, bearish_threshold=-1)
    return AgentInsight(
        name="籌碼分析 Agent",
        role="使用外資買賣超、三大法人與融資融券觀察資金流向",
        stance=stance,
        confidence=bounded_confidence(0.34 + available * 0.13 + min(abs(score), 3) * 0.04),
        summary=(
            f"外資買賣超 {fmt_number(context.foreign_buy, decimals=0)}，"
            f"三大法人合計 {fmt_number(context.institutional_net_buy, decimals=0)}，"
            f"融資餘額變化 {fmt_number(context.margin_balance_change, decimals=0)}。"
        ),
        narrative=narrative,
        evidence=evidence,
        degraded=degraded,
        reasons=reasons or ["籌碼資料未形成明確偏多訊號。"],
        risks=risks or ["未出現重大籌碼風險，但需追蹤法人連續買賣超。"],
    )


def risk_agent(context, prior_agents: list[AgentInsight]) -> AgentInsight:
    risks: list[str] = []
    for agent in prior_agents:
        risks.extend(agent.risks[:2])

    for status in context.source_status:
        if not status.ok:
            risks.append(status.message)
    risks.extend(context.finmind_errors[:3])

    if context.return_20d is not None and context.return_20d > 18:
        risks.append("短線漲幅過大時，回檔風險會高於一般情境。")
    if context.pe_ratio is not None and context.pe_ratio >= 30:
        risks.append("評價偏高時，任何營運不如預期都可能放大波動。")

    unique_risks = unique_items(risks) or ["未出現重大規則式風險，但資料可能延遲或不完整。"]
    stance: Rating = "偏空" if len(unique_risks) >= 3 else "中立"
    degraded = any(not status.ok for status in context.source_status)
    evidence = [
        f"風險項目數：{len(unique_risks)}",
        f"20 日報酬率：{fmt_number(context.return_20d, suffix='%')}",
        f"本益比：{fmt_number(context.pe_ratio)}",
        f"資料來源狀態：{'; '.join(status.message for status in context.source_status) or '資料暫無'}",
    ]
    narrative = (
        f"風險控管以反方角度檢查 {len(unique_risks)} 項風險。短線動能方面，20 日報酬率為 "
        f"{fmt_number(context.return_20d, suffix='%')}；評價面方面，本益比為 {fmt_number(context.pe_ratio)}。"
        f"若資料來源降級、短線漲幅過大、評價偏高或籌碼轉弱，結論就不宜只採用偏多訊號。"
    )
    return AgentInsight(
        name="風險控管 Agent",
        role="提出反方觀點，檢查趨勢、評價、籌碼與資料品質風險",
        stance=stance,
        confidence=0.68 if stance == "偏空" else 0.48,
        summary="反方檢查聚焦於資料缺漏、趨勢轉弱、評價偏高與籌碼壓力。",
        narrative=narrative,
        evidence=evidence,
        degraded=degraded,
        reasons=["風險控管 Agent 必須保留反方觀點，避免只看支持訊號。"],
        risks=unique_risks,
    )


def decision_agent(context, prior_agents: list[AgentInsight]) -> tuple[AgentInsight, DecisionSummary, Rating]:
    weighted_score = 0.0
    for agent in prior_agents:
        if agent.stance == "偏多":
            weighted_score += agent.confidence
        elif agent.stance == "偏空":
            weighted_score -= agent.confidence

    bullish_reasons = [
        reason
        for agent in prior_agents
        if agent.stance == "偏多"
        for reason in agent.reasons[:2]
    ]
    risk_items = unique_items([risk for agent in prior_agents for risk in agent.risks[:2]])
    watch_points = [
        "追蹤下一期月營收、法人買賣超與均線變化。",
        "確認 yfinance 與 FinMind 資料更新狀態。",
    ]
    if context.finmind_errors:
        watch_points.extend(context.finmind_errors[:3])

    if weighted_score >= 1.05:
        rating: Rating = "偏多"
    elif weighted_score <= -0.85:
        rating = "偏空"
    else:
        rating = "中立"

    confidence = bounded_confidence(0.42 + min(abs(weighted_score), 1.5) * 0.22)
    recommendation_text = (
        f"綜合判斷為「{rating}」。技術面目前參考收盤價 {fmt_number(context.latest_close)}、"
        f"MA20 {fmt_number(context.ma20)}、MA60 {fmt_number(context.ma60)} 與 20 日報酬率 "
        f"{fmt_number(context.return_20d, suffix='%')}；基本面參考 EPS {fmt_number(context.eps)}、"
        f"本益比 {fmt_number(context.pe_ratio)} 與月營收成長 {fmt_number(context.revenue_growth, suffix='%')}；"
        f"籌碼面參考外資買賣超 {fmt_number(context.foreign_buy, decimals=0)}、三大法人合計 "
        f"{fmt_number(context.institutional_net_buy, decimals=0)} 與融資餘額變化 "
        f"{fmt_number(context.margin_balance_change, decimals=0)}。建議後續觀察均線是否延續、"
        f"月營收與 EPS 是否改善，以及法人買賣超和融資變化是否支持目前方向；本系統不構成交易建議。"
    )
    decision = DecisionSummary(
        supportReasons=bullish_reasons or ["目前可用資料尚不足以形成明確偏多理由。"],
        risks=risk_items or ["未出現重大規則式風險，但仍需注意資料延遲與市場波動。"],
        watchPoints=unique_items(watch_points),
        recommendationText=recommendation_text,
    )
    evidence = [
        f"加權分數：{weighted_score:.2f}",
        f"技術面立場：{prior_agents[0].stance if len(prior_agents) > 0 else '資料暫無'}",
        f"基本面立場：{prior_agents[1].stance if len(prior_agents) > 1 else '資料暫無'}",
        f"籌碼面立場：{prior_agents[2].stance if len(prior_agents) > 2 else '資料暫無'}",
        f"風險控管立場：{prior_agents[3].stance if len(prior_agents) > 3 else '資料暫無'}",
    ]
    degraded = any(agent.degraded for agent in prior_agents)
    agent = AgentInsight(
        name="總結決策 Agent",
        role="整合技術、基本面、籌碼與風險控管觀點",
        stance=rating,
        confidence=confidence,
        summary=f"加權整合後的規則式結論為「{rating}」，不構成買賣建議。",
        narrative=recommendation_text,
        evidence=evidence,
        degraded=degraded,
        reasons=decision.supportReasons,
        risks=decision.risks,
    )
    return agent, decision, rating


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
        fallback = fallback_agent("總結決策 Agent", "總結決策失敗，已採中立。", exc)
        summary = DecisionSummary(
            supportReasons=["目前可用資料尚不足以形成明確偏多理由。"],
            risks=fallback.risks,
            watchPoints=["請稍後重試，或檢查資料來源與網路狀態。"],
            recommendationText="總結決策發生降級，目前僅能採中立觀察，請稍後重試或檢查資料來源。",
        )
        return fallback, summary, "中立"


def fallback_agent(name: str, message: str, exc: Exception) -> AgentInsight:
    return AgentInsight(
        name=name,
        role="規則式分析降級",
        stance="中立",
        confidence=0.12,
        summary=message,
        narrative=f"{name} 無法完成完整規則式分析，原因為 {type(exc).__name__}；目前以資料不足處理並採中立觀察。",
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
            message = f"整合前面觀點後，本次研究結論為「{rating}」。"
        elif agent.name == "風險控管 Agent":
            tone = "risk"
            message = "反方觀點：" + "；".join(agent.risks[:3])
        elif agent.stance == "偏空":
            tone = "risk"
            message = f"{agent.summary} 主要疑慮：" + "；".join(agent.risks[:2])
        elif agent.stance == "偏多":
            tone = "support"
            message = f"{agent.summary} 支持理由：" + "；".join(agent.reasons[:2])
        else:
            tone = "neutral"
            message = f"{agent.summary} 目前證據不足以明確偏多或偏空。"

        debate.append(
            DebateMessage(
                speaker=agent.name,
                stance=agent.stance,
                message=message,
                tone=tone,
            )
        )
    return debate


def score_to_stance(score: int, bullish_threshold: int, bearish_threshold: int) -> Rating:
    if score >= bullish_threshold:
        return "偏多"
    if score <= bearish_threshold:
        return "偏空"
    return "中立"


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
