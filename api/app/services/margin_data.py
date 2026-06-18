from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from typing import Any, Optional

import requests

from app.services.chip_data_status import apply_data_status, has_usable_data, trading_day_candidates

logger = logging.getLogger(__name__)

TWSE_MARGIN_URL = "https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN"
TPEX_MARGIN_URL = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_margin_balance"
OFFICIAL_TIMEOUT_SECONDS = 10
OFFICIAL_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}


def get_margin_data(symbol: str, market: str | None = None, date: str | None = None) -> dict[str, Any]:
    stock_id = normalize_symbol(symbol)
    market_key = normalize_market(market)
    target_date = parse_query_date(date)

    if market_key == "TWSE":
        return get_twse_margin_with_fallback(stock_id, target_date)
    if market_key == "TPEX":
        return get_tpex_latest_margin(stock_id, target_date)
    if market_key is not None:
        return empty_result(stock_id, "官方融資融券資料", [gap("invalid_market", f"不支援的市場別：{market}")])

    twse_result = get_twse_margin_with_fallback(stock_id, target_date)
    if twse_result["status"] != "missing":
        return twse_result

    tpex_result = get_tpex_latest_margin(stock_id, target_date)
    if tpex_result["status"] != "missing":
        return tpex_result

    return empty_result(
        stock_id,
        "官方融資融券資料",
        [gap("missing_recent_trading_days", "最近 5 個候選交易日皆無可用融資融券資料")],
    )


def get_twse_margin_with_fallback(symbol: str, target_date: date) -> dict[str, Any]:
    for candidate in trading_day_candidates(target_date):
        result = fetch_twse_margin_data(symbol, candidate.isoformat())
        if has_usable_data(result):
            return apply_data_status(result, target_date)
    return empty_result(
        symbol,
        "TWSE 融資融券餘額",
        [gap("missing_recent_trading_days", "最近 5 個候選交易日皆無可用 TWSE 融資融券資料")],
    )


def get_tpex_latest_margin(symbol: str, target_date: date) -> dict[str, Any]:
    result = fetch_tpex_margin_data(symbol)
    candidate_dates = {candidate.isoformat() for candidate in trading_day_candidates(target_date)}
    data_date = result.get("dataDate") or result.get("asOfDate")
    if has_usable_data(result) and data_date in candidate_dates:
        return apply_data_status(result, target_date)
    return empty_result(
        symbol,
        "TPEx 融資融券餘額",
        [gap("missing_recent_trading_days", "最近 5 個候選交易日皆無可用 TPEx 融資融券資料")],
    )


def fetch_twse_margin_data(symbol: str, query_date: str) -> dict[str, Any]:
    source = "TWSE 融資融券餘額"
    params = {"date": parse_query_date(query_date).strftime("%Y%m%d"), "selectType": "ALL", "response": "json"}
    try:
        payload = request_json(
            TWSE_MARGIN_URL,
            params=params,
            referer="https://www.twse.com.tw/zh/trading/margin/mi-margn.html",
        )
    except Exception as exc:
        error_type = type(exc).__name__
        logger.info(
            "margin_source failed source=%s symbol=%s error_type=%s error_message=%s",
            source,
            symbol,
            error_type,
            short_error_message(exc),
        )
        return empty_result(symbol, source, [gap("source_unavailable", f"{source} 讀取失敗：{error_type}", error_type)])

    _, row = find_twse_stock_row(payload.get("tables") or [], symbol)
    if row is None:
        return empty_result(symbol, source, [gap("symbol_not_found", f"{source} 找不到股票代號 {symbol}")])

    margin_balance = parse_int(get_list_value(row, 6))
    previous_margin = parse_int(get_list_value(row, 5))
    short_balance = parse_int(get_list_value(row, 12))
    previous_short = parse_int(get_list_value(row, 11))

    result = empty_result(symbol, source)
    result.update(
        {
            "asOfDate": normalize_output_date(payload.get("date")),
            "dataDate": normalize_output_date(payload.get("date")),
            "marginBalance": margin_balance,
            "marginChange": diff_or_none(margin_balance, previous_margin),
            "shortBalance": short_balance,
            "shortChange": diff_or_none(short_balance, previous_short),
            "marginUtilizationRate": utilization_rate(margin_balance, parse_int(get_list_value(row, 7))),
            "shortUtilizationRate": utilization_rate(short_balance, parse_int(get_list_value(row, 13))),
        }
    )
    add_missing_value_gaps(result, ["marginBalance", "marginChange", "shortBalance", "shortChange"], source)
    return result


