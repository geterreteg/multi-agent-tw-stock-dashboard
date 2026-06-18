from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd


API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services import analysis, institutional_data, margin_data, market_data, mock_data
from app.services.agents import chip_agent, score_risk_control
from app.services.reports import generate_markdown_report


def institutional_result(data_date: str | None = None, available: bool = True) -> dict:
    return {
        "symbol": "2330",
        "asOfDate": data_date,
        "dataDate": data_date,
        "status": "current" if available else "missing",
        "foreignNetBuy": 100 if available else None,
        "investmentTrustNetBuy": 20 if available else None,
        "dealerNetBuy": -10 if available else None,
        "institutionalNetBuyTotal": 110 if available else None,
        "source": "TWSE 三大法人買賣超日報",
        "dataGaps": [] if available else [{"code": "symbol_not_found", "message": "查無資料"}],
    }


def margin_result(data_date: str | None = None, available: bool = True) -> dict:
    return {
        "symbol": "2330",
        "asOfDate": data_date,
        "dataDate": data_date,
        "status": "current" if available else "missing",
        "marginBalance": 1000 if available else None,
        "marginChange": -30 if available else None,
        "shortBalance": 50 if available else None,
        "shortChange": 5 if available else None,
        "marginUtilizationRate": 10.0 if available else None,
        "shortUtilizationRate": 2.0 if available else None,
        "source": "TWSE 融資融券餘額",
        "dataGaps": [] if available else [{"code": "symbol_not_found", "message": "查無資料"}],
    }


class InstitutionalFallbackTests(unittest.TestCase):
    @patch("app.services.institutional_data.fetch_twse_institutional_data")
    def test_current_when_requested_trading_day_is_available(self, fetch) -> None:
        fetch.return_value = institutional_result("2026-06-18")

        result = institutional_data.get_institutional_data("2330", market="TWSE", date="2026-06-18")

        self.assertEqual(result["status"], "current")
        self.assertEqual(result["dataDate"], "2026-06-18")
        fetch.assert_called_once_with("2330", "2026-06-18")

    @patch("app.services.institutional_data.fetch_twse_institutional_data")
    def test_uses_latest_available_prior_trading_day(self, fetch) -> None:
        fetch.side_effect = [
            institutional_result(available=False),
            institutional_result("2026-06-17"),
        ]

        result = institutional_data.get_institutional_data("2330", market="TWSE", date="2026-06-18")

        self.assertEqual(result["status"], "latest_available")
        self.assertEqual(result["dataDate"], "2026-06-17")
        self.assertEqual([call.args[1] for call in fetch.call_args_list], ["2026-06-18", "2026-06-17"])

    @patch("app.services.institutional_data.fetch_twse_institutional_data")
    def test_missing_only_after_five_candidate_trading_days(self, fetch) -> None:
        fetch.return_value = institutional_result(available=False)

        result = institutional_data.get_institutional_data("2330", market="TWSE", date="2026-06-18")

        self.assertEqual(result["status"], "missing")
        self.assertIsNone(result["dataDate"])
        self.assertEqual(
            [call.args[1] for call in fetch.call_args_list],
            ["2026-06-18", "2026-06-17", "2026-06-16", "2026-06-15", "2026-06-12"],
        )


