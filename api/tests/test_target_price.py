from __future__ import annotations

import unittest
from dataclasses import fields
from types import SimpleNamespace

import pandas as pd
from pydantic import ValidationError

from app import models
from app.services.agents import build_investment_committee_debate, build_recommendation_text
from app.services.analysis import historical_pe_to_model
from app.services.market_data import summarize_financials
from app.services.pe_history import HistoricalPEResult
from app.services.reports import generate_markdown_report
from app.services.target_price import EpsEvidence, TargetPriceResult, build_target_price


class TargetPriceEngineTests(unittest.TestCase):
    def test_historical_pe_builds_range_for_ttm_eps(self) -> None:
        for basis in ("TTM", "TTM_EPS"):
            with self.subTest(basis=basis):
                result = build_target_price(
                    current_price=100,
                    eps=EpsEvidence(basis=basis, value=5, source="FinMind TTM EPS"),
                    current_pe=40,
                    pe_source="EXTERNAL",
                    historical_pe=_historical_pe(15, 20, 25, sample_count=36),
                )

                self.assertEqual("RULE_BASED_PE_MULTIPLE", result.valuationMethod)
                self.assertEqual(75, result.bearTargetPrice)
                self.assertEqual(100, result.baseTargetPrice)
                self.assertEqual(125, result.bullTargetPrice)
                self.assertEqual(15, result.bearPERatio)
                self.assertEqual(20, result.fairPERatio)
                self.assertEqual(25, result.bullPERatio)
                self.assertEqual("HISTORICAL_TWSE", result.peSource)
                self.assertTrue(any("已納入 TWSE 歷史 PE" in item for item in result.limitations))
                self.assertTrue(any("尚未納入 TPEx" in item for item in result.limitations))

    def test_insufficient_historical_pe_falls_back_to_current_pe(self) -> None:
        result = build_target_price(
            current_price=100,
            eps=EpsEvidence(basis="TTM", value=5, source="FinMind TTM EPS"),
            current_pe=20,
            pe_source="EXTERNAL",
            historical_pe=_historical_pe(15, 20, 25, sample_count=11),
        )

        self.assertEqual(90, result.bearTargetPrice)
        self.assertEqual(100, result.baseTargetPrice)
        self.assertEqual(110, result.bullTargetPrice)
        self.assertEqual("EXTERNAL", result.peSource)

    def test_external_pe_builds_rule_based_range(self) -> None:
        result = build_target_price(
            current_price=100,
            eps=EpsEvidence(basis="TTM", value=5, source="FinMind TTM EPS"),
            current_pe=20,
            pe_source="EXTERNAL",
        )

        self.assertEqual("RULE_BASED_PE_MULTIPLE", result.valuationMethod)
        self.assertEqual(100, result.currentPrice)
        self.assertEqual(90, result.bearTargetPrice)
        self.assertEqual(100, result.baseTargetPrice)
        self.assertEqual(110, result.bullTargetPrice)
        self.assertEqual(0.0, result.impliedUpsidePct)
        self.assertEqual(20.0, result.fairPERatio)
        self.assertEqual(18.0, result.bearPERatio)
        self.assertEqual(22.0, result.bullPERatio)
        self.assertEqual(65, result.confidence)
        self.assertEqual("EXTERNAL", result.peSource)

    def test_single_quarter_eps_is_insufficient(self) -> None:
        result = build_target_price(
            current_price=100,
            eps=EpsEvidence(basis="SINGLE_QUARTER", value=2, source="FinMind single-quarter EPS"),
            current_pe=20,
            pe_source="EXTERNAL",
            historical_pe=_historical_pe(15, 20, 25, sample_count=36),
        )

        self.assertEqual("INSUFFICIENT_DATA", result.valuationMethod)
        self.assertIsNone(result.baseTargetPrice)
        self.assertEqual(0, result.confidence)
        self.assertTrue(any("單季 EPS" in item for item in result.limitations))
        self.assertTrue(any("歷史 PE 已有 36 筆" in item for item in result.limitations))
        self.assertFalse(any("樣本不足 12 筆" in item for item in result.limitations))

    def test_external_pe_mismatch_is_insufficient(self) -> None:
        result = build_target_price(
            current_price=100,
            eps=EpsEvidence(basis="TTM", value=5, source="FinMind TTM EPS"),
            current_pe=30,
            pe_source="EXTERNAL",
        )

        self.assertEqual("INSUFFICIENT_DATA", result.valuationMethod)
        self.assertTrue(any("口徑不一致" in item for item in result.limitations))

    def test_missing_historical_and_current_pe_is_insufficient(self) -> None:
        result = build_target_price(
            current_price=100,
            eps=EpsEvidence(basis="FOUR_QUARTERS", value=5, source="FinMind quarterly EPS"),
            current_pe=None,
            pe_source="UNAVAILABLE",
        )

        self.assertEqual("INSUFFICIENT_DATA", result.valuationMethod)
        self.assertIsNone(result.baseTargetPrice)
        self.assertIsNone(result.bearTargetPrice)
        self.assertIsNone(result.bullTargetPrice)
        self.assertTrue(any("current PE" in item for item in result.limitations))

    def test_valuation_gaps_cap_confidence_at_50(self) -> None:
        result = build_target_price(
            current_price=100,
            eps=EpsEvidence(basis="FORWARD", value=5, source="verified forward EPS"),
            current_pe=20,
            pe_source="EXTERNAL",
            has_valuation_gaps=True,
        )

        self.assertEqual(50, result.confidence)

    def test_non_positive_eps_is_insufficient(self) -> None:
        result = build_target_price(
            current_price=100,
            eps=EpsEvidence(basis="TTM", value=-1, source="FinMind TTM EPS"),
            current_pe=20,
            pe_source="EXTERNAL",
        )

        self.assertEqual("INSUFFICIENT_DATA", result.valuationMethod)
        self.assertIsNone(result.baseTargetPrice)


