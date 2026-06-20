from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal, Optional

from app.services.pe_history import HistoricalPEResult


EpsBasis = Literal["FORWARD", "TTM", "TTM_EPS", "FOUR_QUARTERS", "SINGLE_QUARTER", "UNAVAILABLE"]
PeSource = Literal["HISTORICAL_TWSE", "EXTERNAL", "DERIVED", "UNAVAILABLE"]
ValuationMethod = Literal["RULE_BASED_PE_MULTIPLE", "INSUFFICIENT_DATA"]

DISCLOSURE = (
    "本規則式估值區間採 PE Multiple 法：TTM EPS 且歷史 PE 樣本足夠時，"
    "使用 p25 / median / p75 建立 Bear / Base / Bull；樣本不足時才以 currentPE 固定折溢價降級。"
    "本結果僅為規則式估值參考，不構成買賣建議。"
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
    historical_pe: HistoricalPEResult | None = None,
) -> TargetPriceResult:
    historical_available = (
        eps.basis in {"TTM", "TTM_EPS"}
        and historical_pe is not None
        and historical_pe.validSampleCount >= 12
        and all(value is not None and value > 0 for value in (historical_pe.p25PE, historical_pe.medianPE, historical_pe.p75PE))
    )
    limitations = _base_limitations(historical_available, historical_pe, eps.basis)
    if eps.basis not in {"FORWARD", "TTM", "TTM_EPS", "FOUR_QUARTERS"} or eps.value is None:
        reason = "目前只有單季 EPS，不得直接產生規則式估值區間。" if eps.basis == "SINGLE_QUARTER" else "缺少可驗證的 forward、TTM 或近四季 EPS。"
        return _insufficient(current_price, eps, current_pe, pe_source, reason, historical_pe)
    if eps.value <= 0:
        return _insufficient(current_price, eps, current_pe, pe_source, "EPS 非正值，不適用 PE Multiple 法。", historical_pe)
    if current_price is None or current_price <= 0:
        return _insufficient(current_price, eps, current_pe, pe_source, "缺少有效 current price，無法建立估值基準。", historical_pe)

    if historical_available:
        bear_pe = float(historical_pe.p25PE)
        base_pe = float(historical_pe.medianPE)
        bull_pe = float(historical_pe.p75PE)
        resolved_source: PeSource = "HISTORICAL_TWSE"
        confidence = 65
    elif current_pe is not None and current_pe > 0:
        implied_pe = current_price / eps.value
        if pe_source == "EXTERNAL" and abs(current_pe - implied_pe) / implied_pe > 0.10:
            return _insufficient(
                current_price,
                eps,
                current_pe,
                pe_source,
                "外部 current PE 與 current price / EPS 的口徑不一致，誤差超過 10%。",
                historical_pe,
            )
        base_pe = float(current_pe)
        bear_pe = base_pe * 0.90
        bull_pe = base_pe * 1.10
        resolved_source = pe_source
        confidence = 65 if pe_source == "EXTERNAL" else 60
    else:
        return _insufficient(current_price, eps, current_pe, pe_source, "歷史 PE 有效樣本不足 12 筆，且缺少可用 current PE。", historical_pe)

    if has_valuation_gaps:
        confidence = min(confidence, 50)
        limitations.append("其他估值資料缺口會限制此區間的解讀，confidence 上限為 50。")

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
        assumptions=[f"EPS 使用 {eps.basis} 口徑，來源：{eps.source}。", *_pe_assumptions(historical_available, historical_pe), DISCLOSURE],
        limitations=limitations,
        peSource=resolved_source,
    )


def _insufficient(
    current_price: Optional[float],
    eps: EpsEvidence,
    current_pe: Optional[float],
    pe_source: PeSource,
    reason: str,
    historical_pe: HistoricalPEResult | None = None,
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
        limitations=[reason, *_base_limitations(False, historical_pe, eps.basis)],
        peSource=pe_source,
    )


def _base_limitations(
    historical_available: bool = False,
    historical_pe: HistoricalPEResult | None = None,
    eps_basis: EpsBasis | None = None,
) -> list[str]:
    limitations: list[str] = []
    if not historical_available:
        if historical_pe is not None and historical_pe.validSampleCount >= 12 and eps_basis not in {"TTM", "TTM_EPS"}:
            limitations.insert(0, f"歷史 PE 已有 {historical_pe.validSampleCount} 筆有效樣本，但 EPS basis 非 TTM，本次不得用於估值情境。")
        else:
            limitations.insert(0, "歷史 PE 有效樣本不足 12 筆，本次未用於估值情境。")
    if historical_available:
        limitations.append("已納入 TWSE 歷史 PE；尚未納入 TPEx、同業 PE、DCF、法人一致性預估。")
    elif historical_pe is not None and historical_pe.validSampleCount > 0:
        limitations.append("已取得 TWSE 歷史 PE，但本次未套用於估值情境；尚未納入 TPEx、同業 PE、DCF、法人一致性預估。")
    else:
        limitations.append("本次未取得可用 TWSE 歷史 PE；尚未納入 TPEx、同業 PE、DCF、法人一致性預估。")
    return limitations


def _pe_assumptions(historical_available: bool, historical_pe: HistoricalPEResult | None) -> list[str]:
    if historical_available and historical_pe is not None:
        return [
            f"Bear / Base / Bull PE 分別使用 TWSE 歷史 PE 的 p25 / median / p75，有效樣本 {historical_pe.validSampleCount} 筆。"
        ]
    return ["historicalPE 不足時，Bear / Base / Bull PE 使用 currentPE * 0.90 / currentPE / currentPE * 1.10。"]


def _round_price(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
