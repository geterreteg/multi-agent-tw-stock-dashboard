from __future__ import annotations

import math
import os
import tempfile
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterator, Optional

import pandas as pd
import requests

try:
    import yfinance as yf
except ImportError:  # pragma: no cover
    yf = None


YFINANCE_SOURCE = "Yahoo Finance / yfinance"
TWSE_SOURCE = "TWSE 官方日 K"
TPEX_SOURCE = "TPEx 官方日 K"
FINMIND_SOURCE = "FinMind"
FINMIND_API_URL = "https://api.finmindtrade.com/api/v4/data"
TWSE_STOCK_DAY_URL = "https://www.twse.com.tw/exchangeReport/STOCK_DAY"
TPEX_STOCK_DAY_URL = "https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock"
FINMIND_TOKEN_CONFIGURED_MESSAGE = "FinMind API 權限已由後端環境設定"
FINMIND_TOKEN_PUBLIC_MESSAGE = "未偵測到 FinMind API 權限，將嘗試公開限制模式"
PROXY_ENV_VARS = ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "GIT_HTTP_PROXY", "GIT_HTTPS_PROXY"]
OFFICIAL_PRICE_TIMEOUT_SECONDS = 10
MIN_PRICE_ROWS = 20

logger = logging.getLogger(__name__)

if yf is not None:
    cache_dir = Path(tempfile.gettempdir()) / "tw_stock_yfinance_cache"
    cache_dir.mkdir(exist_ok=True)
    yf.set_tz_cache_location(str(cache_dir.resolve()))


@dataclass
class SourceStatus:
    name: str
    ok: bool
    message: str


def normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper().replace(".TW", "").replace(".TWO", "")


def safe_float(value) -> Optional[float]:
    try:
        if value is None or pd.isna(value):
            return None
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def safe_int(value) -> Optional[int]:
    number = safe_float(value)
    return int(number) if number is not None else None


def fmt_number(value: Optional[float], decimals: int = 2, suffix: str = "") -> str:
    if value is None:
        return "資料暫無"
    return f"{value:,.{decimals}f}{suffix}"


def get_finmind_token() -> tuple[str, str]:
    token = os.getenv("FINMIND_TOKEN", "").strip()
    if token:
        return token, FINMIND_TOKEN_CONFIGURED_MESSAGE
    return "", FINMIND_TOKEN_PUBLIC_MESSAGE


@contextmanager
def without_proxy_env() -> Iterator[None]:
    backup = {name: os.environ.get(name) for name in PROXY_ENV_VARS}
    for name in PROXY_ENV_VARS:
        os.environ.pop(name, None)
    try:
        yield
    finally:
        for name, value in backup.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def calculate_price_metrics(history: pd.DataFrame) -> dict[str, Optional[float]]:
    if history.empty or "Close" not in history.columns:
        return {
            "latest_close": None,
            "ma20": None,
            "ma60": None,
            "return_20d": None,
            "average_volume": None,
        }

    close = pd.to_numeric(history["Close"], errors="coerce").dropna()
    volume = pd.to_numeric(history.get("Volume", pd.Series(dtype=float)), errors="coerce").dropna()
    latest_close = safe_float(close.iloc[-1]) if not close.empty else None
    ma20 = safe_float(close.tail(20).mean()) if len(close) >= 20 else None
    ma60 = safe_float(close.tail(60).mean()) if len(close) >= 60 else None
    average_volume = safe_float(volume.tail(20).mean()) if not volume.empty else None

    return_20d = None
    if len(close) >= 21 and close.iloc[-21] != 0:
        return_20d = safe_float(((close.iloc[-1] / close.iloc[-21]) - 1) * 100)

    return {
        "latest_close": latest_close,
        "ma20": ma20,
        "ma60": ma60,
        "return_20d": return_20d,
        "average_volume": average_volume,
    }


def parse_period_months(period: str) -> int:
    normalized = (period or "6mo").strip().lower()
    if normalized.endswith("mo"):
        try:
            return max(1, min(60, int(normalized[:-2])))
        except ValueError:
            return 6
    if normalized.endswith("y"):
        try:
            return max(1, min(60, int(normalized[:-1]) * 12))
        except ValueError:
            return 12
    if normalized == "ytd":
        today = date.today()
        return max(1, today.month)
    return 6