class FinancialSummaryTests(unittest.TestCase):
    def test_explicit_ttm_eps_has_verified_basis(self) -> None:
        frame = pd.DataFrame([{"date": "2026-03-31", "type": "TTM EPS", "value": 10.25}])

        result = summarize_financials(frame)

        self.assertEqual("TTM", result.basis)
        self.assertEqual(10.25, result.value)

    def test_four_explicit_quarter_eps_values_are_summed(self) -> None:
        frame = pd.DataFrame(
            [
                {"date": "2025-06-30", "type": "Quarterly EPS", "value": 2.0},
                {"date": "2025-09-30", "type": "Quarterly EPS", "value": 2.5},
                {"date": "2025-12-31", "type": "Quarterly EPS", "value": 3.0},
                {"date": "2026-03-31", "type": "Quarterly EPS", "value": 3.5},
            ]
        )

        result = summarize_financials(frame)

        self.assertEqual("FOUR_QUARTERS", result.basis)
        self.assertEqual(11.0, result.value)
        self.assertEqual(4, len(result.periods))

    def test_generic_eps_is_single_quarter_not_ttm(self) -> None:
        frame = pd.DataFrame([{"date": "2026-03-31", "type": "EPS", "value": 3.5}])

        result = summarize_financials(frame)

        self.assertEqual("SINGLE_QUARTER", result.basis)
        self.assertEqual(3.5, result.value)

    def test_unlabelled_value_is_not_treated_as_eps(self) -> None:
        frame = pd.DataFrame([{"date": "2026-03-31", "type": "Revenue", "value": 5000}])

        result = summarize_financials(frame)

        self.assertEqual("UNAVAILABLE", result.basis)
        self.assertIsNone(result.value)


