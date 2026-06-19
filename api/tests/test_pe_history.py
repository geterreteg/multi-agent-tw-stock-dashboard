from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from app.services.pe_history import (
    get_historical_pe,
    parse_pe,
    summarize_pe_samples,
)


class PeHistoryParsingTests(unittest.TestCase):
    def test_parse_pe_accepts_positive_numeric_values(self) -> None:
        self.assertEqual(21.35, parse_pe("21.35"))
        self.assertEqual(1234.5, parse_pe("1,234.5"))

    def test_parse_pe_filters_invalid_values(self) -> None:
        for value in (None, "", "--", "0", 0, "-3.5", -1, "not-a-number"):
            with self.subTest(value=value):
                self.assertIsNone(parse_pe(value))

    def test_percentiles_use_linear_interpolation(self) -> None:
        result = summarize_pe_samples(
            "2330",
            [
                {"date": "2024-01-31", "pe": 10},
                {"date": "2024-02-29", "pe": 20},
                {"date": "2024-03-29", "pe": 30},
                {"date": "2024-04-30", "pe": 40},
            ],
        )

        self.assertEqual(4, result.validSampleCount)
        self.assertEqual(10, result.minPE)
        self.assertEqual(17.5, result.p25PE)
        self.assertEqual(25, result.medianPE)
        self.assertEqual(32.5, result.p75PE)
        self.assertEqual(40, result.maxPE)


class PeHistoryCacheTests(unittest.TestCase):
    def test_collects_exactly_36_completed_month_end_samples(self) -> None:
        calls: list[str] = []

        def request_json(query_date: str) -> dict:
            calls.append(query_date)
            return {
                "stat": "OK",
                "date": query_date,
                "fields": ["證券代號", "本益比"],
                "data": [["2330", "20"]],
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            result = get_historical_pe(
                "2330",
                market="TWSE",
                reference_date=date(2025, 3, 15),
                cache_path=Path(temp_dir) / "2330.json",
                request_json=request_json,
            )

        self.assertEqual(36, result.validSampleCount)
        self.assertEqual(36, len(calls))
        self.assertEqual("20250228", calls[0])
        self.assertEqual("20220331", calls[-1])

    def test_tpex_is_explicitly_unavailable_without_twse_request(self) -> None:
        calls: list[str] = []

        result = get_historical_pe("8299", market="TPEX", request_json=lambda value: calls.append(value) or {})

        self.assertEqual(0, result.validSampleCount)
        self.assertEqual("missing", result.cacheStatus)
        self.assertEqual([], calls)
        self.assertTrue(any("TPEx" in item and "尚不支援" in item for item in result.dataLimitations))

    def test_month_end_looks_back_up_to_ten_days_and_filters_invalid_pe(self) -> None:
        calls: list[str] = []

        def request_json(query_date: str) -> dict:
            calls.append(query_date)
            if query_date == "20250228":
                return {
                    "stat": "OK",
                    "date": "20250201",
                    "fields": ["證券代號", "本益比"],
                    "data": [["2330", "99"]],
                }
            if query_date == "20250227":
                return {
                    "stat": "OK",
                    "date": query_date,
                    "fields": ["證券代號", "本益比"],
                    "data": [["2330", "21.5"]],
                }
            return {"stat": "很抱歉，沒有符合條件的資料!"}

        with tempfile.TemporaryDirectory() as temp_dir:
            result = get_historical_pe(
                "2330",
                market="TWSE",
                reference_date=date(2025, 3, 15),
                months=1,
                cache_path=Path(temp_dir) / "2330.json",
                request_json=request_json,
            )

        self.assertEqual(["20250228", "20250227"], calls)
        self.assertEqual(1, result.validSampleCount)
        self.assertEqual(21.5, result.medianPE)
        self.assertEqual("2025-02-27", result.samples[0]["date"])

    def test_no_usable_live_samples_falls_back_to_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "2330.json"

            def successful_request(query_date: str) -> dict:
                return {
                    "stat": "OK",
                    "date": query_date,
                    "fields": ["證券代號", "本益比"],
                    "data": [["2330", "20"]],
                }

            get_historical_pe(
                "2330",
                market="TWSE",
                reference_date=date(2025, 3, 15),
                months=1,
                cache_path=cache_path,
                request_json=successful_request,
            )
            cached = get_historical_pe(
                "2330",
                market="TWSE",
                reference_date=date(2025, 3, 15),
                months=1,
                cache_path=cache_path,
                request_json=lambda _: {"stat": "很抱歉，沒有符合條件的資料!"},
            )

        self.assertEqual("cache", cached.cacheStatus)
        self.assertEqual(20, cached.medianPE)

    def test_source_failure_uses_existing_json_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "2330.json"

            def successful_request(query_date: str) -> dict:
                return {
                    "stat": "OK",
                    "date": query_date,
                    "fields": ["證券代號", "本益比"],
                    "data": [["2330", "20"]],
                }

            live = get_historical_pe(
                "2330",
                market="TWSE",
                reference_date=date(2025, 3, 15),
                months=1,
                cache_path=cache_path,
                request_json=successful_request,
            )

            def failed_request(_: str) -> dict:
                raise ConnectionError("TWSE unavailable")

            cached = get_historical_pe(
                "2330",
                market="TWSE",
                reference_date=date(2025, 3, 15),
                months=1,
                cache_path=cache_path,
                request_json=failed_request,
            )

        self.assertEqual("live", live.cacheStatus)
        self.assertEqual("cache", cached.cacheStatus)
        self.assertEqual(20, cached.medianPE)
        self.assertTrue(any("快取" in item for item in cached.dataLimitations))


if __name__ == "__main__":
    unittest.main()