def month_starts_for_period(period: str) -> list[date]:
    today = date.today()
    month_count = parse_period_months(period)
    cursor = date(today.year, today.month, 1)
    months: list[date] = []
    for _ in range(month_count + 1):
        months.append(cursor)
        if cursor.month == 1:
            cursor = date(cursor.year - 1, 12, 1)
        else:
            cursor = date(cursor.year, cursor.month - 1, 1)
    return sorted(months)


def period_start_date(period: str) -> pd.Timestamp:
    today = date.today()
    months = parse_period_months(period)
    return pd.Timestamp(today - timedelta(days=months * 31))


def parse_official_number(value: object) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if text in {"", "--", "---", "None", "nan"}:
        return None
    try:
        number = float(text)
        return number if math.isfinite(number) else None
    except ValueError:
        return None


def parse_official_date(value: object) -> Optional[pd.Timestamp]:
    if value is None:
        return None
    text = str(value).strip().replace(".", "/").replace("-", "/")
    parts = text.split("/")
    if len(parts) != 3:
        return None
    try:
        year, month, day = [int(part.strip()) for part in parts]
    except ValueError:
        return None
    if year < 1911:
        year += 1911
    try:
        return pd.Timestamp(datetime(year, month, day))
    except ValueError:
        return None


def clean_official_price_rows(rows: list[list[object]], fields: list[str], volume_multiplier: int = 1) -> pd.DataFrame:
    if not rows or not fields:
        return pd.DataFrame()

    frame = pd.DataFrame(rows, columns=fields)
    column_map = {
        "date": ["日期", "日 期", "Date"],
        "open": ["開盤價", "開盤", "Open"],
        "high": ["最高價", "最高", "High"],
        "low": ["最低價", "最低", "Low"],
        "close": ["收盤價", "收盤", "Close"],
        "volume": ["成交股數", "成交張數", "Volume"],
    }

    def find_column(candidates: list[str]) -> Optional[str]:
        for candidate in candidates:
            if candidate in frame.columns:
                return candidate
        return None

    selected = {key: find_column(candidates) for key, candidates in column_map.items()}
    if any(column is None for column in selected.values()):
        return pd.DataFrame()

    records = []
    for _, row in frame.iterrows():
        row_date = parse_official_date(row[selected["date"]])
        values = {
            "Open": parse_official_number(row[selected["open"]]),
            "High": parse_official_number(row[selected["high"]]),
            "Low": parse_official_number(row[selected["low"]]),
            "Close": parse_official_number(row[selected["close"]]),
            "Volume": parse_official_number(row[selected["volume"]]),
        }
        if row_date is None or any(values[column] is None for column in ["Open", "High", "Low", "Close"]):
            continue
        if values["Volume"] is not None:
            values["Volume"] = values["Volume"] * volume_multiplier
        records.append({"Date": row_date, **values})

    if not records:
        return pd.DataFrame()

    cleaned = pd.DataFrame(records).drop_duplicates(subset=["Date"]).sort_values("Date")
    cleaned = cleaned.set_index("Date")
    return cleaned[["Open", "High", "Low", "Close", "Volume"]]


def fetch_twse_price_history(stock_id: str, period: str) -> tuple[pd.DataFrame, str]:
    frames: list[pd.DataFrame] = []
    session = requests.Session()
    session.trust_env = False

    for month_start in month_starts_for_period(period):
        params = {
            "response": "json",
            "date": month_start.strftime("%Y%m%d"),
            "stockNo": stock_id,
        }
        try:
            response = session.get(TWSE_STOCK_DAY_URL, params=params, timeout=OFFICIAL_PRICE_TIMEOUT_SECONDS)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            return pd.DataFrame(), f"TWSE 讀取失敗：{type(exc).__name__}"

        if str(payload.get("stat", "")).upper() != "OK":
            continue
        frame = clean_official_price_rows(payload.get("data") or [], payload.get("fields") or [])
        if not frame.empty:
            frames.append(frame)

    if not frames:
        return pd.DataFrame(), "TWSE 無可用日 K 資料"
    return combine_price_frames(frames), ""


