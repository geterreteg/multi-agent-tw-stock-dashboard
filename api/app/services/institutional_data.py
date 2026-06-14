from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

TWSE_INSTITUTIONAL_URL = "https://www.twse.com.tw/rwd/zh/fund/T86"
TPEX_INSTITUTIONAL_URL = "https://www.tpex.org.tw/www/zh-tw/insti/dailyTrade"
OFFICIAL_TIMEOUT_SECONDS = 10
OFFICIAL_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}


def get_institutional_data(symbol: str, market: str | None = None, date: str | None = None) -> dict[str, Any]:
    stock_id = normalize_symbol(symbol)
    market_key = normalize_market(market)

    if market_key == "TWSE":
        return fetch_twse_institutional_data(stock_id, date)
    if market_key == "TPEX":
        return fetch_tpex_institutional_data(stock_id, date)
    if market_key is not None:
        return empty_result(stock_id, "官方三大法人資料", [gap("invalid_market", f"不支援的市場別：{market}")])

    twse_result = fetch_twse_institutional_data(stock_id, date)
    if not twse_result["dataGaps"]:
        return twse_result

    tpex_result = fetch_tpex_institutional_data(stock_id, date)
    if not tpex_result["dataGaps"]:
        return tpex_result

    return empty_result(
        stock_id,
        "官方三大法人資料",
        [
            *twse_result["dataGaps"],
            *tpex_result["dataGaps"],
        ],
    )


def fetch_twse_institutional_data(symbol: str, query_date: str | None) -> dict[str, Any]:
    source = "TWSE 三大法人買賣超日報"
    params = {
        "date": format_twse_query_date(query_date),
        "selectType": "ALL",
        "response": "json",
    }

    try:
        payload = request_json(TWSE_INSTITUTIONAL_URL, params=params, referer="https://www.twse.com.tw/zh/trading/foreign/t86.html")
    except Exception as exc:
        error_type = type(exc).__name__
        logger.info(
            "institutional_source failed source=%s symbol=%s error_type=%s error_message=%s",
            source,
            symbol,
            error_type,
            short_error_message(exc),
        )
        return empty_result(symbol, source, [gap("source_unavailable", f"{source} 讀取失敗：{error_type}", error_type)])

    if str(payload.get("stat", "")).upper() != "OK":
        return empty_result(symbol, source, [gap("source_unavailable", f"{source} 回傳狀態非 OK")])

    fields = payload.get("fields") or []
    row = find_list_row(payload.get("data") or [], 0, symbol)
    if row is None:
        return empty_result(symbol, source, [gap("symbol_not_found", f"{source} 找不到股票代號 {symbol}")])

    values = row_to_dict(fields, row)
    result = empty_result(symbol, source)
    result.update(
        {
            "asOfDate": normalize_output_date(payload.get("date")),
            "foreignNetBuy": parse_int(values.get("外陸資買賣超股數(不含外資自營商)")),
            "investmentTrustNetBuy": parse_int(values.get("投信買賣超股數")),
            "dealerNetBuy": parse_int(values.get("自營商買賣超股數")),
            "institutionalNetBuyTotal": parse_int(values.get("三大法人買賣超股數")),
        }
    )
    add_missing_value_gaps(result, ["foreignNetBuy", "investmentTrustNetBuy", "dealerNetBuy", "institutionalNetBuyTotal"], source)
    return result


def fetch_tpex_institutional_data(symbol: str, query_date: str | None) -> dict[str, Any]:
    source = "TPEx 三大法人買賣明細"
    params = {
        "type": "Daily",
        "sect": "AL",
        "date": format_tpex_query_date(query_date),
        "response": "json",
    }

    try:
        payload = request_json(
            TPEX_INSTITUTIONAL_URL,
            params=params,
            referer="https://www.tpex.org.tw/zh-tw/mainboard/trading/major-institutional/detail/day.html",
        )
    except Exception as exc:
        error_type = type(exc).__name__
        logger.info(
            "institutional_source failed source=%s symbol=%s error_type=%s error_message=%s",
            source,
            symbol,
            error_type,
            short_error_message(exc),
        )
        return empty_result(symbol, source, [gap("source_unavailable", f"{source} 讀取失敗：{error_type}", error_type)])

    tables = payload.get("tables") or []
    table = tables[0] if tables else {}
    row = find_list_row(table.get("data") or [], 0, symbol)
    if row is None:
        return empty_result(symbol, source, [gap("symbol_not_found", f"{source} 找不到股票代號 {symbol}")])

    result = empty_result(symbol, source)
    result.update(
        {
            "asOfDate": normalize_output_date(table.get("date")),
            "foreignNetBuy": parse_int(get_list_value(row, 10)),
            "investmentTrustNetBuy": parse_int(get_list_value(row, 13)),
            "dealerNetBuy": parse_int(get_list_value(row, 22)),
            "institutionalNetBuyTotal": parse_int(get_list_value(row, 23)),
        }
    )
    add_missing_value_gaps(result, ["foreignNetBuy", "investmentTrustNetBuy", "dealerNetBuy", "institutionalNetBuyTotal"], source)
    return result


