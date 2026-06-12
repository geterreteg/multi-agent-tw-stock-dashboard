"use client";

import { useMemo, useState } from "react";
import type { MouseEvent, ReactNode } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { AnalyzeResponse } from "@/lib/types";

const axisStyle = { fill: "#64748b", fontSize: 12 };
type ChartMode = "close" | "candlestick";
type ScenarioDirection = "偏多" | "中性整理" | "偏弱";
type ScenarioConfidence = "高" | "中" | "低";

type ScenarioCard = {
  title: string;
  trigger: string;
  path: string;
  watch: string;
  tone: "bullish" | "neutral" | "weak";
};

type TechnicalScenario = {
  direction: ScenarioDirection;
  confidence: ScenarioConfidence;
  confidenceNote: string;
  reasons: string[];
  cards: ScenarioCard[];
  dataLimited: boolean;
};

export function StockCharts({ data }: { data: AnalyzeResponse }) {
  const [chartMode, setChartMode] = useState<ChartMode>("close");
  const scenario = useMemo(() => buildTechnicalScenario(data), [data]);

  return (
    <div className="grid gap-5">
      <section className="grid gap-5 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <ChartPanel
          title="股價走勢"
          description="觀察收盤價趨勢與日 K 結構，是本頁主要市場價格視圖。"
          featured
          action={<ChartModeSwitch value={chartMode} onChange={setChartMode} />}
        >
          {chartMode === "close" ? (
            <ResponsiveContainer width="100%" height={380}>
              <AreaChart data={data.charts.price}>
                <defs>
                  <linearGradient id="priceGradient" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(148,163,184,.12)" vertical={false} />
                <XAxis dataKey="date" tick={axisStyle} tickLine={false} axisLine={false} minTickGap={28} />
                <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={48} />
                <Tooltip contentStyle={tooltipStyle} />
                <Area type="monotone" dataKey="close" stroke="#22d3ee" fill="url(#priceGradient)" strokeWidth={2.2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <CandlestickChart data={data.charts.price} />
          )}
        </ChartPanel>
        <div className="grid gap-5">
          <ChartPanel title="成交量" description="輔助判斷價格移動背後是否有量能支持。" muted>
            <ResponsiveContainer width="100%" height={185}>
              <BarChart data={data.charts.volume} margin={{ left: 8, right: 4 }}>
                <CartesianGrid stroke="rgba(148,163,184,.12)" vertical={false} />
                <XAxis dataKey="date" tick={axisStyle} tickLine={false} axisLine={false} minTickGap={28} />
                <YAxis tick={axisStyle} tickLine={false} axisLine={false} tickFormatter={formatVolumeAxis} width={58} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="volume" fill="#34d399" opacity={0.52} radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartPanel>
          <ChartPanel title="均線位置" description="比較 MA20 與 MA60，輔助辨識短中期趨勢結構。" muted>
            <ResponsiveContainer width="100%" height={185}>
              <LineChart data={data.charts.movingAverage}>
                <CartesianGrid stroke="rgba(148,163,184,.12)" vertical={false} />
                <XAxis dataKey="date" tick={axisStyle} tickLine={false} axisLine={false} minTickGap={28} />
                <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={48} />
                <Tooltip contentStyle={tooltipStyle} />
                <Line type="monotone" dataKey="ma20" name="MA20" stroke="#22d3ee" dot={false} strokeWidth={2} />
                <Line type="monotone" dataKey="ma60" name="MA60" stroke="#fbbf24" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </ChartPanel>
        </div>
      </section>
      <TechnicalScenarioPanel scenario={scenario} />
    </div>
  );
}

function ChartPanel({
  title,
  description,
  children,
  action,
  featured = false,
  muted = false,
}: {
  title: string;
  description: string;
  children: ReactNode;
  action?: ReactNode;
  featured?: boolean;
  muted?: boolean;
}) {
  return (
    <section
      className={`rounded-3xl border p-5 shadow-glass ${
        featured
          ? "border-cyan-300/15 bg-white/[.055]"
          : muted
            ? "border-white/[.07] bg-slate-950/35"
            : "border-white/[.08] bg-white/[.045]"
      }`}
    >
      <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className={featured ? "text-lg font-semibold text-white" : "text-base font-semibold text-white"}>{title}</h2>
          <p className="mt-2 text-xs leading-5 text-slate-500">{description}</p>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

function ChartModeSwitch({ value, onChange }: { value: ChartMode; onChange: (value: ChartMode) => void }) {
  const options: Array<{ value: ChartMode; label: string }> = [
    { value: "close", label: "收盤走勢" },
    { value: "candlestick", label: "K 線圖" },
  ];

  return (
    <div className="flex w-fit rounded-full border border-white/[.1] bg-slate-950/60 p-1 shadow-inner shadow-black/30">
      {options.map((option) => {
        const isActive = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={`rounded-full border px-4 py-2 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-200/70 ${
              isActive
                ? "border-cyan-200/70 bg-cyan-100 text-slate-950 shadow-[0_0_0_1px_rgba(103,232,249,.2),0_10px_28px_rgba(0,0,0,.26)]"
                : "border-transparent text-slate-400 hover:border-white/[.08] hover:bg-white/[.075] hover:text-slate-100 active:bg-white/[.1]"
            }`}
            aria-pressed={isActive}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

function TechnicalScenarioPanel({ scenario }: { scenario: TechnicalScenario }) {
  const badgeClass =
    scenario.direction === "偏多"
      ? "border-emerald-300/30 bg-emerald-300/[.12] text-emerald-100"
      : scenario.direction === "偏弱"
        ? "border-rose-300/30 bg-rose-300/[.12] text-rose-100"
        : "border-cyan-300/25 bg-cyan-300/[.1] text-cyan-100";

  return (
    <section className="rounded-3xl border border-white/[.08] bg-slate-950/35 p-5 shadow-glass">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">scenario analysis</p>
          <h3 className="mt-2 text-lg font-semibold text-white">K 線情境推演</h3>
          <p className="mt-2 max-w-3xl text-xs leading-6 text-slate-500">
            依既有日 K、均線、20 日報酬、成交量與資料來源品質，整理可能的技術情境，不新增資料請求。
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className={`rounded-full border px-3 py-1.5 text-sm font-semibold ${badgeClass}`}>目前推演方向：{scenario.direction}</span>
          <span className="rounded-full border border-white/[.08] bg-black/20 px-3 py-1.5 text-sm font-medium text-slate-200">推演信心：{scenario.confidence}</span>
        </div>
      </div>

      {scenario.dataLimited ? (
        <p className="mt-4 rounded-2xl border border-amber-300/15 bg-amber-300/[.045] p-3 text-xs leading-6 text-amber-100">
          資料不足，僅能提供保守情境推演。
        </p>
      ) : null}

      <div className="mt-5 grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.7fr)]">
        <div className="rounded-2xl border border-white/[.06] bg-black/20 p-4">
          <p className="text-sm font-semibold text-slate-100">判斷依據</p>
          <ul className="mt-3 grid gap-2 text-sm leading-6 text-slate-300">
            {scenario.reasons.map((reason) => (
              <li key={reason} className="flex gap-2">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-200/70" />
                <span>{reason}</span>
              </li>
            ))}
          </ul>
          <p className="mt-4 border-t border-white/[.07] pt-3 text-xs leading-6 text-slate-500">{scenario.confidenceNote}</p>
        </div>

        <div className="grid gap-3 lg:grid-cols-3">
          {scenario.cards.map((card) => (
            <ScenarioCardView key={card.title} card={card} />
          ))}
        </div>
      </div>

      <p className="mt-5 rounded-2xl border border-white/[.07] bg-white/[.035] p-3 text-xs leading-6 text-slate-400">
        此區塊為規則式情境推演，不代表未來價格保證。
      </p>
    </section>
  );
}

function ScenarioCardView({ card }: { card: ScenarioCard }) {
  const toneClass =
    card.tone === "bullish"
      ? "border-emerald-300/15 hover:border-emerald-200/35"
      : card.tone === "weak"
        ? "border-rose-300/15 hover:border-rose-200/35"
        : "border-cyan-300/15 hover:border-cyan-200/35";

  return (
    <article className={`rounded-2xl border bg-slate-950/35 p-4 transition-colors hover:bg-white/[.045] ${toneClass}`}>
      <h4 className="text-sm font-semibold text-white">{card.title}</h4>
      <dl className="mt-4 grid gap-3 text-xs leading-6">
        <div>
          <dt className="font-medium text-slate-500">觸發條件</dt>
          <dd className="mt-1 text-slate-200">{card.trigger}</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-500">可能走勢</dt>
          <dd className="mt-1 text-slate-200">{card.path}</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-500">觀察指標</dt>
          <dd className="mt-1 text-slate-200">{card.watch}</dd>
        </div>
      </dl>
    </article>
  );
}

function CandlestickChart({ data }: { data: AnalyzeResponse["charts"]["price"] }) {
  const [hovered, setHovered] = useState<{ x: number; y: number; point: CandlestickPoint } | null>(null);
  const chart = useMemo(() => buildCandlestickViewModel(data), [data]);

  if (chart.points.length === 0) {
    return (
      <div className="flex min-h-[360px] items-center justify-center rounded-2xl border border-amber-300/15 bg-amber-300/[.045] p-6 text-center text-sm leading-6 text-amber-100">
        K 線資料暫無。後端需提供 open、high、low、close 後才能顯示 K 線圖。
      </div>
    );
  }

  const stepWidth = (chart.width - chart.padding.left - chart.padding.right) / chart.points.length;
  const candleWidth = Math.max(3.2, Math.min(10.5, stepWidth * 0.78));
  const hitWidth = Math.max(candleWidth + 3, stepWidth);

  return (
    <div className="relative min-h-[360px] overflow-hidden rounded-2xl border border-white/[.06] bg-slate-950/25">
      <svg viewBox={`0 0 ${chart.width} ${chart.height}`} className="h-[380px] w-full" role="img" aria-label="K 線圖">
        <rect width={chart.width} height={chart.height} fill="transparent" />
        {chart.yTicks.map((tick) => (
          <g key={tick.value}>
            <line x1={chart.padding.left} x2={chart.width - chart.padding.right} y1={tick.y} y2={tick.y} stroke="rgba(148,163,184,.12)" />
            <text x={chart.padding.left - 10} y={tick.y + 4} textAnchor="end" className="fill-slate-500 text-[11px]">
              {formatAxisPrice(tick.value)}
            </text>
          </g>
        ))}
        {chart.xLabels.map((label) => (
          <text key={`${label.date}-${label.x}`} x={label.x} y={chart.height - 18} textAnchor="middle" className="fill-slate-500 text-[11px]">
            {label.date.slice(5)}
          </text>
        ))}
        {chart.points.map((point) => {
          const rising = point.close >= point.open;
          const isHovered = hovered?.point.date === point.date;
          const color = rising ? "#22c55e" : "#f43f5e";
          const wickColor = rising ? "rgba(34,197,94,.82)" : "rgba(244,63,94,.82)";
          const fillColor = rising ? "rgba(34,197,94,.34)" : "rgba(244,63,94,.34)";
          const bodyTop = Math.min(point.openY, point.closeY);
          const bodyHeight = Math.max(1.5, Math.abs(point.closeY - point.openY));
          return (
            <g
              key={point.date}
              onMouseEnter={(event) => setHovered({ x: event.clientX, y: event.clientY, point })}
              onMouseMove={(event: MouseEvent<SVGGElement>) => setHovered({ x: event.clientX, y: event.clientY, point })}
              onMouseLeave={() => setHovered(null)}
            >
              {isHovered ? (
                <rect
                  x={point.x - hitWidth / 2}
                  y={chart.padding.top}
                  width={hitWidth}
                  height={chart.height - chart.padding.top - chart.padding.bottom}
                  fill="rgba(148,163,184,.08)"
                />
              ) : null}
              <line x1={point.x} x2={point.x} y1={point.highY} y2={point.lowY} stroke={wickColor} strokeWidth={isHovered ? 1.9 : 1.45} />
              <rect
                x={point.x - candleWidth / 2}
                y={bodyTop}
                width={candleWidth}
                height={bodyHeight}
                rx={1}
                fill={isHovered ? color : fillColor}
                stroke={color}
                strokeWidth={isHovered ? 1.8 : 1.35}
              />
              <rect
                x={point.x - hitWidth / 2}
                y={chart.padding.top}
                width={hitWidth}
                height={chart.height - chart.padding.top - chart.padding.bottom}
                fill="transparent"
              />
            </g>
          );
        })}
      </svg>
      {hovered ? (
        <div
          className="pointer-events-none fixed z-50 rounded-2xl border border-white/[.1] bg-slate-950/95 px-4 py-3 text-xs leading-5 text-slate-200 shadow-2xl"
          style={{ left: Math.min(hovered.x + 14, window.innerWidth - 190), top: Math.max(hovered.y - 84, 12) }}
        >
          <p className="font-medium text-white">{hovered.point.date}</p>
          <p>開盤：{formatCompactPrice(hovered.point.open)}</p>
          <p>最高：{formatCompactPrice(hovered.point.high)}</p>
          <p>最低：{formatCompactPrice(hovered.point.low)}</p>
          <p>收盤：{formatCompactPrice(hovered.point.close)}</p>
        </div>
      ) : null}
    </div>
  );
}

type CandlestickPoint = {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  x: number;
  openY: number;
  highY: number;
  lowY: number;
  closeY: number;
};

function buildCandlestickViewModel(data: AnalyzeResponse["charts"]["price"]) {
  const width = 920;
  const height = 420;
  const padding = { top: 24, right: 18, bottom: 46, left: 58 };
  const raw = data
    .filter((point) => [point.open, point.high, point.low, point.close].every((value) => typeof value === "number" && Number.isFinite(value)))
    .map((point) => ({
      date: point.date,
      open: point.open as number,
      high: point.high as number,
      low: point.low as number,
      close: point.close as number,
    }));

  if (raw.length === 0) {
    return { width, height, padding, points: [], yTicks: [], xLabels: [] };
  }

  const minPrice = Math.min(...raw.map((point) => point.low));
  const maxPrice = Math.max(...raw.map((point) => point.high));
  const range = maxPrice - minPrice || Math.max(maxPrice, 1) * 0.05;
  const lower = minPrice - range * 0.06;
  const upper = maxPrice + range * 0.06;
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const yFor = (value: number) => padding.top + ((upper - value) / (upper - lower)) * plotHeight;
  const xFor = (index: number) => padding.left + (raw.length === 1 ? plotWidth / 2 : (index / (raw.length - 1)) * plotWidth);
  const points = raw.map((point, index) => ({
    ...point,
    x: xFor(index),
    openY: yFor(point.open),
    highY: yFor(point.high),
    lowY: yFor(point.low),
    closeY: yFor(point.close),
  }));
  const yTicks = buildPriceTicks(lower, upper).map((value) => ({ value, y: yFor(value) })).reverse();
  const labelStep = Math.max(1, Math.ceil(raw.length / 6));
  const xLabels = raw
    .map((point, index) => ({ date: point.date, x: xFor(index), index }))
    .filter((label) => label.index % labelStep === 0 || label.index === raw.length - 1);

  return { width, height, padding, points, yTicks, xLabels };
}

function buildTechnicalScenario(data: AnalyzeResponse): TechnicalScenario {
  const prices = getValidPricePoints(data.charts.price);
  const volumes = data.charts.volume.map((point) => point.volume).filter((value): value is number => typeof value === "number" && Number.isFinite(value));
  const latest = prices.at(-1);
  const previous = prices.at(-2);
  const metrics = data.metrics;
  const sourceText = data.sources.map((source) => `${source.name} ${source.message}`).join(" ");
  const usesFallback = /yfinance/i.test(sourceText);
  const usesOfficial = sourceText.includes("TWSE 官方日 K") || sourceText.includes("TPEx 官方日 K");
  const dataLimited = prices.length < 20 || latest === undefined || metrics.latestClose === null;

  if (dataLimited || latest === undefined) {
    return {
      direction: "中性整理",
      confidence: "低",
      confidenceNote: "OHLC 或均線資料不足，推演以風險控管與區間觀察為主。",
      dataLimited: true,
      reasons: [
        "資料不足，僅能提供保守情境推演。",
        usesFallback ? "目前價格資料來自 yfinance fallback，推演信心已保守下修。" : "目前未取得足夠日 K 序列驗證短線結構。",
        "若後續日 K 與均線資料補齊，應重新檢查 MA20、MA60 與近 20 日報酬。",
      ],
      cards: buildScenarioCards("中性整理", metrics, "資料暫無", "資料暫無", false),
    };
  }

  const latestClose = metrics.latestClose ?? latest.close;
  const latestVolume = volumes.at(-1) ?? null;
  const averageVolume = average(volumes.slice(-20));
  const recentWindow = prices.slice(-10);
  const previousWindow = prices.slice(-20, -10);
  const recentHigh = Math.max(...recentWindow.map((point) => point.high));
  const recentLow = Math.min(...recentWindow.map((point) => point.low));
  const previousHigh = previousWindow.length > 0 ? Math.max(...previousWindow.map((point) => point.high)) : null;
  const previousLow = previousWindow.length > 0 ? Math.min(...previousWindow.map((point) => point.low)) : null;
  const lowRising = previousLow !== null && recentLow > previousLow;
  const highFalling = previousHigh !== null && recentHigh < previousHigh;
  const rangePosition = recentHigh !== recentLow ? (latestClose - recentLow) / (recentHigh - recentLow) : 0.5;
  const closeNearHigh = rangePosition >= 0.7;
  const downOnVolume = latestVolume !== null && averageVolume !== null && latestVolume > averageVolume * 1.2 && previous !== undefined && latest.close < previous.close;

  let bullishScore = 0;
  let weakScore = 0;
  const reasons: string[] = [];

  if (metrics.ma20 !== null && latestClose >= metrics.ma20) {
    bullishScore += 2;
    reasons.push(`最新收盤 ${formatCompactPrice(latestClose)} 高於 MA20 ${formatCompactPrice(metrics.ma20)}，短線結構偏正向。`);
  } else if (metrics.ma20 !== null) {
    weakScore += 2;
    reasons.push(`最新收盤 ${formatCompactPrice(latestClose)} 低於 MA20 ${formatCompactPrice(metrics.ma20)}，短線壓力仍需觀察。`);
  }

  if (metrics.ma20 !== null && metrics.ma60 !== null && metrics.ma20 >= metrics.ma60) {
    bullishScore += 2;
    reasons.push(`MA20 高於 MA60，中期趨勢仍有支撐。`);
  } else if (metrics.ma20 !== null && metrics.ma60 !== null) {
    weakScore += 1;
    reasons.push(`MA20 低於 MA60，均線排列尚未轉強。`);
  }

  if (metrics.ma60 !== null && latestClose < metrics.ma60) {
    weakScore += 2;
    reasons.push(`最新收盤低於 MA60 ${formatCompactPrice(metrics.ma60)}，風險權重提高。`);
  } else if (metrics.ma60 !== null) {
    bullishScore += 1;
  }

  if (metrics.return20d !== null && metrics.return20d > 3) {
    bullishScore += 1;
    reasons.push(`近 20 日報酬 ${formatSignedPercent(metrics.return20d)}，動能偏正向但仍需留意追價風險。`);
  } else if (metrics.return20d !== null && metrics.return20d < 0) {
    weakScore += 2;
    reasons.push(`近 20 日報酬 ${formatSignedPercent(metrics.return20d)}，短線動能偏弱。`);
  }

  if (lowRising && closeNearHigh) {
    bullishScore += 2;
    reasons.push(`近 10 根日 K 低點墊高，且收盤靠近區間高位，偏多情境權重提高。`);
  } else if (highFalling) {
    weakScore += 1;
    reasons.push(`近 10 根日 K 高點未能延伸，若低點同步轉弱，整理風險提高。`);
  }

  if (downOnVolume) {
    weakScore += 2;
    reasons.push(`成交量高於近 20 日均量且價格下跌，需觀察賣壓是否延續。`);
  } else if (latestVolume !== null && averageVolume !== null) {
    reasons.push(`成交量與近 20 日均量相較未出現明顯失衡，量價訊號仍需搭配後續 K 線確認。`);
  }

  if (usesOfficial) {
    reasons.push(`資料來源為官方日 K，資料品質對本次推演較有支撐。`);
  } else if (usesFallback) {
    reasons.push(`價格資料使用 yfinance fallback，推演信心已保守下修。`);
  }

  let direction: ScenarioDirection = bullishScore - weakScore >= 2 ? "偏多" : weakScore - bullishScore >= 2 ? "偏弱" : "中性整理";
  if (metrics.ma20 !== null && metrics.ma60 !== null && latestClose < metrics.ma20 && latestClose >= metrics.ma60 && direction === "偏多") {
    direction = "中性整理";
  }
  const baseConfidence = dataLimited ? 1 : Math.min(3, Math.max(1, Math.round((Math.abs(bullishScore - weakScore) + (usesOfficial ? 3 : 1)) / 2)));
  const adjustedConfidence = usesFallback ? Math.max(1, baseConfidence - 1) : baseConfidence;
  const confidence = confidenceLabel(adjustedConfidence);
  const trendSummary = `近 10 根日 K 區間：高 ${formatCompactPrice(recentHigh)}、低 ${formatCompactPrice(recentLow)}`;

  return {
    direction,
    confidence,
    confidenceNote: usesFallback ? "因價格來源為 yfinance fallback，推演信心下修一級。" : "推演信心依資料完整度、官方日 K 狀態與技術訊號一致性評估。",
    dataLimited: false,
    reasons: reasons.slice(0, 5),
    cards: buildScenarioCards(direction, metrics, trendSummary, downOnVolume ? "量增下跌" : "量價待確認", usesFallback),
  };
}

function getValidPricePoints(data: AnalyzeResponse["charts"]["price"]) {
  return data
    .filter((point) => [point.open, point.high, point.low, point.close].every((value) => typeof value === "number" && Number.isFinite(value)))
    .map((point) => ({
      date: point.date,
      open: point.open as number,
      high: point.high as number,
      low: point.low as number,
      close: point.close as number,
    }));
}

function buildScenarioCards(
  direction: ScenarioDirection,
  metrics: AnalyzeResponse["metrics"],
  trendSummary: string,
  volumeSummary: string,
  usesFallback: boolean,
): ScenarioCard[] {
  const ma20 = metrics.ma20 === null ? "MA20" : `MA20 ${formatCompactPrice(metrics.ma20)}`;
  const ma60 = metrics.ma60 === null ? "MA60" : `MA60 ${formatCompactPrice(metrics.ma60)}`;
  const returnText = metrics.return20d === null ? "20 日報酬" : `20 日報酬 ${formatSignedPercent(metrics.return20d)}`;
  const sourceCaution = usesFallback ? "；因資料來源為 fallback，需保守解讀" : "";

  return [
    {
      title: "偏多路徑",
      tone: "bullish",
      trigger: `若收盤持續站上 ${ma20}，且 ${ma20} 維持高於 ${ma60}。`,
      path: direction === "偏多" ? "可能維持偏多震盪，並以區間高位是否延續作為主要觀察。" : "可能先由整理轉為偏多，但需等待均線與 K 線結構同步確認。",
      watch: `${trendSummary}；觀察 ${returnText} 與成交量是否溫和配合${sourceCaution}。`,
    },
    {
      title: "中性整理",
      tone: "neutral",
      trigger: `若收盤在 ${ma20} 附近反覆，且未明確跌破 ${ma60}。`,
      path: "可能維持區間整理，盤勢重點在支撐是否守住與反彈是否帶量。",
      watch: `${trendSummary}；觀察日 K 是否出現低點墊高或高點受壓。`,
    },
    {
      title: "偏弱延續",
      tone: "weak",
      trigger: `若收盤跌回 ${ma20} 下方，或進一步低於 ${ma60}。`,
      path: "可能延續偏弱整理，需降低對短線反彈的解讀權重。",
      watch: `${volumeSummary}；觀察是否出現量增下跌、低點下移或 20 日報酬轉弱。`,
    },
  ];
}

function average(values: number[]) {
  if (values.length === 0) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function confidenceLabel(score: number): ScenarioConfidence {
  if (score >= 3) return "高";
  if (score === 2) return "中";
  return "低";
}

function formatSignedPercent(value: number) {
  return `${value > 0 ? "+" : ""}${value.toLocaleString("zh-TW", { maximumFractionDigits: 2 })}%`;
}

function buildPriceTicks(lower: number, upper: number) {
  const targetTicks = 5;
  const rawStep = Math.max((upper - lower) / (targetTicks - 1), 1);
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const normalized = rawStep / magnitude;
  const niceNormalized = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
  const step = Math.max(1, niceNormalized * magnitude);
  const first = Math.floor(lower / step) * step;
  const ticks: number[] = [];

  for (let value = first; value <= upper + step * 0.5 && ticks.length < 7; value += step) {
    if (value >= lower - step * 0.5) {
      ticks.push(Math.round(value));
    }
  }

  return ticks.length >= 2 ? ticks : [Math.floor(lower), Math.ceil(upper)];
}

function formatAxisPrice(value: number) {
  return value.toLocaleString("zh-TW", { maximumFractionDigits: 0 });
}

function formatCompactPrice(value: number) {
  return value.toLocaleString("zh-TW", { maximumFractionDigits: 2 });
}

function formatVolumeAxis(value: number | string) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "資料暫無";
  const absolute = Math.abs(numeric);

  if (absolute >= 1_000_000) {
    return `${(numeric / 1_000_000).toLocaleString("zh-TW", { maximumFractionDigits: 1 })}M`;
  }

  if (absolute >= 1_000) {
    return `${(numeric / 1_000).toLocaleString("zh-TW", { maximumFractionDigits: 0 })}K`;
  }

  return numeric.toLocaleString("zh-TW", { maximumFractionDigits: 0 });
}

const tooltipStyle = {
  background: "rgba(15,23,42,.94)",
  border: "1px solid rgba(148,163,184,.22)",
  borderRadius: "14px",
  color: "#e2e8f0",
};
