from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

try:
    from dotenv import dotenv_values
except ImportError:  # pragma: no cover
    dotenv_values = None

try:
    import yfinance as yf
except ImportError:  # pragma: no cover
    yf = None

if yf is not None:
    YFINANCE_CACHE_DIR = Path(tempfile.gettempdir()) / "tw_stock_yfinance_cache"
    YFINANCE_CACHE_DIR.mkdir(exist_ok=True)
    yf.set_tz_cache_location(str(YFINANCE_CACHE_DIR.resolve()))


APP_TITLE = "多 Agent 台股智慧分析儀表板"
APP_SUBTITLE = "整合 Yahoo Finance 與 FinMind，讓多個分析 Agent 協作產生台股研究報告。"
DISCLAIMER = "本系統分析結果僅供學術研究與投資參考，不構成任何買賣建議。投資人仍應自行評估風險並承擔投資結果。"
DATA_DELAY_NOTE = "資料可能延遲或不完整，本系統不宣稱資料完全即時。"
YFINANCE_SOURCE = "Yahoo Finance / yfinance"
FINMIND_SOURCE = "FinMind"
FINMIND_API_URL = "https://api.finmindtrade.com/api/v4/data"
FINMIND_TOKEN_CONFIGURED_MESSAGE = "FinMind token 已由系統環境設定"
FINMIND_TOKEN_PUBLIC_MESSAGE = "未偵測到 FinMind token，將嘗試公開限制模式"
PROXY_ENV_VARS = ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "GIT_HTTP_PROXY", "GIT_HTTPS_PROXY"]


@dataclass
class SourceStatus:
    name: str
    ok: bool
    message: str


@dataclass
class StockContext:
    stock_id: str
    stock_name: str
    industry: str
    last_updated: str
    price_history: pd.DataFrame = field(default_factory=pd.DataFrame)
    latest_close: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    return_20d: Optional[float] = None
    average_volume: Optional[float] = None
    revenue_growth: Optional[float] = None
    latest_revenue: Optional[float] = None
    eps: Optional[float] = None
    pe_ratio: Optional[float] = None
    foreign_buy: Optional[float] = None
    institutional_net_buy: Optional[float] = None
    margin_balance_change: Optional[float] = None
    short_balance_change: Optional[float] = None
    dividend_summary: str = "股利資料暫無"
    source_status: List[SourceStatus] = field(default_factory=list)
    finmind_errors: List[str] = field(default_factory=list)
    finmind_token_mode: str = FINMIND_TOKEN_PUBLIC_MESSAGE


def normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper().replace(".TW", "").replace(".TWO", "")


def is_valid_tw_symbol(symbol: str) -> bool:
    return symbol.isdigit() and 4 <= len(symbol) <= 6


def safe_float(value) -> Optional[float]:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt_number(value: Optional[float], decimals: int = 2, suffix: str = "") -> str:
    if value is None:
        return "資料暫無"
    return f"{value:,.{decimals}f}{suffix}"


def read_env_file_token() -> str:
    if dotenv_values is not None:
        value = dotenv_values(".env").get("FINMIND_TOKEN", "")
        return str(value).strip() if value else ""

    try:
        lines = Path(".env").read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return ""

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() == "FINMIND_TOKEN":
            return value.strip().strip('"').strip("'")
    return ""


def get_finmind_token() -> Tuple[str, str]:
    try:
        token = st.secrets.get("FINMIND_TOKEN", "")
        if token:
            return str(token), FINMIND_TOKEN_CONFIGURED_MESSAGE
    except Exception:
        pass

    token = os.getenv("FINMIND_TOKEN", "")
    if token:
        return token, FINMIND_TOKEN_CONFIGURED_MESSAGE

    token = read_env_file_token()
    if token:
        return token, FINMIND_TOKEN_CONFIGURED_MESSAGE

    return "", FINMIND_TOKEN_PUBLIC_MESSAGE


def calculate_price_metrics(history: pd.DataFrame) -> Dict[str, Optional[float]]:
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


def without_proxy_env() -> Dict[str, Optional[str]]:
    backup = {name: os.environ.get(name) for name in PROXY_ENV_VARS}
    for name in PROXY_ENV_VARS:
        os.environ.pop(name, None)
    return backup


def restore_proxy_env(backup: Dict[str, Optional[str]]) -> None:
    for name, value in backup.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


def fetch_yfinance_bundle(stock_id: str, period: str = "6mo") -> Tuple[pd.DataFrame, Dict[str, Optional[float]], SourceStatus]:
    if yf is None:
        status = SourceStatus(YFINANCE_SOURCE, False, "尚未安裝 yfinance，請先執行 pip install -r requirements.txt。")
        return pd.DataFrame(), calculate_price_metrics(pd.DataFrame()), status

    ticker = f"{stock_id}.TW"
    proxy_backup = without_proxy_env()
    try:
        history = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=False)
    except Exception as exc:
        status = SourceStatus(YFINANCE_SOURCE, False, f"yfinance 讀取失敗：{type(exc).__name__}")
        return pd.DataFrame(), calculate_price_metrics(pd.DataFrame()), status
    finally:
        restore_proxy_env(proxy_backup)

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