class MarginStatusTests(unittest.TestCase):
    @patch("app.services.margin_data.request_json")
    def test_twse_historical_response_preserves_date_and_balances(self, request_json) -> None:
        request_json.return_value = {
            "stat": "OK",
            "date": "20260617",
            "tables": [
                {
                    "fields": [
                        "代號", "名稱", "融資買進", "融資賣出", "現金償還", "融資前日餘額",
                        "融資今日餘額", "融資限額", "融券買進", "融券賣出", "現券償還", "融券前日餘額",
                        "融券今日餘額", "融券限額",
                    ],
                    "data": [["2330", "台積電", "10", "20", "0", "1,030", "1,000", "10,000", "5", "2", "0", "45", "50", "2,500"]],
                }
            ],
        }

        result = margin_data.fetch_twse_margin_data("2330", "2026-06-17")

        self.assertIsNotNone(result["marginBalance"])
        self.assertEqual(result["dataDate"], "2026-06-17")
        self.assertEqual(result["marginChange"], -30)
        self.assertEqual(result["shortChange"], 5)
        self.assertEqual(result["marginUtilizationRate"], 10.0)

    @patch("app.services.margin_data.fetch_twse_margin_data")
    def test_twse_uses_latest_available_prior_trading_day(self, fetch) -> None:
        fetch.side_effect = [
            margin_result(available=False),
            margin_result("2026-06-17"),
        ]

        result = margin_data.get_margin_data("2330", market="TWSE", date="2026-06-18")

        self.assertEqual(result["status"], "latest_available")
        self.assertEqual(result["dataDate"], "2026-06-17")
        self.assertEqual([call.args[1] for call in fetch.call_args_list], ["2026-06-18", "2026-06-17"])

    @patch("app.services.margin_data.fetch_tpex_margin_data")
    def test_latest_endpoint_date_is_classified_against_requested_day(self, fetch) -> None:
        fetch.return_value = margin_result("2026-06-17")

        result = margin_data.get_margin_data("2330", market="TPEX", date="2026-06-18")

        self.assertEqual(result["status"], "latest_available")
        self.assertEqual(result["dataDate"], "2026-06-17")


