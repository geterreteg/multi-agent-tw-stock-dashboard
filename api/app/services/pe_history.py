from __future__ import annotations

import calendar
import concurrent.futures
import json
import math
import threading
import time
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Optional

import requests


TWSE_PE_URL = "https://www.twse.com.tw/exchangeReport/BWIBBU_d"
TWSE_PE_SOURCE = "TWSE 個股日本益比、殖利率及股價淨值比"
DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[2] / ".cache" / "pe_history"
REQUEST_TIMEOUT_SECONDS = 4
OVERALL_TIMEOUT_SECONDS = 6
MAX_WORKERS = 5
RequestJson = Callable[[str], dict[str, Any]]


@dataclass(frozen=True)
class HistoricalPEResult:
    symbol: str
    minPE: Optional[float]
    p25PE: Optional[float]
    medianPE: Optional[float]
    p75PE: Optional[float]
    maxPE: Optional[float]
    validSampleCount: int
    source: str
    cacheStatus: str
    dataLimitations: list[str]
    samples: list[dict[str, Any]]


def get_historical_pe(
    symbol: str,
    market: str | None,
    reference_date: date | None = None,
    months: int = 36,
    cache_path: Path | None = None,
    request_json: RequestJson | None = None,
    overall_timeout_seconds: float = OVERALL_TIMEOUT_SECONDS,
    max_workers: int = MAX_WORKERS,
) -> HistoricalPEResult:
    stock_id = _normalize_symbol(symbol)
    resolved_cache_path = cache_path or DEFAULT_CACHE_DIR / f"{stock_id}.json"
    if str(market or "").strip().upper() != "TWSE":
        return empty_historical_pe(stock_id, ["第一版歷史 PE 僅支援 TWSE 上市股票，尚不支援 TPEx。"])

    cached = _read_cache(resolved_cache_path, stock_id)
    if cached is not None:
        return replace(
            cached,
            cacheStatus="cache",
            dataLimitations=[*cached.dataLimitations, "本次優先使用有效歷史 PE JSON 快取，未同步重抓 TWSE。"],
        )

    requester = request_json or _build_twse_requester()
    samples: list[dict[str, Any]] = []
    month_ends = _recent_completed_month_ends(reference_date or date.today(), months)
    deadline = time.monotonic() + max(0, overall_timeout_seconds)
    timed_out = False
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(max_workers, len(month_ends) or 1)))
    futures: dict[concurrent.futures.Future[Optional[dict[str, Any]]], date] = {}
    try:
        futures = {
            executor.submit(_fetch_month_end_sample, stock_id, month_end, requester, deadline): month_end
            for month_end in month_ends
        }
        done, not_done = concurrent.futures.wait(futures, timeout=max(0, overall_timeout_seconds))
        timed_out = bool(not_done)
        for future in done:
            try:
                sample = future.result()
            except Exception:
                sample = None
            if sample is not None:
                samples.append(sample)
        for future in not_done:
            future.cancel()
    except Exception as exc:
        return empty_historical_pe(
            stock_id,
            [f"TWSE 歷史 PE best-effort 讀取失敗（{type(exc).__name__}），且無可用快取；不影響主分析。"],
        )
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    result = summarize_pe_samples(stock_id, samples)
    limitations = [
        "歷史 PE 取自 TWSE 每日本益比資料，以最近 36 個已完成月份的月末或往前最多 10 天交易日為樣本。",
        "TWSE 資料可能延遲、缺漏或調整欄位格式；歷史區間不代表未來合理估值。",
    ]
    missing_months = max(0, len(month_ends) - result.validSampleCount)
    if missing_months:
        limitations.append(f"{missing_months} 個月份在月末往前 10 天內無可用 PE 樣本。")
    if timed_out:
        limitations.append(f"TWSE live 抓取已達 {overall_timeout_seconds:g} 秒整體時間上限，未完成月份視為 missing；不影響主分析。")
    if result.validSampleCount == 0:
        limitations.append("TWSE live 抓取未取得可用歷史 PE，且無有效快取；主分析仍可繼續。")
    result = replace(result, dataLimitations=limitations)
    if result.validSampleCount > 0:
        try:
            _write_cache(resolved_cache_path, result)
        except OSError:
            result = replace(result, dataLimitations=[*result.dataLimitations, "歷史 PE cache 寫入失敗；不影響本次主分析。"])
    return result


def parse_pe(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if text in {"", "--"}:
        return None
    try:
        parsed = float(text)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed) or parsed <= 0:
        return None
    return parsed