def finmind_date_range(days: int) -> Tuple[str, str]:
    end = date.today()
    start = end - timedelta(days=days)
    return start.isoformat(), end.isoformat()


def fetch_finmind_dataset(dataset: str, stock_id: str, token: str, days: int) -> Tuple[pd.DataFrame, str]:
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


def latest_numeric(df: pd.DataFrame, candidates: List[str]) -> Optional[float]:
    if df.empty:
        return None
    for column in candidates:
        if column in df.columns:
            series = pd.to_numeric(df[column], errors="coerce").dropna()
            if not series.empty:
                return safe_float(series.iloc[-1])
    return None


def summarize_revenue(df: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
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


def summarize_institutional(df: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
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


def summarize_margin(df: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
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


def fetch_finmind_bundle(stock_id: str, token: str, token_mode: str) -> Dict[str, object]:
    datasets = {
        "stock_info": ("TaiwanStockInfo", 3650),
        "month_revenue": ("TaiwanStockMonthRevenue", 1095),
        "financials": ("TaiwanStockFinancialStatements", 1095),
        "per": ("TaiwanStockPER", 365),
        "institutional": ("TaiwanStockInstitutionalInvestorsBuySell", 180),
        "margin": ("TaiwanStockMarginPurchaseShortSale", 180),
        "dividend": ("TaiwanStockDividend", 3650),
    }
    frames: Dict[str, pd.DataFrame] = {}
    errors: List[str] = []

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
        errors.insert(0, "未設定 FINMIND_TOKEN，已嘗試公開限制模式；部分資料可能受限。")

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


def build_context(symbol: str, period: str = "6mo") -> StockContext:
    stock_id = normalize_symbol(symbol)
    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    token, token_mode = get_finmind_token()
    history, metrics, y_status = fetch_yfinance_bundle(stock_id, period)
    finmind = fetch_finmind_bundle(stock_id, token, token_mode)

    return StockContext(
        stock_id=stock_id,
        stock_name=str(finmind["stock_name"]),
        industry=str(finmind["industry"]),
        last_updated=last_updated,
        price_history=history,
        latest_close=metrics["latest_close"],
        ma20=metrics["ma20"],
        ma60=metrics["ma60"],
        return_20d=metrics["return_20d"],
        average_volume=metrics["average_volume"],
        latest_revenue=finmind["latest_revenue"],
        revenue_growth=finmind["revenue_growth"],
        eps=finmind["eps"],
        pe_ratio=finmind["pe_ratio"],
        foreign_buy=finmind["foreign_buy"],
        institutional_net_buy=finmind["institutional_net_buy"],
        margin_balance_change=finmind["margin_balance_change"],
        short_balance_change=finmind["short_balance_change"],
        dividend_summary=str(finmind["dividend_summary"]),
        source_status=[y_status, finmind["status"]],
        finmind_errors=list(finmind["errors"]),
        finmind_token_mode=token_mode,
    )


def run_agents(context: StockContext) -> Tuple[Dict[str, str], str, List[Tuple[str, str, str]], Dict[str, List[str]]]:
    support_reasons: List[str] = []
    risks: List[str] = []
    watch_points: List[str] = []
    score = 0

    if context.latest_close is not None and context.ma20 is not None:
        if context.latest_close >= context.ma20:
            score += 1
            support_reasons.append("收盤價站上 20 日均線，短線技術面偏強。")
        else:
            score -= 1
            risks.append("收盤價跌破 20 日均線，短線動能轉弱。")
    else:
        watch_points.append("股價或均線資料暫無，技術面可靠度下降。")

    if context.ma20 is not None and context.ma60 is not None:
        if context.ma20 >= context.ma60:
            score += 1
            support_reasons.append("20 日均線高於 60 日均線，中期趨勢仍有支撐。")
        else:
            risks.append("20 日均線低於 60 日均線，中期趨勢偏弱。")

    if context.return_20d is not None:
        if context.return_20d > 18:
            score -= 1
            risks.append("近 20 日漲幅過大，短線追價風險升高。")
        elif context.return_20d > 5:
            score += 1
            support_reasons.append("近 20 日報酬率為正且具動能。")
        elif context.return_20d < -5:
            score -= 1
            risks.append("近 20 日報酬率明顯轉弱。")

    if context.revenue_growth is not None:
        if context.revenue_growth > 5:
            score += 1
            support_reasons.append("月營收年增率為正，基本面成長訊號較佳。")
        else:
            risks.append("月營收成長不強，需追蹤後續營運表現。")
    else:
        watch_points.append("月營收資料暫無，不以 0 視為衰退。")

    if context.eps is not None:
        if context.eps > 3:
            score += 1
            support_reasons.append("EPS 表現具獲利支撐。")
        elif context.eps > 0:
            support_reasons.append("EPS 為正，但獲利強度仍需與同業比較。")
        else:
            score -= 1
            risks.append("EPS 偏弱或為負，基本面需保守解讀。")
    else:
        watch_points.append("EPS 資料暫無，基本面結論可靠度下降。")

    if context.pe_ratio is not None and context.pe_ratio >= 30:
        score -= 1
        risks.append("本益比偏高，評價面可能已反映較多成長預期。")

    if context.foreign_buy is not None:
        if context.foreign_buy > 0:
            score += 1
            support_reasons.append("外資最近一日呈現買超，籌碼面偏正向。")
        elif context.foreign_buy < 0:
            score -= 1
            risks.append("外資最近一日賣超，籌碼面偏保守。")
    else:
        watch_points.append("法人買賣超資料暫無，籌碼結論可靠度下降。")

    if context.institutional_net_buy is not None and context.institutional_net_buy < 0:
        risks.append("三大法人合計偏賣超，需留意籌碼壓力。")

    if (
        context.margin_balance_change is not None
        and context.latest_close is not None
        and context.ma20 is not None
        and context.margin_balance_change > 0
        and context.latest_close < context.ma20
    ):
        score -= 1
        risks.append("融資增加但股價跌破 20 日均線，可能代表追價後轉弱。")
    elif context.margin_balance_change is None:
        watch_points.append("融資融券資料暫無，無法完整評估信用交易風險。")

    if context.average_volume is not None and context.average_volume < 1_000_000:
        risks.append("近 20 日平均成交量偏低，流動性可能不足。")

    failed_sources = [status.message for status in context.source_status if not status.ok]
    if failed_sources:
        risks.append("資料來源有失敗項目，報告應視為降級分析。")
        watch_points.extend(failed_sources)

    available_signal_count = sum(
        [
            context.latest_close is not None and context.ma20 is not None,
            context.ma20 is not None and context.ma60 is not None,
            context.return_20d is not None,
            context.revenue_growth is not None,
            context.eps is not None,
            context.foreign_buy is not None,
        ]
    )

    if available_signal_count < 2:
        final_rating = "中立"
        watch_points.append("可用分析訊號不足，總結決策採中立。")
    elif score >= 4:
        final_rating = "偏多"
    elif score <= -2:
        final_rating = "偏空"
    else:
        final_rating = "中立"

    if not support_reasons:
        support_reasons.append("目前可用資料尚不足以形成明確偏多理由。")
    if not risks:
        risks.append("未出現重大規則式風險，但仍需注意資料延遲與市場波動。")
    if not watch_points:
        watch_points.append("追蹤下一期月營收、法人買賣超與均線變化。")

    agents = {
        "資料整合 Agent": f"已整合 {YFINANCE_SOURCE} 與 {FINMIND_SOURCE}。股價資料：{context.source_status[0].message} FinMind：{context.source_status[1].message}",
        "技術分析 Agent": f"最新收盤 {fmt_number(context.latest_close)}，MA20 {fmt_number(context.ma20)}，MA60 {fmt_number(context.ma60)}，20 日報酬率 {fmt_number(context.return_20d, suffix='%')}。",
        "基本面 Agent": f"月營收 {fmt_number(context.latest_revenue, decimals=0)}，月營收成長率 {fmt_number(context.revenue_growth, suffix='%')}，EPS {fmt_number(context.eps)}，本益比 {fmt_number(context.pe_ratio)}。",
        "籌碼分析 Agent": f"外資買賣超 {fmt_number(context.foreign_buy, decimals=0)}，三大法人合計 {fmt_number(context.institutional_net_buy, decimals=0)}，融資餘額變化 {fmt_number(context.margin_balance_change, decimals=0)}，融券餘額變化 {fmt_number(context.short_balance_change, decimals=0)}。",
        "風險控管 Agent": "反方意見：" + "；".join(risks),
        "總結決策 Agent": f"綜合技術、基本面、籌碼與風險後，規則式結論為：{final_rating}。此結論不構成買賣建議。",
    }

    debate = [
        ("技術分析 Agent", f"支持觀點：均線與短期報酬率可快速判斷趨勢。目前觀察為：{agents['技術分析 Agent']}", "info"),
        ("基本面 Agent", f"補充觀點：營收、EPS 與評價面決定研究品質。{agents['基本面 Agent']}", "info"),
        ("籌碼分析 Agent", f"資金觀點：法人與信用交易可觀察短期資金方向。{agents['籌碼分析 Agent']}", "info"),
        ("風險控管 Agent", "反方觀點：" + "；".join(risks), "warning"),
        ("總結決策 Agent", f"總結觀點：本次整合判斷為「{final_rating}」，需搭配資料限制與免責聲明解讀。", "success"),
    ]

    decision = {
        "support_reasons": support_reasons,
        "risks": risks,
        "watch_points": watch_points,
    }
    return agents, final_rating, debate, decision


def generate_markdown_report(
    context: StockContext,
    agents: Dict[str, str],
    final_rating: str,
    debate: List[Tuple[str, str, str]],
    decision: Dict[str, List[str]],
) -> str:
    source_items = "\n".join(
        f"- {status.name}：{'成功' if status.ok else '降級'}，{status.message}" for status in context.source_status
    )
    agent_sections = "\n\n".join(f"### {name}\n{content}" for name, content in agents.items())
    debate_sections = "\n".join(f"- **{speaker}**：{message}" for speaker, message, _tone in debate)
    support_items = "\n".join(f"- {item}" for item in decision["support_reasons"])
    risk_items = "\n".join(f"- {item}" for item in decision["risks"])
    watch_items = "\n".join(f"- {item}" for item in decision["watch_points"])
    finmind_errors = "\n".join(f"- {error}" for error in context.finmind_errors) or "- 無"

    return f"""# {context.stock_id} {context.stock_name} 多 Agent 台股研究報告

## 一、資料摘要
- 股票代號：{context.stock_id}
- 股票名稱：{context.stock_name}
- 產業分類：{context.industry}
- 最後更新時間：{context.last_updated}
- 股價資料來源：{YFINANCE_SOURCE}
- 基本面與籌碼資料來源：{FINMIND_SOURCE}
- 最新收盤價：{fmt_number(context.latest_close)}
- MA20：{fmt_number(context.ma20)}
- MA60：{fmt_number(context.ma60)}
- 20 日報酬率：{fmt_number(context.return_20d, suffix="%")}
- 平均成交量：{fmt_number(context.average_volume, decimals=0)}
- 月營收成長率：{fmt_number(context.revenue_growth, suffix="%")}
- EPS：{fmt_number(context.eps)}
- 本益比：{fmt_number(context.pe_ratio)}
- 外資買賣超：{fmt_number(context.foreign_buy, decimals=0)}
- 融資餘額變化：{fmt_number(context.margin_balance_change, decimals=0)}
- 股利資料：{context.dividend_summary}

## 二、資料來源與取得狀態
{source_items}

### FinMind 降級提示
{finmind_errors}

## 三、多 Agent 分析
{agent_sections}

## 四、Agent 辯論室
{debate_sections}

## 五、最終研究結論
### 綜合評級：{final_rating}

#### 支持理由
{support_items}

#### 反方風險
{risk_items}

#### 觀察重點
{watch_items}

## 六、資料限制與免責聲明
{DATA_DELAY_NOTE}

{DISCLAIMER}
"""


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #080d16;
            --panel: #101826;
            --panel-2: #132033;
            --line: rgba(148, 163, 184, 0.26);
            --text: #edf4ff;
            --muted: #94a3b8;
            --blue: #38bdf8;
            --green: #34d399;
            --amber: #fbbf24;
            --red: #fb7185;
        }
        .stApp {
            background:
                radial-gradient(circle at 15% 0%, rgba(56, 189, 248, .18), transparent 32%),
                radial-gradient(circle at 85% 8%, rgba(52, 211, 153, .12), transparent 30%),
                linear-gradient(180deg, #080d16 0%, #0b1120 100%);
        }
        .block-container { padding-top: 1.25rem; padding-bottom: 3rem; max-width: 1220px; }
        [data-testid="stSidebar"] { background: #0b1020; border-right: 1px solid var(--line); }
        [data-testid="stSidebar"] * { color: #e5eefb !important; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label {
            font-size: 13px;
            letter-spacing: 0;
        }
        [data-testid="stSidebar"] input, [data-testid="stSidebar"] [role="combobox"] {
            background: #0f172a !important;
            border: 1px solid rgba(148, 163, 184, .35) !important;
            color: #f8fafc !important;
            border-radius: 8px !important;
        }
        .hero {
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(56, 189, 248, .32);
            border-radius: 14px;
            padding: 30px;
            background:
                linear-gradient(135deg, rgba(15,23,42,.96), rgba(12,48,70,.92)),
                repeating-linear-gradient(90deg, rgba(255,255,255,.04) 0, rgba(255,255,255,.04) 1px, transparent 1px, transparent 58px);
            box-shadow: 0 24px 70px rgba(0, 0, 0, .28);
            margin-bottom: 18px;
        }
        .hero h1 { color: #ffffff; margin: 0 0 10px; letter-spacing: 0; font-size: 44px; line-height: 1.12; }
        .hero p { color: #c7d2fe; margin: 0; font-size: 17px; line-height: 1.75; max-width: 820px; }
        .hero-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin-top: 22px;
        }
        .value-card {
            border: 1px solid rgba(148, 163, 184, .28);
            border-radius: 12px;
            padding: 14px;
            background: rgba(15, 23, 42, .72);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.04);
        }
        .value-card strong { display: block; color: #f8fafc; margin-bottom: 6px; }
        .value-card span { color: #a7b6cb; font-size: 13px; line-height: 1.55; }
        .status-pill {
            display: inline-flex;
            margin: 18px 8px 0 0;
            border: 1px solid rgba(56, 189, 248, .28);
            border-radius: 999px;
            padding: 7px 12px;
            color: #dbeafe;
            background: rgba(14, 165, 233, .12);
            font-size: 13px;
            font-weight: 800;
        }
        .section-title { font-size: 22px; font-weight: 900; margin: 24px 0 12px; color: #f8fafc; letter-spacing: 0; }
        .section-kicker { color: #38bdf8; font-size: 13px; font-weight: 900; margin-bottom: 4px; }
        [data-testid="stMetric"] {
            border: 1px solid rgba(148, 163, 184, .24);
            border-radius: 14px;
            padding: 15px 16px;
            background: linear-gradient(180deg, rgba(15,23,42,.95), rgba(15,23,42,.78));
            box-shadow: 0 12px 34px rgba(0,0,0,.18);
            min-height: 112px;
        }
        [data-testid="stMetric"] * { color: #f8fafc !important; }
        [data-testid="stMetricLabel"] { color: #93c5fd !important; font-weight: 800; }
        [data-testid="stAlert"] {
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, .22);
        }
        [data-testid="stTabs"] button {
            color: #cbd5e1 !important;
            border-radius: 10px 10px 0 0;
            font-weight: 800;
        }
        [data-testid="stTabs"] button[aria-selected="true"] {
            color: #ffffff !important;
            border-bottom-color: #38bdf8 !important;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid rgba(148, 163, 184, .22);
            border-radius: 12px;
            overflow: hidden;
        }
        .chart-shell {
            border: 1px solid rgba(148, 163, 184, .22);
            border-radius: 14px;
            background: linear-gradient(180deg, rgba(15, 23, 42, .9), rgba(2, 6, 23, .82));
            padding: 12px 12px 2px;
            box-shadow: 0 18px 44px rgba(0,0,0,.2);
            margin-top: 8px;
        }
        .panel-note {
            color: #93a4b8;
            font-size: 13px;
            line-height: 1.7;
            margin: -4px 0 12px;
        }
        .agent-card {
            border: 1px solid rgba(148, 163, 184, .24);
            border-radius: 14px;
            padding: 16px;
            background: rgba(15, 23, 42, .82);
            margin-bottom: 12px;
            box-shadow: 0 14px 36px rgba(0,0,0,.16);
        }
        .flow-card {
            border: 1px solid rgba(148, 163, 184, .22);
            border-radius: 14px;
            padding: 15px 16px;
            background:
                linear-gradient(180deg, rgba(15,23,42,.88), rgba(15,23,42,.66));
            margin-bottom: 12px;
            min-height: 116px;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.04);
        }
        .flow-card .step {
            color: #38bdf8;
            font-size: 12px;
            font-weight: 900;
            letter-spacing: .08em;
        }
        .flow-card h4 {
            margin: 8px 0 6px;
            color: #f8fafc;
            font-size: 16px;
        }
        .flow-card p {
            margin: 0;
            color: #9fb0c7;
            font-size: 13px;
            line-height: 1.65;
        }
        .agent-card h4 { margin: 0 0 8px; color: #f8fafc; }
        .agent-card p { color: #cbd5e1; line-height: 1.7; margin: 6px 0; }
        .agent-badge {
            display: inline-block;
            border-radius: 999px;
            padding: 4px 9px;
            background: rgba(56, 189, 248, .14);
            color: #7dd3fc;
            font-weight: 900;
            font-size: 12px;
            margin-bottom: 8px;
        }
        .chat-card {
            border: 1px solid rgba(148, 163, 184, .22);
            border-radius: 14px;
            padding: 15px 16px;
            background: rgba(15, 23, 42, .82);
            margin-bottom: 12px;
        }
        .chat-card strong { color: #f8fafc; }
        .chat-card p { color: #cbd5e1; line-height: 1.75; margin: 7px 0 0; }
        .chat-support { border-left: 5px solid var(--blue); }
        .chat-risk { border-left: 5px solid var(--amber); }
        .chat-summary { border-left: 5px solid var(--green); }
        .report-box {
            border: 1px solid rgba(148, 163, 184, .24);
            border-radius: 14px;
            background: rgba(15, 23, 42, .82);
            padding: 18px;
        }
        .decision-hero {
            border: 1px solid rgba(56, 189, 248, .28);
            border-radius: 14px;
            padding: 18px 20px;
            background: linear-gradient(135deg, rgba(14,165,233,.16), rgba(15,23,42,.82));
            margin: 8px 0 16px;
        }
        .decision-hero span {
            color: #93c5fd;
            font-size: 13px;
            font-weight: 900;
        }
        .decision-hero h3 {
            margin: 5px 0 0;
            color: #ffffff;
            font-size: 24px;
        }
        @media (max-width: 900px) {
            .hero h1 { font-size: 32px; }
            .hero-grid { grid-template-columns: 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(kicker: str, title: str) -> None:
    st.markdown(f'<div class="section-kicker">{kicker}</div><div class="section-title">{title}</div>', unsafe_allow_html=True)


def render_hero(context: Optional[StockContext] = None, final_rating: Optional[str] = None) -> None:
    stock = f"{context.stock_id} {context.stock_name}" if context else "等待輸入股票代碼"
    updated = context.last_updated if context else "尚未更新"
    rating = final_rating if final_rating else "等待分析"
    st.markdown(
        f"""
        <section class="hero">
            <h1>{APP_TITLE}</h1>
            <p>{APP_SUBTITLE}</p>
            <div class="hero-grid">
                <div class="value-card"><strong>資料一鍵更新</strong><span>串接 yfinance 與 FinMind，將股價、基本面與籌碼資料整合到同一個研究流程。</span></div>
                <div class="value-card"><strong>多 Agent 協作</strong><span>技術、基本面、籌碼與風險角色分工，讓分析邏輯更容易展示與說明。</span></div>
                <div class="value-card"><strong>研究報告輸出</strong><span>自動整理支持理由、反方風險、觀察重點與 Markdown 報告下載。</span></div>
            </div>
            <span class="status-pill">目前標的：{stock}</span>
            <span class="status-pill">綜合評級：{rating}</span>
            <span class="status-pill">最後更新：{updated}</span>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> Tuple[str, str, bool]:
    period_options = {"3 個月": "3mo", "6 個月": "6mo", "1 年": "1y"}
    with st.sidebar:
        st.header("研究設定")
        symbol = st.text_input("股票代碼", value="2330", help="例如 2330、2317、2454。")
        period_label = st.selectbox("資料期間", list(period_options.keys()), index=1)
        st.caption("資料期間會套用在股價、成交量與均線分析。")
        _, token_status = get_finmind_token()
        st.info(f"Token 狀態：{token_status}")
        with st.expander("資料來源", expanded=False):
            st.write(f"股價資料：{YFINANCE_SOURCE}")
            st.write(f"基本面與籌碼：{FINMIND_SOURCE}")
            st.write("Token 由系統管理者設定，不由使用者輸入。")
        st.warning("免責提醒：本系統僅供課堂展示、學術研究與投資參考。")
        start = st.button("更新資料", type="primary", use_container_width=True)
    return symbol, period_options[period_label], start


def render_status_strip(context: StockContext) -> None:
    cols = st.columns(4)
    for index, status in enumerate(context.source_status[:2]):
        if status.ok:
            cols[index].success(status.message)
        else:
            cols[index].warning(status.message)
    cols[2].info(f"Token 狀態：{context.finmind_token_mode}")
    cols[3].info(f"最後更新：{context.last_updated}")


def render_metrics(context: StockContext) -> None:
    render_section_header("MARKET SNAPSHOT", "快速總覽")
    first = st.columns(4)
    first[0].metric("最新收盤價", fmt_number(context.latest_close))
    first[1].metric("20 日報酬率", fmt_number(context.return_20d, suffix="%"))
    first[2].metric("MA20", fmt_number(context.ma20))
    first[3].metric("MA60", fmt_number(context.ma60))
    second = st.columns(4)
    second[0].metric("EPS", fmt_number(context.eps))
    second[1].metric("本益比", fmt_number(context.pe_ratio))
    second[2].metric("月營收成長率", fmt_number(context.revenue_growth, suffix="%"))
    second[3].metric("外資買賣超", fmt_number(context.foreign_buy, decimals=0))


def render_source_panel(context: StockContext) -> None:
    st.info(f"資料來源：股價使用 {YFINANCE_SOURCE}；基本面、月營收、法人買賣超、融資融券使用 {FINMIND_SOURCE}。")
    with st.expander("系統狀態與降級說明", expanded=False):
        for status in context.source_status:
            if status.ok:
                st.success(f"{status.name}：{status.message}")
            else:
                st.warning(f"{status.name}：{status.message}")
        if context.finmind_errors:
            st.warning("FinMind 部分資料取得失敗，系統已保留可用資料並降級分析。")
            for error in context.finmind_errors:
                st.write(f"- {error}")
        st.warning(DATA_DELAY_NOTE)
        st.info(DISCLAIMER)


def price_chart_data(context: StockContext) -> pd.DataFrame:
    if context.price_history.empty:
        return pd.DataFrame()
    data = context.price_history.copy().reset_index()
    date_col = data.columns[0]
    data["日期"] = data[date_col].astype(str)
    return data


def apply_plotly_theme(fig: go.Figure, title: str, y_title: str = "") -> go.Figure:
    fig.update_layout(
        title={"text": title, "font": {"size": 18, "color": "#f8fafc"}},
        template="plotly_dark",
        height=430,
        margin={"l": 28, "r": 18, "t": 54, "b": 34},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(2,6,23,0.45)",
        font={"color": "#cbd5e1", "family": "Arial, sans-serif"},
        hovermode="x unified",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "font": {"size": 12},
        },
        xaxis={
            "showgrid": True,
            "gridcolor": "rgba(148,163,184,0.12)",
            "zeroline": False,
            "rangeslider": {"visible": False},
        },
        yaxis={
            "title": y_title,
            "showgrid": True,
            "gridcolor": "rgba(148,163,184,0.12)",
            "zeroline": False,
        },
    )
    return fig


def render_plotly_chart(fig: go.Figure) -> None:
    st.markdown('<div class="chart-shell">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)


def render_charts(context: StockContext) -> None:
    render_section_header("MARKET ANALYTICS", "市場圖表")
    st.markdown('<p class="panel-note">以深色金融圖表呈現價格、成交量、均線與資料表，方便課堂 Demo 快速切換觀察重點。</p>', unsafe_allow_html=True)
    tabs = st.tabs(["股價走勢", "成交量", "均線分析", "法人籌碼", "基本面資料"])
    chart_data = price_chart_data(context)

    with tabs[0]:
        if chart_data.empty or "Close" not in chart_data:
            st.warning("股價資料暫無，技術圖表已降級。")
        else:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=chart_data["日期"],
                    y=pd.to_numeric(chart_data["Close"], errors="coerce"),
                    mode="lines",
                    name="收盤價",
                    line={"color": "#38bdf8", "width": 2.4},
                    fill="tozeroy",
                    fillcolor="rgba(56,189,248,0.08)",
                )
            )
            render_plotly_chart(apply_plotly_theme(fig, "股價走勢", "價格"))

    with tabs[1]:
        if chart_data.empty or "Volume" not in chart_data:
            st.warning("成交量資料暫無。")
        else:
            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    x=chart_data["日期"],
                    y=pd.to_numeric(chart_data["Volume"], errors="coerce"),
                    name="成交量",
                    marker={"color": "#34d399", "opacity": 0.76},
                )
            )
            render_plotly_chart(apply_plotly_theme(fig, "成交量", "股數"))

    with tabs[2]:
        if chart_data.empty or "Close" not in chart_data:
            st.warning("均線資料暫無。")
        else:
            ma_data = chart_data[["日期", "Close"]].copy()
            close = pd.to_numeric(ma_data["Close"], errors="coerce")
            ma_data["MA20"] = close.rolling(20).mean()
            ma_data["MA60"] = close.rolling(60).mean()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ma_data["日期"], y=close, mode="lines", name="收盤價", line={"color": "#e2e8f0", "width": 2}))
            fig.add_trace(go.Scatter(x=ma_data["日期"], y=ma_data["MA20"], mode="lines", name="MA20", line={"color": "#38bdf8", "width": 2}))
            fig.add_trace(go.Scatter(x=ma_data["日期"], y=ma_data["MA60"], mode="lines", name="MA60", line={"color": "#fbbf24", "width": 2}))
            render_plotly_chart(apply_plotly_theme(fig, "均線分析", "價格"))

    with tabs[3]:
        chip_df = pd.DataFrame(
            [
                {"項目": "外資買賣超", "數值": fmt_number(context.foreign_buy, decimals=0)},
                {"項目": "三大法人買賣超", "數值": fmt_number(context.institutional_net_buy, decimals=0)},
                {"項目": "融資餘額變化", "數值": fmt_number(context.margin_balance_change, decimals=0)},
                {"項目": "融券餘額變化", "數值": fmt_number(context.short_balance_change, decimals=0)},
            ]
        )
        st.dataframe(chip_df, use_container_width=True, hide_index=True)

    with tabs[4]:
        fundamental_df = pd.DataFrame(
            [
                {"項目": "月營收", "數值": fmt_number(context.latest_revenue, decimals=0)},
                {"項目": "月營收成長率", "數值": fmt_number(context.revenue_growth, suffix="%")},
                {"項目": "EPS", "數值": fmt_number(context.eps)},
                {"項目": "本益比", "數值": fmt_number(context.pe_ratio)},
                {"項目": "股利摘要", "數值": context.dividend_summary},
            ]
        )
        st.dataframe(fundamental_df, use_container_width=True, hide_index=True)


def agent_specs(context: StockContext, agents: Dict[str, str], final_rating: str, decision: Dict[str, List[str]]) -> List[Dict[str, str]]:
    return [
        {"name": "資料整合 Agent", "role": "整合資料源並監控降級狀態", "data": "yfinance、FinMind", "observation": agents.get("資料整合 Agent", "資料暫無"), "conclusion": "資料可用時進入完整分析，失敗時保留可用資訊。", "level": "高" if all(s.ok for s in context.source_status) else "中"},
        {"name": "技術分析 Agent", "role": "判讀價格趨勢與短線動能", "data": "收盤價、均線、成交量、20 日報酬率", "observation": agents.get("技術分析 Agent", "資料暫無"), "conclusion": "用趨勢與動能建立第一層市場判讀。", "level": "高" if context.latest_close is not None else "低"},
        {"name": "基本面 Agent", "role": "評估營運成長、獲利與評價", "data": "月營收、EPS、本益比、股利", "observation": agents.get("基本面 Agent", "資料暫無"), "conclusion": "缺資料不視為負面，改列為資料限制。", "level": "高" if context.eps is not None else "低"},
        {"name": "籌碼分析 Agent", "role": "觀察法人與信用交易變化", "data": "外資、三大法人、融資融券", "observation": agents.get("籌碼分析 Agent", "資料暫無"), "conclusion": "用資金流向補足短期市場結構。", "level": "高" if context.foreign_buy is not None else "低"},
        {"name": "風險控管 Agent", "role": "提出反方意見與壓力情境", "data": "技術、基本面、籌碼與資料缺口", "observation": "；".join(decision["risks"]), "conclusion": "避免只看正面訊號，保留風險解讀。", "level": "中"},
        {"name": "總結決策 Agent", "role": "整合多方觀點形成研究結論", "data": "所有 Agent 輸出", "observation": agents.get("總結決策 Agent", "資料暫無"), "conclusion": f"本次綜合評級為：{final_rating}", "level": "中"},
    ]


def render_agent_flow() -> None:
    render_section_header("AGENT PIPELINE", "多 Agent 分工流程")
    st.markdown('<p class="panel-note">從資料整合到總結決策，每個 Agent 負責不同分析視角，讓老師能一眼看懂系統價值。</p>', unsafe_allow_html=True)
    steps = [
        ("01", "資料整合", "取得資料並檢查降級"),
        ("02", "技術分析", "判讀股價與均線"),
        ("03", "基本面", "分析營收與獲利"),
        ("04", "籌碼", "觀察法人與融資"),
        ("05", "風險控管", "提出反方情境"),
        ("06", "總結決策", "產生研究評級"),
    ]
    cols = st.columns(3)
    for index, (number, title, body) in enumerate(steps):
        with cols[index % 3]:
            st.markdown(
                f"""
                <div class="flow-card">
                    <div class="step">AGENT {number}</div>
                    <h4>{title}</h4>
                    <p>{body}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_agent_outputs(context: StockContext, agents: Dict[str, str], final_rating: str, decision: Dict[str, List[str]]) -> None:
    render_section_header("AGENT BRIEFING", "多 Agent 分析")
    for spec in agent_specs(context, agents, final_rating, decision):
        st.markdown(
            f"""
            <div class="agent-card">
                <span class="agent-badge">信心程度：{spec['level']}</span>
                <h4>{spec['name']}</h4>
                <p><strong>角色定位：</strong>{spec['role']}</p>
                <p><strong>使用資料：</strong>{spec['data']}</p>
                <p><strong>主要觀察：</strong>{spec['observation']}</p>
                <p><strong>結論：</strong>{spec['conclusion']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_debate(debate: List[Tuple[str, str, str]]) -> None:
    render_section_header("DEBATE ROOM", "Agent 辯論室")
    for speaker, message, tone in debate:
        css = "chat-risk" if tone == "warning" else "chat-summary" if tone == "success" else "chat-support"
        label = "反方觀點" if tone == "warning" else "總結觀點" if tone == "success" else "支持觀點"
        st.markdown(
            f"""
            <div class="chat-card {css}">
                <strong>{speaker}｜{label}</strong>
                <p>{message}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_decision(context: StockContext, final_rating: str, decision: Dict[str, List[str]], report: str) -> None:
    render_section_header("RESEARCH REPORT", "最終研究報告")
    st.markdown(
        f"""
        <div class="decision-hero">
            <span>{context.stock_id}｜{context.stock_name}｜規則式多 Agent 研究結論</span>
            <h3>綜合評級：{final_rating}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if final_rating == "偏多":
        st.success(f"綜合評級：{final_rating}")
    elif final_rating == "偏空":
        st.warning(f"綜合評級：{final_rating}")
    else:
        st.info(f"綜合評級：{final_rating}")

    cols = st.columns(3)
    with cols[0]:
        st.subheader("支持理由")
        for item in decision["support_reasons"]:
            st.success(item)
    with cols[1]:
        st.subheader("反方風險")
        for item in decision["risks"]:
            st.warning(item)
    with cols[2]:
        st.subheader("觀察重點")
        for item in decision["watch_points"]:
            st.info(item)

    with st.expander("資料來源與免責聲明", expanded=True):
        st.write(f"股價資料來源：{YFINANCE_SOURCE}")
        st.write(f"基本面與籌碼資料來源：{FINMIND_SOURCE}")
        st.warning(DATA_DELAY_NOTE)
        st.info(DISCLAIMER)

    st.download_button(
        "下載 Markdown 研究報告",
        data=report.encode("utf-8"),
        file_name=f"{context.stock_id}_analysis_report.md",
        mime="text/markdown",
        use_container_width=True,
    )


def render_empty_state() -> None:
    render_section_header("DEMO READY", "展示起點")
    cols = st.columns(3)
    cols[0].success("輸入股票代碼後即可更新研究資料。")
    cols[1].info("系統會以多 Agent 方式拆解技術、基本面、籌碼與風險。")
    cols[2].warning("所有研究結果皆附資料限制與免責聲明。")


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    apply_styles()
    symbol, period, start = render_sidebar()

    if not start and "analysis" not in st.session_state:
        render_hero()
        render_empty_state()
        return

    if start:
        stock_id = normalize_symbol(symbol)
        if not is_valid_tw_symbol(stock_id):
            render_hero()
            st.error("股票代碼格式不正確。請輸入 4 到 6 位數的台股代號，例如 2330。")
            return
        try:
            with st.spinner("正在更新資料，並交由多 Agent 分析..."):
                context = build_context(stock_id, period)
                agents, final_rating, debate, decision = run_agents(context)
                report = generate_markdown_report(context, agents, final_rating, debate, decision)
                st.session_state["analysis"] = {
                    "context": context,
                    "agents": agents,
                    "final_rating": final_rating,
                    "debate": debate,
                    "decision": decision,
                    "report": report,
                }
        except Exception:
            render_hero()
            st.error("系統暫時無法完成分析，請稍後再試。")
            st.info("錯誤已被攔截，App 不會崩潰。請確認網路連線、套件安裝與資料來源狀態。")
            return

    analysis = st.session_state["analysis"]
    context: StockContext = analysis["context"]
    agents: Dict[str, str] = analysis["agents"]
    final_rating: str = analysis["final_rating"]
    debate: List[Tuple[str, str, str]] = analysis["debate"]
    decision: Dict[str, List[str]] = analysis["decision"]
    report: str = analysis["report"]

    render_hero(context, final_rating)
    render_status_strip(context)
    render_source_panel(context)

    main_tabs = st.tabs(["快速總覽", "市場圖表", "多 Agent 分析", "Agent 辯論室", "最終研究報告"])
    with main_tabs[0]:
        render_metrics(context)
        render_agent_flow()
    with main_tabs[1]:
        render_charts(context)
    with main_tabs[2]:
        render_agent_outputs(context, agents, final_rating, decision)
    with main_tabs[3]:
        render_debate(debate)
    with main_tabs[4]:
        render_decision(context, final_rating, decision, report)
        with st.expander("查看完整 Markdown 報告", expanded=False):
            st.markdown(report)


if __name__ == "__main__":
    main()
