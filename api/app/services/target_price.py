from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal, Optional


EpsBasis = Literal["FORWARD", "TTM", "FOUR_QUARTERS", "SINGLE_QUARTER", "UNAVAILABLE"]
PeSource = Literal["EXTERNAL", "DERIVED", "UNAVAILABLE"]
ValuationMethod = Literal["RULE_BASED_PE_MULTIPLE", "INSUFFICIENT_DATA"]

DISCLOSURE = (
    "本目標價採規則式 PE Multiple 法，以目前可驗證本益比作為 Base Case 估值基準，"
    "並以固定折溢價建立 Bear / Bull 情境。由於尚未納入歷史 PE 區間、同業估值、DCF "
    "與法人一致性預估，本目標價應視為估值參考區間，而非正式法人目標價。"
)


@dataclass(frozen=True)
class EpsEvidence:
    basis: EpsBasis
    value: Optional[float]
    source: str
    periods: tuple[str, ...] = ()


@dataclass(frozen=True)
class TargetPriceResult:
    currentPrice: Optional[int]
    baseTargetPrice: Optional[int]
    bearTargetPrice: Optional[int]
    bullTargetPrice: Optional[int]
    impliedUpsidePct: Optional[float]
    valuationMethod: ValuationMethod
    epsBasis: EpsBasis
    epsUsed: Optional[float]
    fairPERatio: Optional[float]
    bearPERatio: Optional[float]
    bullPERatio: Optional[float]
    confidence: int
    assumptions: list[str]
    limitations: list[str]
    peSource: PeSource


def build_target_price(
    current_price: Optional[float],
    eps: EpsEvidence,
    current_pe: Optional[float],
    pe_source: PeSource,
    has_valuation_gaps: bool = False,
) -> TargetPriceResult:
    limitations = _base_limitations()
    if eps.basis not in {"FORWARD", "TTM", "FOUR_QUARTERS"} or eps.value is None:
        reason = "目前只有單季 EPS，不得直接產生正式 12M 目標價。" if eps.basis == "SINGLE_QUARTER" else "缺少可驗證的 forward、TTM 或近四季 EPS。"
        return _insufficient(current_price, eps, current_pe, pe_source, reason)
    if eps.value <= 0:
        return _insufficient(current_price, eps, current_pe, pe_source, "EPS 非正值，不適用 PE Multiple 法。")
    if current_price is None or current_price <= 0:
        return _insufficient(current_price, eps, current_pe, pe_source, "缺少有效 current price，無法建立估值基準。")

    verified_pe = current_pe
    resolved_source = pe_source
    implied_pe = current_price / eps.value
    if pe_source == "EXTERNAL":
        if current_pe is None or current_pe <= 0:
            return _insufficient(current_price, eps, current_pe, pe_source, "外部 current PE 無效，無法建立估值基準。")
        relative_error = abs(current_pe - implied_pe) / implied_pe
        if relative_error > 0.10:
            return _insufficient(
                current_price,
                eps,
                current_pe,
                pe_source,
                "外部 current PE 與 current price / EPS 的口徑不一致，誤差超過 10%。",
            )
        confidence = 65
    else:
        verified_pe = implied_pe
        resolved_source = "DERIVED"
        confidence = 60
        limitations.append("current PE 僅由 current price / EPS 推導，沒有外部 PE 佐證，不構成獨立驗證。")

    if has_valuation_gaps:
        confidence = min(confidence, 50)
        limitations.append("其他估值資料缺口會限制此區間的解讀，confidence 上限為 50。")

    base_pe = float(verified_pe)
    bear_pe = base_pe * 0.90
    bull_pe = base_pe * 1.10
    base_target = eps.value * base_pe
    bear_target = eps.value * bear_pe
    bull_target = eps.value * bull_pe
    implied_upside = ((base_target / current_price) - 1) * 100

    return TargetPriceResult(
        currentPrice=_round_price(current_price),
        baseTargetPrice=_round_price(base_target),
        bearTargetPrice=_round_price(bear_target),
        bullTargetPrice=_round_price(bull_target),
        impliedUpsidePct=round(implied_upside, 1),
        valuationMethod="RULE_BASED_PE_MULTIPLE",
        epsBasis=eps.basis,
        epsUsed=round(eps.value, 4),
        fairPERatio=round(base_pe, 2),
        bearPERatio=round(bear_pe, 2),
        bullPERatio=round(bull_pe, 2),
        confidence=confidence,
        assumptions=[
            f"EPS 使用 {eps.basis} 口徑，來源：{eps.source}。",
            "basePERatio = currentPE；bearPERatio = currentPE * 0.90；bullPERatio = currentPE * 1.10。",
            DISCLOSURE,
        ],
        limitations=limitations,
        peSource=resolved_source,
    )


def _insufficient(
    current_price: Optional[float],
    eps: EpsEvidence,
    current_pe: Optional[float],
    pe_source: PeSource,
    reason: str,
) -> TargetPriceResult:
    valid_pe = current_pe if current_pe is not None and current_pe > 0 else None
    return TargetPriceResult(
        currentPrice=_round_price(current_price) if current_price is not None and current_price > 0 else None,
        baseTargetPrice=None,
        bearTargetPrice=None,
        bullTargetPrice=None,
        impliedUpsidePct=None,
        valuationMethod="INSUFFICIENT_DATA",
        epsBasis=eps.basis,
        epsUsed=round(eps.value, 4) if eps.value is not None else None,
        fairPERatio=round(valid_pe, 2) if valid_pe is not None else None,
        bearPERatio=None,
        bullPERatio=None,
        confidence=0,
        assumptions=[DISCLOSURE],
        limitations=[reason, *_base_limitations()],
        peSource=pe_source,
    )


def _base_limitations() -> list[str]:
    return ["尚未納入歷史 PE 區間、同業 PE、DCF 與法人一致性預估。"]


def _round_price(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
