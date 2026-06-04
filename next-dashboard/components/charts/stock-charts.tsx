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
    <div className="grid gap-5 xl:grid-cols-3">
      <ChartPanel title="股價走勢">
        <ResponsiveContainer width="100%" height={260}>
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
      <ChartPanel title="成交量">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data.charts.volume}>
            <CartesianGrid stroke="rgba(148,163,184,.12)" vertical={false} />
            <XAxis dataKey="date" tick={axisStyle} tickLine={false} axisLine={false} minTickGap={28} />
            <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={48} />
            <Tooltip contentStyle={tooltipStyle} />
            <Bar dataKey="volume" fill="#34d399" opacity={0.62} radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartPanel>
      <ChartPanel title="均線分析">
        <ResponsiveContainer width="100%" height={260}>
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
  );
}

function ChartPanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-3xl border border-white/[.08] bg-white/[.045] p-5 shadow-glass">
      <h2 className="mb-5 text-base font-semibold text-white">{title}</h2>
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