class OfficialChipSelectionTests(unittest.TestCase):
    @patch("app.services.market_data.fetch_finmind_dataset")
    def test_finmind_chip_datasets_are_legacy_not_active_sources(self, fetch) -> None:
        fetch.return_value = (pd.DataFrame(), "")

        market_data.fetch_finmind_bundle("2330", "", market_data.FINMIND_TOKEN_PUBLIC_MESSAGE)

        requested_datasets = {call.args[0] for call in fetch.call_args_list}
        self.assertNotIn("TaiwanStockInstitutionalInvestorsBuySell", requested_datasets)
        self.assertNotIn("TaiwanStockMarginPurchaseShortSale", requested_datasets)

    def test_context_metrics_are_selected_from_official_chip_data(self) -> None:
        chip_data = {
            "institutional": institutional_result("2026-06-18"),
            "margin": margin_result("2026-06-18"),
            "dataGaps": [],
        }

        selected = analysis.chip_metrics_from_data(chip_data)

        self.assertEqual(selected["foreign_buy"], 100)
        self.assertEqual(selected["institutional_net_buy"], 110)
        self.assertEqual(selected["margin_balance_change"], -30)
        self.assertEqual(selected["institutional_source"], "TWSE 三大法人買賣超日報")
        self.assertEqual(selected["institutional_data_date"], "2026-06-18")

    def test_missing_status_never_exposes_stale_chip_values(self) -> None:
        stale_institutional = institutional_result("2026-06-10")
        stale_institutional["status"] = "missing"
        stale_margin = margin_result("2026-06-10")
        stale_margin["status"] = "missing"

        selected = analysis.chip_metrics_from_data(
            {"institutional": stale_institutional, "margin": stale_margin, "dataGaps": []}
        )

        self.assertIsNone(selected["foreign_buy"])
        self.assertIsNone(selected["institutional_net_buy"])
        self.assertIsNone(selected["margin_balance_change"])

    @patch("app.services.analysis.get_margin_data")
    @patch("app.services.analysis.get_institutional_data")
    def test_chip_data_overall_status_follows_backend_contract(self, get_institutional, get_margin) -> None:
        cases = [
            ("current", "current", "current"),
            ("latest_available", "current", "latest_available"),
            ("current", "missing", "partial"),
            ("missing", "missing", "missing"),
        ]

        for institutional_status, margin_status, expected in cases:
            with self.subTest(institutional=institutional_status, margin=margin_status):
                institutional = institutional_result("2026-06-18", institutional_status != "missing")
                institutional["status"] = institutional_status
                margin = margin_result("2026-06-18", margin_status != "missing")
                margin["status"] = margin_status
                get_institutional.return_value = institutional
                get_margin.return_value = margin

                chip_data = analysis.build_chip_data("2330", "TWSE")
                model = analysis.chip_data_to_model(chip_data)

                self.assertEqual(chip_data["overallStatus"], expected)
                self.assertEqual(model.overallStatus, expected)

    def test_risk_control_margin_penalty_uses_status_weight(self) -> None:
        base = {
            "return_20d": None,
            "pe_ratio": None,
            "margin_balance_change": 10,
            "latest_close": 90,
            "ma20": 100,
        }

        current = score_risk_control(SimpleNamespace(**base, margin_status="current"), [], [])
        latest = score_risk_control(SimpleNamespace(**base, margin_status="latest_available"), [], [])
        missing = score_risk_control(SimpleNamespace(**base, margin_status="missing"), [], [])

        self.assertEqual(current, 17.0)
        self.assertEqual(latest, 17.75)
        self.assertEqual(missing, 20.0)

    def test_chip_score_distinguishes_current_latest_available_and_missing(self) -> None:
        base = {
            "foreign_buy": 100,
            "institutional_net_buy": 110,
            "margin_balance_change": -30,
            "short_balance_change": 5,
            "latest_close": 100,
            "ma20": 90,
            "institutional_source": "TWSE 三大法人買賣超日報",
            "institutional_data_date": "2026-06-18",
            "margin_source": "TWSE 融資融券餘額",
            "margin_data_date": "2026-06-18",
        }
        current = chip_agent(SimpleNamespace(**base, institutional_status="current", margin_status="current"))
        latest = chip_agent(
            SimpleNamespace(**base, institutional_status="latest_available", margin_status="latest_available")
        )
        missing_values = {
            **base,
            "foreign_buy": None,
            "institutional_net_buy": None,
            "margin_balance_change": None,
            "short_balance_change": None,
            "institutional_data_date": None,
            "margin_data_date": None,
        }
        missing = chip_agent(
            SimpleNamespace(**missing_values, institutional_status="missing", margin_status="missing")
        )

        self.assertGreater(current.score, latest.score)
        self.assertGreater(latest.score, missing.score)
        self.assertFalse(current.degraded)
        self.assertTrue(latest.degraded)
        self.assertTrue(missing.degraded)

    def test_report_preserves_chip_source_status_and_data_date(self) -> None:
        context = SimpleNamespace(
            stock_id="2330",
            stock_name="台積電",
            industry="半導體",
            last_updated="2026-06-18 12:00:00",
            latest_close=100,
            ma20=90,
            ma60=80,
            return_20d=5,
            average_volume=1000,
            revenue_growth=10,
            eps=5,
            pe_ratio=20,
            foreign_buy=100,
            margin_balance_change=-30,
            dividend_summary="資料暫無",
            source_status=[],
            finmind_errors=[],
            institutional_source="TWSE 三大法人買賣超日報",
            institutional_status="latest_available",
            institutional_data_date="2026-06-17",
            margin_source="TWSE 融資融券餘額",
            margin_status="current",
            margin_data_date="2026-06-18",
        )
        research = SimpleNamespace(
            investmentThesis=[], keyMetrics=[], businessQuality=[], financialAnalysis=[], valuation=[], catalysts=[],
            risks=[], variantView=[], recommendation="Neutral / 中性", confidenceScore=50, scoreBreakdown={}, dataGaps=[]
        )
        decision = SimpleNamespace(
            supportReasons=[], risks=[], watchPoints=[], recommendationText="觀望", finalScore=50,
            scoreBreakdown={}, researchReport=research
        )

        report = generate_markdown_report(context, [], "Neutral / 中性", decision)

        self.assertIn("籌碼資料來源：TWSE 三大法人買賣超日報", report)
        self.assertIn("籌碼資料狀態：latest_available", report)
        self.assertIn("法人資料日期：2026-06-17", report)

    def test_mock_data_gap_does_not_claim_finmind_chip_source(self) -> None:
        response = mock_data.build_mock_analysis("2330", "6mo")

        self.assertIn("真實籌碼資料", response.decision.researchReport.dataGaps)
        self.assertNotIn("真實 FinMind 籌碼資料", response.decision.researchReport.dataGaps)


if __name__ == "__main__":
    unittest.main()
