from __future__ import annotations

import time
from datetime import date, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Query

from app.services.institutional_data import (
    OFFICIAL_HEADERS as INSTITUTIONAL_HEADERS,
    OFFICIAL_TIMEOUT_SECONDS as INSTITUTIONAL_TIMEOUT_SECONDS,
    TPEX_INSTITUTIONAL_URL,
    TWSE_INSTITUTIONAL_URL,
)
from app.services.margin_data import (
    OFFICIAL_HEADERS as MARGIN_HEADERS,
    OFFICIAL_TIMEOUT_SECONDS as MARGIN_TIMEOUT_SECONDS,
    TPEX_MARGIN_URL,
    TWSE_MARGIN_URL,
)

router = APIRouter()


@router.get("/debug/official-source")
def debug_official_source(
    market: str = Query(..., pattern="^(TWSE|TPEX|twse|tpex)$"),
    kind: str = Query(..., pattern="^(institutional|margin)$"),
    symbol: str = Query(..., min_length=1, max_length=12),
    date: str | None = Query(None),
) -> dict[str, Any]:
    market_key = market.strip().upper()
    kind_key = kind.strip().lower()
    symbol_key = normalize_symbol(symbol)
    started = time.perf_counter()

    result: dict[str, Any] = {
        "requestedUrl": None,
        "market": market_key,
        "kind": kind_key,
        "symbol": symbol_key,
        "queryDate": None,
        "httpStatus": None,
        "contentType": None,
        "responsePreview": None,
        "errorType": None,
        "errorMessage": None,
        "elapsedMs": None,
    }

    try:
        query_date = normalize_query_date(date)
        request_spec = build_request_spec(market_key, kind_key, query_date)
        result["queryDate"] = query_date
        result["requestedUrl"] = build_requested_url(request_spec["url"], request_spec["params"])

        session = requests.Session()
        session.trust_env = False
        response = session.get(
            request_spec["url"],
            params=request_spec["params"],
            headers=request_spec["headers"],
            timeout=request_spec["timeout"],
        )
        result["requestedUrl"] = response.url
        result["httpStatus"] = response.status_code
        result["contentType"] = response.headers.get("content-type")
        result["responsePreview"] = response.text[:800]
    except Exception as exc:
        result["errorType"] = type(exc).__name__
        result["errorMessage"] = short_error_message(exc)
    finally:
        result["elapsedMs"] = round((time.perf_counter() - started) * 1000)

    return result


def build_request_spec(market: str, kind: str, query_date: str | None) -> dict[str, Any]:
    if kind == "institutional":
        if market == "TWSE":
            params = {
                "date": format_twse_date(query_date),
                "selectType": "ALL",
                "response": "json",
            }
            return {
                "url": TWSE_INSTITUTIONAL_URL,
                "params": params,
                "headers": {
                    **INSTITUTIONAL_HEADERS,
                    "Referer": "https://www.twse.com.tw/zh/trading/foreign/t86.html",
                },
                "timeout": INSTITUTIONAL_TIMEOUT_SECONDS,
            }
        params = {
            "type": "Daily",
            "sect": "AL",
            "date": format_tpex_date(query_date),
            "response": "json",
        }
        return {
            "url": TPEX_INSTITUTIONAL_URL,
            "params": params,
            "headers": {
                **INSTITUTIONAL_HEADERS,
                "Referer": "https://www.tpex.org.tw/zh-tw/mainboard/trading/major-institutional/detail/day.html",
            },
            "timeout": INSTITUTIONAL_TIMEOUT_SECONDS,
        }

    if market == "TWSE":
        return {
            "url": TWSE_MARGIN_URL,
            "params": {
                "date": format_twse_date(query_date),
                "selectType": "ALL",
                "response": "json",
            },
            "headers": {**MARGIN_HEADERS, "Referer": "https://www.twse.com.tw/zh/trading/margin/mi-margn.html"},
            "timeout": MARGIN_TIMEOUT_SECONDS,
        }
    return {
        "url": TPEX_MARGIN_URL,
        "params": {},
        "headers": {
            **MARGIN_HEADERS,
            "Referer": "https://www.tpex.org.tw/zh-tw/mainboard/trading/margin-trading/balance.html",
        },
        "timeout": MARGIN_TIMEOUT_SECONDS,
    }


def build_requested_url(url: str, params: dict[str, str]) -> str:
    if not params:
        return url
    return f"{url}?{urlencode(params)}"


def normalize_symbol(symbol: str) -> str:
    return str(symbol).strip().upper().replace(".TW", "").replace(".TWO", "")


def normalize_query_date(value: str | None) -> str | None:
    if not value:
        return None
    parsed = parse_query_date(value)
    return parsed.isoformat()


def format_twse_date(value: str | None) -> str:
    return parse_query_date(value).strftime("%Y%m%d")


def format_tpex_date(value: str | None) -> str:
    return parse_query_date(value).strftime("%Y/%m/%d")


def parse_query_date(value: str | None) -> date:
    if not value:
        return latest_likely_trading_date()

    text = value.strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Unsupported date format: {value}")


def latest_likely_trading_date() -> date:
    today = date.today()
    if today.weekday() == 5:
        return today - timedelta(days=1)
    if today.weekday() == 6:
        return today - timedelta(days=2)
    return today


def short_error_message(exc: Exception) -> str:
    return " ".join(str(exc).split())[:240]
