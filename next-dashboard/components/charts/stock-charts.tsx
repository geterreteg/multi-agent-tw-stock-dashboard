"use client";

import type { ReactNode } from "react";
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

export function StockCharts({ data }: { data: AnalyzeResponse }) {
  return (
    <section className="grid gap-5 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
      <ChartPanel title="股價走勢" description="觀察收盤價趨勢與近期波動，是本頁主要市場價格視圖。" featured>
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
  featured = false,
  muted = false,
}: {
  title: string;
  description: string;
  children: ReactNode;
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
      <div className="mb-5">
        <h2 className={featured ? "text-lg font-semibold text-white" : "text-base font-semibold text-white"}>{title}</h2>
        <p className="mt-2 text-xs leading-5 text-slate-500">{description}</p>
      </div>
      {children}
    </section>
  );
}

const tooltipStyle = {
  background: "rgba(15,23,42,.94)",
  border: "1px solid rgba(148,163,184,.22)",
  borderRadius: "14px",
  color: "#e2e8f0",
};
