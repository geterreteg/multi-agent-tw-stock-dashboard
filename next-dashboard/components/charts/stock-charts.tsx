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

export function StockCharts({ data }: { data: AnalyzeResponse }) {
  const [chartMode, setChartMode] = useState<ChartMode>("close");

  return (
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
            <BarChart data={data.charts.volume}>
              <CartesianGrid stroke="rgba(148,163,184,.12)" vertical={false} />
              <XAxis dataKey="date" tick={axisStyle} tickLine={false} axisLine={false} minTickGap={28} />
              <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={48} />
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
    <div className="flex w-fit rounded-full border border-white/[.08] bg-black/20 p-1">
      {options.map((option) => {
        const isActive = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={`rounded-full px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-200/70 ${
              isActive ? "bg-cyan-100 text-slate-950 shadow-[0_10px_28px_rgba(0,0,0,.22)]" : "text-slate-400 hover:bg-white/[.07] hover:text-slate-100"
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

  const candleWidth = Math.max(2.4, Math.min(9, (chart.width - chart.padding.left - chart.padding.right) / chart.points.length * 0.58));

  return (
    <div className="relative min-h-[360px] overflow-hidden rounded-2xl border border-white/[.06] bg-slate-950/25">
      <svg viewBox={`0 0 ${chart.width} ${chart.height}`} className="h-[380px] w-full" role="img" aria-label="K 線圖">
        <rect width={chart.width} height={chart.height} fill="transparent" />
        {chart.yTicks.map((tick) => (
          <g key={tick.value}>
            <line x1={chart.padding.left} x2={chart.width - chart.padding.right} y1={tick.y} y2={tick.y} stroke="rgba(148,163,184,.12)" />
            <text x={chart.padding.left - 10} y={tick.y + 4} textAnchor="end" className="fill-slate-500 text-[11px]">
              {formatCompactPrice(tick.value)}
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
          const color = rising ? "#34d399" : "#fb7185";
          const bodyTop = Math.min(point.openY, point.closeY);
          const bodyHeight = Math.max(1.5, Math.abs(point.closeY - point.openY));
          return (
            <g
              key={point.date}
              onMouseEnter={(event) => setHovered({ x: event.clientX, y: event.clientY, point })}
              onMouseMove={(event: MouseEvent<SVGGElement>) => setHovered({ x: event.clientX, y: event.clientY, point })}
              onMouseLeave={() => setHovered(null)}
            >
              <line x1={point.x} x2={point.x} y1={point.highY} y2={point.lowY} stroke={color} strokeWidth={1.4} />
              <rect
                x={point.x - candleWidth / 2}
                y={bodyTop}
                width={candleWidth}
                height={bodyHeight}
                rx={1}
                fill={rising ? "rgba(52,211,153,.22)" : "rgba(251,113,133,.22)"}
                stroke={color}
                strokeWidth={1.3}
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
          <p>開：{formatCompactPrice(hovered.point.open)}</p>
          <p>高：{formatCompactPrice(hovered.point.high)}</p>
          <p>低：{formatCompactPrice(hovered.point.low)}</p>
          <p>收：{formatCompactPrice(hovered.point.close)}</p>
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
  const yTicks = Array.from({ length: 5 }, (_, index) => {
    const value = lower + ((upper - lower) / 4) * index;
    return { value, y: yFor(value) };
  }).reverse();
  const labelStep = Math.max(1, Math.ceil(raw.length / 6));
  const xLabels = raw
    .map((point, index) => ({ date: point.date, x: xFor(index), index }))
    .filter((label) => label.index % labelStep === 0 || label.index === raw.length - 1);

  return { width, height, padding, points, yTicks, xLabels };
}

function formatCompactPrice(value: number) {
  return value.toLocaleString("zh-TW", { maximumFractionDigits: 2 });
}

const tooltipStyle = {
  background: "rgba(15,23,42,.94)",
  border: "1px solid rgba(148,163,184,.22)",
  borderRadius: "14px",
  color: "#e2e8f0",
};