def request_json(url: str, params: dict[str, str], referer: str) -> dict[str, Any]:
    session = requests.Session()
    session.trust_env = False
    headers = {**OFFICIAL_HEADERS, "Referer": referer}
    response = session.get(url, params=params, headers=headers, timeout=OFFICIAL_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("JSON payload is not an object")
    return payload


def normalize_symbol(symbol: str) -> str:
    return str(symbol).strip().upper().replace(".TW", "").replace(".TWO", "")


def normalize_market(market: str | None) -> Optional[str]:
    if market is None:
        return None
    value = market.strip().upper()
    if value in {"TWSE", "上市"}:
        return "TWSE"
    if value in {"TPEX", "OTC", "上櫃"}:
        return "TPEX"
    return value


def empty_result(symbol: str, source: str, data_gaps: list[dict[str, str]] | None = None) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "asOfDate": None,
        "foreignNetBuy": None,
        "investmentTrustNetBuy": None,
        "dealerNetBuy": None,
        "institutionalNetBuyTotal": None,
        "source": source,
        "dataGaps": data_gaps or [],
    }


def gap(code: str, message: str, error_type: str | None = None) -> dict[str, str]:
    return {"code": code, "message": message, "errorType": error_type or code}


def short_error_message(exc: Exception) -> str:
    return " ".join(str(exc).split())[:240]


def add_missing_value_gaps(result: dict[str, Any], fields: list[str], source: str) -> None:
    missing = [field for field in fields if result.get(field) is None]
    if missing:
        result["dataGaps"].append(gap("missing_values", f"{source} 欄位缺值：{', '.join(missing)}"))


def row_to_dict(fields: list[Any], row: list[Any]) -> dict[str, Any]:
    return {str(field): row[index] if index < len(row) else None for index, field in enumerate(fields)}


def find_list_row(rows: list[Any], symbol_index: int, symbol: str) -> Optional[list[Any]]:
    for row in rows:
        if isinstance(row, list) and normalize_symbol(get_list_value(row, symbol_index)) == symbol:
            return row
    return None


def get_list_value(row: list[Any], index: int) -> Any:
    return row[index] if index < len(row) else None


def parse_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if text in {"", "--", "None", "null"}:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def format_twse_query_date(value: str | None) -> str:
    return parse_query_date(value).strftime("%Y%m%d")


def format_tpex_query_date(value: str | None) -> str:
    return parse_query_date(value).strftime("%Y/%m/%d")


def parse_query_date(value: str | None) -> date:
    if not value:
        return latest_likely_trading_date()

    text = value.strip()
    roc_date = parse_roc_date(text)
    if roc_date is not None:
        return roc_date

    for fmt in ("%Y%m%d", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass

    for fmt in ("%y%m%d", "%y/%m/%d"):
        try:
            parsed = datetime.strptime(text, fmt).date()
            if parsed.year < 2000:
                return date(parsed.year + 1911, parsed.month, parsed.day)
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


def normalize_output_date(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    roc_date = parse_roc_date(text)
    if roc_date is not None:
        return roc_date.isoformat()

    for fmt in ("%Y%m%d", "%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    for fmt in ("%y%m%d", "%y/%m/%d"):
        try:
            parsed = datetime.strptime(text, fmt).date()
            if parsed.year < 2000:
                return date(parsed.year + 1911, parsed.month, parsed.day).isoformat()
        except ValueError:
            pass
    return text


def parse_roc_date(text: str) -> Optional[date]:
    compact = text.replace("/", "").replace("-", "")
    if re.fullmatch(r"\d{7}", compact):
        year = int(compact[:3]) + 1911
        month = int(compact[3:5])
        day = int(compact[5:7])
        return date(year, month, day)
    match = re.fullmatch(r"(\d{2,3})[/-](\d{1,2})[/-](\d{1,2})", text)
    if match:
        year = int(match.group(1)) + 1911
        month = int(match.group(2))
        day = int(match.group(3))
        return date(year, month, day)
    return None