def fetch_tpex_price_history(stock_id: str, period: str) -> tuple[pd.DataFrame, str]:
    frames: list[pd.DataFrame] = []
    session = requests.Session()
    session.trust_env = False

    for month_start in month_starts_for_period(period):
        params = {
            "code": stock_id,
            "date": month_start.strftime("%Y/%m/%d"),
            "response": "json",
        }
        try:
            response = session.get(TPEX_STOCK_DAY_URL, params=params, timeout=OFFICIAL_PRICE_TIMEOUT_SECONDS)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            return pd.DataFrame(), f"TPEx 讀取失敗：{type(exc).__name__}"

        tables = payload.get("tables") or []
        table = tables[0] if tables else {}
        frame = clean_official_price_rows(table.get("data") or [], table.get("fields") or [], volume_multiplier=1000)
        if not frame.empty:
            frames.append(frame)

    if not frames:
        return pd.DataFrame(), "TPEx 無可用日 K 資料"
    return combine_price_frames(frames), ""


def combine_price_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames)
    combined = combined[~combined.index.duplicated(keep="last")].sort_index()
    return combined[["Open", "High", "Low", "Close", "Volume"]].dropna(how="all")


def trim_price_history_for_period(history: pd.DataFrame, period: str) -> pd.DataFrame:
    if history.empty:
        return history
    start = period_start_date(period)
    return history[history.index >= start].sort_index()


def valid_price_history(history: pd.DataFrame, min_rows: int = MIN_PRICE_ROWS) -> bool:
    if history.empty or len(history) < min_rows:
        return False
    required = ["Open", "High", "Low", "Close", "Volume"]
    if any(column not in history.columns for column in required):
        return False
    return not pd.to_numeric(history["Close"], errors="coerce").dropna().empty


def fetch_official_price_bundle(stock_id: str, period: str = "6mo") -> tuple[pd.DataFrame, dict[str, Optional[float]], SourceStatus]:
    attempts: list[str] = []
    for source_name, fetcher in ((TWSE_SOURCE, fetch_twse_price_history), (TPEX_SOURCE, fetch_tpex_price_history)):
        history, error = fetcher(stock_id, period)
        if valid_price_history(history):
            trimmed = trim_price_history_for_period(history, period)
            status = SourceStatus(source_name, True, f"已使用 {source_name} 取得 {stock_id} {period} 日 K 股價資料。")
            logger.info("price_source selected=%s stock_id=%s rows=%s period=%s", source_name, stock_id, len(trimmed), period)
            return trimmed, calculate_price_metrics(trimmed), status
        reason = error or f"{source_name} 資料不足：{len(history)} 筆"
        attempts.append(reason)
        logger.info("price_source unavailable=%s stock_id=%s reason=%s", source_name, stock_id, reason)

    y_history, y_metrics, y_status = fetch_yfinance_bundle(stock_id, period)
    if y_status.ok:
        y_status = SourceStatus(YFINANCE_SOURCE, True, f"官方日 K 不可用，已 fallback yfinance。{'；'.join(attempts)}")
        logger.info("price_source selected=%s stock_id=%s rows=%s period=%s fallback_reason=%s", YFINANCE_SOURCE, stock_id, len(y_history), period, "；".join(attempts))
    else:
        y_status = SourceStatus(YFINANCE_SOURCE, False, f"官方日 K 與 yfinance 皆不可用。{'；'.join(attempts)}；{y_status.message}")
        logger.info("price_source failed stock_id=%s period=%s reason=%s", stock_id, period, y_status.message)
    return y_history, y_metrics, y_status


def fetch_yfinance_bundle(stock_id: str, period: str = "6mo") -> tuple[pd.DataFrame, dict[str, Optional[float]], SourceStatus]:
    if yf is None:
        status = SourceStatus(YFINANCE_SOURCE, False, "尚未安裝 yfinance，系統已降級。")
        return pd.DataFrame(), calculate_price_metrics(pd.DataFrame()), status

    ticker = f"{stock_id}.TW"
    try:
        with without_proxy_env():
            history = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=False)
    except Exception as exc:
        status = SourceStatus(YFINANCE_SOURCE, False, f"yfinance 讀取失敗：{type(exc).__name__}")
        return pd.DataFrame(), calculate_price_metrics(pd.DataFrame()), status

    if history.empty:
        status = SourceStatus(YFINANCE_SOURCE, False, f"找不到 {ticker} 的股價資料，請確認股票代號或稍後再試。")
        return pd.DataFrame(), calculate_price_metrics(pd.DataFrame()), status

    if isinstance(history.columns, pd.MultiIndex):
        history.columns = history.columns.get_level_values(0)

    required = ["Open", "High", "Low", "Close", "Volume"]
    missing = [column for column in required if column not in history.columns]
    if missing:
        status = SourceStatus(YFINANCE_SOURCE, False, f"股價資料缺少欄位：{', '.join(missing)}")
        return pd.DataFrame(), calculate_price_metrics(pd.DataFrame()), status

    cleaned = history[required].dropna(how="all")
    status = SourceStatus(YFINANCE_SOURCE, True, f"已取得 {ticker} {period} 股價、成交量、均線與報酬率資料。")
    return cleaned, calculate_price_metrics(cleaned), status