def summarize_pe_samples(symbol: str, samples: list[dict[str, Any]]) -> HistoricalPEResult:
    valid_samples = [
        {"date": str(sample.get("date", "")), "pe": pe}
        for sample in samples
        if (pe := parse_pe(sample.get("pe"))) is not None
    ]
    values = sorted(float(sample["pe"]) for sample in valid_samples)
    if not values:
        return empty_historical_pe(symbol)
    return HistoricalPEResult(
        symbol=symbol,
        minPE=_rounded(values[0]),
        p25PE=_rounded(_percentile(values, 0.25)),
        medianPE=_rounded(_percentile(values, 0.50)),
        p75PE=_rounded(_percentile(values, 0.75)),
        maxPE=_rounded(values[-1]),
        validSampleCount=len(values),
        source=TWSE_PE_SOURCE,
        cacheStatus="live",
        dataLimitations=[],
        samples=valid_samples,
    )


def empty_historical_pe(symbol: str, limitations: list[str] | None = None) -> HistoricalPEResult:
    return HistoricalPEResult(
        symbol=symbol,
        minPE=None,
        p25PE=None,
        medianPE=None,
        p75PE=None,
        maxPE=None,
        validSampleCount=0,
        source=TWSE_PE_SOURCE,
        cacheStatus="missing",
        dataLimitations=limitations or [],
        samples=[],
    )


def _fetch_month_end_sample(
    symbol: str,
    month_end: date,
    request_json: RequestJson,
    deadline: float = math.inf,
) -> Optional[dict[str, Any]]:
    for days_back in range(11):
        if time.monotonic() >= deadline:
            return None
        query_date = month_end - timedelta(days=days_back)
        payload = request_json(query_date.strftime("%Y%m%d"))
        if str(payload.get("stat", "")).upper() != "OK":
            continue
        data_date = _parse_twse_date(payload.get("date")) or query_date
        if data_date > month_end or data_date < month_end - timedelta(days=10):
            continue
        fields = [str(field).strip() for field in payload.get("fields") or []]
        try:
            symbol_index = fields.index("證券代號")
            pe_index = fields.index("本益比")
        except ValueError:
            raise ValueError("TWSE PE payload fields changed")
        for row in payload.get("data") or []:
            if not isinstance(row, list) or symbol_index >= len(row):
                continue
            if _normalize_symbol(row[symbol_index]) != symbol:
                continue
            pe = parse_pe(row[pe_index] if pe_index < len(row) else None)
            if pe is not None:
                return {"date": data_date.isoformat(), "pe": pe}
    return None


def _recent_completed_month_ends(reference_date: date, months: int) -> list[date]:
    if months <= 0:
        return []
    year = reference_date.year
    month = reference_date.month - 1
    if month == 0:
        year -= 1
        month = 12
    result: list[date] = []
    for _ in range(months):
        result.append(date(year, month, calendar.monthrange(year, month)[1]))
        month -= 1
        if month == 0:
            year -= 1
            month = 12
    return result


def _percentile(values: list[float], percentile: float) -> float:
    if len(values) == 1:
        return values[0]
    position = (len(values) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return values[lower]
    weight = position - lower
    return values[lower] + (values[upper] - values[lower]) * weight


def _rounded(value: float) -> float:
    return round(value, 2)


def _normalize_symbol(symbol: Any) -> str:
    return str(symbol).strip().upper().replace(".TW", "").replace(".TWO", "")


def _parse_twse_date(value: Any) -> Optional[date]:
    text = str(value or "").strip()
    try:
        return datetime.strptime(text, "%Y%m%d").date()
    except ValueError:
        return None


def _build_twse_requester() -> RequestJson:
    thread_local = threading.local()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
        "Accept": "application/json,text/plain,*/*",
        "Referer": "https://www.twse.com.tw/zh/trading/historical/bwibbu.html",
    }

    def request_json(query_date: str) -> dict[str, Any]:
        session = getattr(thread_local, "session", None)
        if session is None:
            session = requests.Session()
            session.trust_env = False
            thread_local.session = session
        response = session.get(
            TWSE_PE_URL,
            params={"date": query_date, "selectType": "ALL", "response": "json"},
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("TWSE PE payload is not an object")
        return payload

    return request_json


def _write_cache(cache_path: Path, result: HistoricalPEResult) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"cachedAt": datetime.now().isoformat(timespec="seconds"), "result": asdict(result)}
    cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_cache(cache_path: Path, symbol: str) -> Optional[HistoricalPEResult]:
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        result = payload.get("result") or {}
        cached = HistoricalPEResult(**result)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None
    if cached.symbol != symbol or cached.validSampleCount <= 0:
        return None
    validated = summarize_pe_samples(symbol, cached.samples)
    if validated.validSampleCount != cached.validSampleCount:
        return None
    return replace(
        validated,
        source=cached.source,
        cacheStatus="cache",
        dataLimitations=cached.dataLimitations,
    )