class TargetPriceApiTests(unittest.TestCase):
    def test_api_model_exposes_complete_target_price_contract(self) -> None:
        target_model = getattr(models, "TargetPrice", None)

        self.assertIsNotNone(target_model)
        field_names = set(target_model.model_fields)
        self.assertTrue(
            {
                "currentPrice",
                "baseTargetPrice",
                "bearTargetPrice",
                "bullTargetPrice",
                "impliedUpsidePct",
                "valuationMethod",
                "epsBasis",
                "epsUsed",
                "fairPERatio",
                "bearPERatio",
                "bullPERatio",
                "confidence",
                "assumptions",
                "limitations",
                "peSource",
            }.issubset(field_names)
        )

    def test_api_model_exposes_historical_pe_contract(self) -> None:
        historical_model = getattr(models, "HistoricalPE", None)

        self.assertIsNotNone(historical_model)
        self.assertTrue(
            {
                "minPE",
                "p25PE",
                "medianPE",
                "p75PE",
                "maxPE",
                "validSampleCount",
                "source",
                "cacheStatus",
                "dataLimitations",
            }.issubset(set(historical_model.model_fields))
        )
        self.assertIn("historicalPE", models.AnalyzeResponse.model_fields)

    def test_dataclass_and_pydantic_contracts_match_exactly(self) -> None:
        target_fields = {item.name for item in fields(TargetPriceResult)}
        historical_fields = {item.name for item in fields(HistoricalPEResult)} - {"symbol", "samples"}

        self.assertEqual(target_fields, set(models.TargetPrice.model_fields))
        self.assertEqual(historical_fields, set(models.HistoricalPE.model_fields))
        converted = historical_pe_to_model(_historical_pe(15, 20, 25, sample_count=36))
        self.assertEqual(36, converted.validSampleCount)
        self.assertEqual(20, converted.medianPE)

    def test_contract_models_reject_unknown_fields_instead_of_ignoring_them(self) -> None:
        self.assertEqual("forbid", models.AnalyzeResponse.model_config.get("extra"))
        with self.assertRaises(ValidationError):
            models.TargetPrice(unexpectedField=1)
        with self.assertRaises(ValidationError):
            models.HistoricalPE(historicalPeMedian=20)
        with self.assertRaises(ValidationError):
            models.HistoricalPE(peHistory={})

    def test_insufficient_target_price_does_not_change_rating(self) -> None:
        context = _report_context(eps=2, pe_ratio=20)
        target_price = build_target_price(
            current_price=100,
            eps=EpsEvidence("SINGLE_QUARTER", 2, "FinMind latest reported EPS"),
            current_pe=20,
            pe_source="EXTERNAL",
        )
        agents = [_agent("技術分析 Agent", "Buy / 看多", ["收盤價高於 MA20"])]

        debate = build_investment_committee_debate(
            context=context,
            agents=agents,
            rating="Buy / 看多",
            research=_research("Buy / 看多"),
            target_price=target_price,
        )

        self.assertEqual("INSUFFICIENT_DATA", target_price.valuationMethod)
        self.assertEqual("Buy / 看多", debate[-1].stance)
        self.assertTrue(any("資料不足" in item.message for item in debate))