def fetch_tpex_margin_data(symbol: str) -> dict[str, Any]:
    source = "TPEx 融資融券餘額"
    try:
        rows = request_json_list(TPEX_MARGIN_URL, referer="https://www.tpex.org.tw/zh-tw/mainboard/trading/margin-trading/balance.html")
    except Exception as exc:
        error_type = type(exc).__name__
        logger.info(
            "margin_source failed source=%s symbol=%s error_type=%s error_message=%s",
            source,
            symbol,
            error_type,
            short_error_message(exc),
        )
        return empty_result(symbol, source, [gap("source_unavailable", f"{source} 讀取失敗：{error_type}", error_type)])

    row = find_dict_row(rows, "SecuritiesCompanyCode", symbol)
    if row is None:
        return empty_result(symbol, source, [gap("symbol_not_found", f"{source} 找不到股票代號 {symbol}")])

    margin_balance = parse_int(row.get("MarginPurchaseBalance"))
    previous_margin = parse_int(row.get("MarginPurchaseBalancePreviousDay"))
    short_balance = parse_int(row.get("ShortSaleBalance"))
    previous_short = parse_int(row.get("ShortSaleBalancePreviousDay"))

    result = empty_result(symbol, source)
    result.update(
        {
            "asOfDate": normalize_output_date(row.get("Date")),
            "dataDate": normalize_output_date(row.get("Date")),
            "marginBalance": margin_balance,
            "marginChange": diff_or_none(margin_balance, previous_margin),
            "shortBalance": short_balance,
            "shortChange": diff_or_none(short_balance, previous_short),
            "marginUtilizationRate": parse_float(row.get("MarginPurchaseUtilizationRate")),
            "shortUtilizationRate": parse_float(row.get("ShortSaleUtilizationRate")),
        }
    )
    add_missing_value_gaps(result, ["marginBalance", "marginChange", "shortBalance", "shortChange"], source)
    return result


def request_json_list(url: str, referer: str) -> list[dict[str, Any]]:
    session = requests.Session()
    session.trust_env = False
    headers = {**OFFICIAL_HEADERS, "Referer": referer}
    response = session.get(url, headers=headers, timeout=OFFICIAL_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError("JSON payload is not a list")
    return [row for row in payload if isinstance(row, dict)]


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
        "dataDate": None,
        "status": "missing",
        "marginBalance": None,
        "marginChange": None,
        "shortBalance": None,
        "shortChange": None,
        "marginUtilizationRate": None,
        "shortUtilizationRate": None,
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


def find_dict_row(rows: list[dict[str, Any]], symbol_key: str, symbol: str) -> Optional[dict[str, Any]]:
    for row in rows:
        if normalize_symbol(row.get(symbol_key, "")) == symbol:
            return row
    return None


def find_twse_stock_row(tables: list[Any], symbol: str) -> tuple[list[Any], Optional[list[Any]]]:
    symbol_fields = ("代號", "股票代號", "證券代號")
    for table in tables:
        if not isinstance(table, dict):
            continue
        fields = table.get("fields") or []
        symbol_field = next((field for field in symbol_fields if field in fields), None)
        if symbol_field is None:
            continue
        row = find_list_row(table.get("data") or [], fields.index(symbol_field), symbol)
        if row is not None:
            return fields, row
    return [], None


def find_list_row(rows: list[Any], symbol_index: int, symbol: str) -> Optional[list[Any]]:
    for row in rows:
        if isinstance(row, list) and normalize_symbol(get_list_value(row, symbol_index)) == symbol:
            return row
    return None


def get_list_value(row: list[Any], index: int) -> Any:
    return row[index] if index < len(row) else None


def parse_int(value: Any) -> Optional[int]:
    number = parse_float(value)
    return int(number) if number is not None else None


def parse_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if text in {"", "--", "None", "null"}:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number


def diff_or_none(current: Optional[int], previous: Optional[int]) -> Optional[int]:
    if current is None or previous is None:
        return None
    return current - previous


def utilization_rate(balance: Optional[int], quota: Optional[int]) -> Optional[float]:
    if balance is None or quota in (None, 0):
        return None
    return round(balance / quota * 100, 4)


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