def finmind_date_range(days: int) -> tuple[str, str]:
    end = date.today()
    start = end - timedelta(days=days)
    return start.isoformat(), end.isoformat()


def fetch_finmind_dataset(dataset: str, stock_id: str, token: str, days: int) -> tuple[pd.DataFrame, str]:
    start_date, end_date = finmind_date_range(days)
    params = {
        "dataset": dataset,
        "data_id": stock_id,
        "start_date": start_date,
        "end_date": end_date,
    }
    if token:
        params["token"] = token

    session = requests.Session()
    session.trust_env = False
    try:
        response = session.get(FINMIND_API_URL, params=params, timeout=15)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        return pd.DataFrame(), f"{dataset} 讀取失敗：{type(exc).__name__}"

    if payload.get("status") not in (200, "200", None):
        return pd.DataFrame(), f"{dataset} 回傳錯誤：{payload.get('msg') or payload.get('status')}"

    data = payload.get("data") or []
    if not data:
        return pd.DataFrame(), f"{dataset} 目前無可用資料"

    return pd.DataFrame(data), ""


def latest_numeric(df: pd.DataFrame, candidates: list[str]) -> Optional[float]:
    if df.empty:
        return None
    for column in candidates:
        if column in df.columns:
            series = pd.to_numeric(df[column], errors="coerce").dropna()
            if not series.empty:
                return safe_float(series.iloc[-1])
    return None


def summarize_revenue(df: pd.DataFrame) -> tuple[Optional[float], Optional[float]]:
    if df.empty:
        return None, None
    work = df.sort_values("date") if "date" in df.columns else df.copy()
    latest_revenue = latest_numeric(work, ["revenue", "Revenue"])
    growth = latest_numeric(work, ["revenue_growth_rate", "growth_rate", "YoY"])
    if growth is None and len(work) >= 13 and "revenue" in work.columns:
        latest = safe_float(work["revenue"].iloc[-1])
        previous_year = safe_float(work["revenue"].iloc[-13])
        if latest is not None and previous_year:
            growth = ((latest / previous_year) - 1) * 100
    return latest_revenue, growth


def summarize_financials(df: pd.DataFrame) -> Optional[float]:
    if df.empty:
        return None
    work = df.sort_values("date") if "date" in df.columns else df.copy()
    if "type" in work.columns and "value" in work.columns:
        type_text = work["type"].astype(str)
        eps_rows = work[type_text.str.contains("EPS|EarningsPerShare|BasicEarnings", case=False, na=False)]
        eps = latest_numeric(eps_rows, ["value"])
        if eps is not None:
            return eps
    return latest_numeric(work, ["EPS", "eps", "EarningsPerShare", "value"])


def summarize_institutional(df: pd.DataFrame) -> tuple[Optional[float], Optional[float]]:
    if df.empty:
        return None, None
    latest_rows = df[df["date"] == df["date"].max()].copy() if "date" in df.columns else df.tail(10).copy()
    for column in latest_rows.columns:
        if column not in {"date", "stock_id", "name"}:
            latest_rows[column] = pd.to_numeric(latest_rows[column], errors="coerce")

    if "buy" in latest_rows.columns and "sell" in latest_rows.columns:
        institutional_net = safe_float((latest_rows["buy"] - latest_rows["sell"]).sum())
    elif "buy_sell" in latest_rows.columns:
        institutional_net = safe_float(latest_rows["buy_sell"].sum())
    else:
        institutional_net = safe_float(latest_rows.select_dtypes("number").sum().sum())

    foreign_rows = latest_rows
    if "name" in latest_rows.columns:
        matched = latest_rows[latest_rows["name"].astype(str).str.contains("Foreign|外資", case=False, na=False)]
        if not matched.empty:
            foreign_rows = matched

    if "buy" in foreign_rows.columns and "sell" in foreign_rows.columns:
        foreign_buy = safe_float((foreign_rows["buy"] - foreign_rows["sell"]).sum())
    elif "buy_sell" in foreign_rows.columns:
        foreign_buy = safe_float(foreign_rows["buy_sell"].sum())
    else:
        foreign_buy = institutional_net

    return foreign_buy, institutional_net