class TargetPriceReportTests(unittest.TestCase):
    def test_recommendation_text_reports_actual_historical_pe_scope(self) -> None:
        context = _report_context(eps=5, pe_ratio=20)
        context.historical_pe = _historical_pe(15, 20, 25, sample_count=36)

        text = build_recommendation_text(context, _research("Buy / 看多"), 60)

        self.assertIn("已取得 TWSE 歷史 PE", text)
        self.assertIn("尚未納入 TPEx", text)
        self.assertNotIn("尚未納入歷史 PE", text)
    def test_report_uses_institutional_structure_and_rule_based_disclosure(self) -> None:
        context = _report_context(eps=5, pe_ratio=20)
        target_price = build_target_price(
            current_price=100,
            eps=EpsEvidence("TTM", 5, "FinMind TTM EPS"),
            current_pe=20,
            pe_source="EXTERNAL",
        )
        decision = _decision("Buy / 看多")

        report = generate_markdown_report(
            context,
            [],
            "Buy / 看多",
            decision,
            target_price=target_price,
        )

        self.assertIn("### 結論", report)
        self.assertIn("### 依據", report)
        self.assertIn("### 風險", report)
        self.assertIn("### 資料限制", report)
        self.assertIn("Bear：90", report)
        self.assertIn("Base：100", report)
        self.assertIn("Bull：110", report)
        self.assertIn("目前 PE：20.0", report)
        self.assertIn("最新收盤價：100\n", report)
        self.assertNotIn("最新收盤價：100.00", report)
        self.assertIn("規則式估值區間採 PE Multiple 法", report)
        self.assertIn("僅為規則式估值參考", report)

    def test_insufficient_report_has_no_invented_target_price(self) -> None:
        context = _report_context(eps=2, pe_ratio=20)
        target_price = build_target_price(
            current_price=100,
            eps=EpsEvidence("SINGLE_QUARTER", 2, "FinMind latest reported EPS"),
            current_pe=20,
            pe_source="EXTERNAL",
        )

        report = generate_markdown_report(
            context,
            [],
            "Neutral / 中性",
            _decision("Neutral / 中性"),
            target_price=target_price,
        )

        self.assertIn("資料不足，暫不產生規則式估值區間", report)
        self.assertNotIn("Bear：", report)


def _agent(name: str, stance: str, evidence: list[str]):
    return SimpleNamespace(
        name=name,
        role=name,
        stance=stance,
        score=1,
        confidence=0.6,
        summary="規則式分析摘要",
        narrative="規則式分析內容",
        evidence=evidence,
        degraded=False,
        reasons=evidence,
        risks=["資料可能延遲"],
    )


def _historical_pe(p25: float, median: float, p75: float, sample_count: int) -> HistoricalPEResult:
    return HistoricalPEResult(
        symbol="2330",
        minPE=10,
        p25PE=p25,
        medianPE=median,
        p75PE=p75,
        maxPE=30,
        validSampleCount=sample_count,
        source="TWSE 個股日本益比、殖利率及股價淨值比",
        cacheStatus="live",
        dataLimitations=[],
        samples=[],
    )


def _research(rating: str):
    return SimpleNamespace(
        investmentThesis=["趨勢與基本面提供支持"],
        keyMetrics=["收盤價 100", "MA20 90"],
        businessQuality=["營收維持正成長"],
        financialAnalysis=["TTM EPS 5"],
        valuation=["規則式估值參考"],
        catalysts=["營收延續"],
        risks=["估值收縮風險"],
        variantView=["成長不如預期時需下修"],
        recommendation=rating,
        confidenceScore=60,
        dataGaps=["缺少同業 PE"],
        scoreBreakdown={},
    )


def _decision(rating: str):
    return SimpleNamespace(
        supportReasons=["趨勢與基本面提供支持"],
        risks=["估值收縮風險"],
        watchPoints=["追蹤營收"],
        recommendationText="結論：維持審慎評估。",
        finalScore=60,
        scoreBreakdown={},
        researchReport=_research(rating),
    )


def _report_context(eps: float, pe_ratio: float):
    return SimpleNamespace(
        stock_id="2330",
        stock_name="台積電",
        industry="半導體",
        last_updated="2026-06-19 12:00:00",
        latest_close=100,
        ma20=90,
        ma60=80,
        return_20d=5,
        average_volume=1000,
        revenue_growth=10,
        latest_revenue=10000,
        eps=eps,
        pe_ratio=pe_ratio,
        foreign_buy=100,
        institutional_net_buy=200,
        margin_balance_change=-30,
        short_balance_change=5,
        dividend_summary="資料暫無",
        source_status=[],
        finmind_errors=[],
        institutional_source="TWSE 三大法人買賣超日報",
        institutional_status="latest_available",
        institutional_data_date="2026-06-18",
        margin_source="TWSE 融資融券餘額",
        margin_status="latest_available",
        margin_data_date="2026-06-18",
    )


if __name__ == "__main__":
    unittest.main()
