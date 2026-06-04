from __future__ import annotations

import math
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterator, Optional

import pandas as pd
import requests

try:
    import yfinance as yf
except ImportError:  # pragma: no cover
    yf = None


YFINANCE_SOURCE = "Yahoo Finance / yfinance"
FINMIND_SOURCE = "FinMind"
FINMIND_API_URL = "https://api.finmindtrade.com/api/v4/data"
FINMIND_TOKEN_CONFIGURED_MESSAGE = "FinMind API 權限已由後端環境設定"
FINMIND_TOKEN_PUBLIC_MESSAGE = "未偵測到 FinMind API 權限，將嘗試公開限制模式"
PROXY_ENV_VARS = ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "GIT_HTTP_PROXY", "GIT_HTTPS_PROXY"]

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