def summarize_margin(df: pd.DataFrame) -> tuple[Optional[float], Optional[float]]:
    if df.empty:
        return None, None
    work = df.sort_values("date") if "date" in df.columns else df.copy()
    margin_candidates = ["MarginPurchaseTodayBalance", "MarginPurchaseBuy", "MarginPurchaseLimit"]
    short_candidates = ["ShortSaleTodayBalance", "ShortSale", "ShortSaleLimit"]
    latest_margin = latest_numeric(work, margin_candidates)
    latest_short = latest_numeric(work, short_candidates)
    if len(work) < 2:
        return None, None
    prev_margin = latest_numeric(work.iloc[:-1], margin_candidates)
    prev_short = latest_numeric(work.iloc[:-1], short_candidates)
    margin_change = latest_margin - prev_margin if latest_margin is not None and prev_margin is not None else None
    short_change = latest_short - prev_short if latest_short is not None and prev_short is not None else None
    return margin_change, short_change


def summarize_dividend(df: pd.DataFrame) -> str:
    if df.empty:
        return "股利資料暫無"
    work = df.sort_values("date") if "date" in df.columns else df.copy()
    latest = work.iloc[-1]
    cash = safe_float(latest.get("CashEarningsDistribution", latest.get("cash_dividend", 0)))
    stock = safe_float(latest.get("StockEarningsDistribution", latest.get("stock_dividend", 0)))
    return f"最近可得現金股利 {fmt_number(cash)}，股票股利 {fmt_number(stock)}"


def fetch_finmind_bundle(stock_id: str, token: str, token_mode: str) -> dict[str, object]:
    datasets = {
        "stock_info": ("TaiwanStockInfo", 3650),
        "month_revenue": ("TaiwanStockMonthRevenue", 1095),
        "financials": ("TaiwanStockFinancialStatements", 1095),
        "per": ("TaiwanStockPER", 365),
        "institutional": ("TaiwanStockInstitutionalInvestorsBuySell", 180),
        "margin": ("TaiwanStockMarginPurchaseShortSale", 180),
        "dividend": ("TaiwanStockDividend", 3650),
    }
    frames: dict[str, pd.DataFrame] = {}
    errors: list[str] = []

    for key, (dataset, days) in datasets.items():
        df, error = fetch_finmind_dataset(dataset, stock_id, token, days)
        frames[key] = df
        if error:
            errors.append(error)

    info = frames["stock_info"]
    stock_name = f"{stock_id}.TW"
    industry = "未分類"
    if not info.empty:
        matched = info[info.get("stock_id", pd.Series(dtype=str)).astype(str) == stock_id]
        row = matched.iloc[0] if not matched.empty else info.iloc[0]
        stock_name = str(row.get("stock_name", row.get("name", stock_name)))
        industry = str(row.get("industry_category", row.get("industry", industry)))

    latest_revenue, revenue_growth = summarize_revenue(frames["month_revenue"])
    eps = summarize_financials(frames["financials"])
    pe_ratio = latest_numeric(frames["per"], ["PER", "pe_ratio", "PE", "P_E_Ratio"])
    foreign_buy, institutional_net = summarize_institutional(frames["institutional"])
    margin_change, short_change = summarize_margin(frames["margin"])
    dividend_summary = summarize_dividend(frames["dividend"])

    ok_count = sum(1 for frame in frames.values() if not frame.empty)
    status = SourceStatus(
        FINMIND_SOURCE,
        ok_count > 0,
        f"已取得 {ok_count}/{len(datasets)} 組 FinMind 資料。"
        if ok_count > 0
        else f"FinMind 未取得資料；{token_mode}，系統已降級分析。",
    )

    if token_mode == FINMIND_TOKEN_PUBLIC_MESSAGE:
        errors.insert(0, "未偵測到 FinMind API 權限，已嘗試公開限制模式；部分資料可能受限。")

    return {
        "stock_name": stock_name,
        "industry": industry,
        "latest_revenue": latest_revenue,
        "revenue_growth": revenue_growth,
        "eps": eps,
        "pe_ratio": pe_ratio,
        "foreign_buy": foreign_buy,
        "institutional_net_buy": institutional_net,
        "margin_balance_change": margin_change,
        "short_balance_change": short_change,
        "dividend_summary": dividend_summary,
        "errors": errors,
        "status": status,
    }
