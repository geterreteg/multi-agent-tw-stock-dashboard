import { AlertTriangle, Download, ShieldCheck } from "lucide-react";

import { KpiCard } from "@/components/analysis/kpi-card";
import { StockCharts } from "@/components/charts/stock-charts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { analyzeStock } from "@/lib/api";

type PageProps = {
  params: Promise<{ symbol: string }>;
};

export default async function StockAnalysisPage({ params }: PageProps) {
  const { symbol } = await params;
  const result = await loadAnalysis(symbol);

  if (!result.data) {
    return (
      <div className="rounded-3xl border border-amber-300/20 bg-amber-300/10 p-8 text-amber-50">
        <AlertTriangle className="mb-4 h-8 w-8" />
        <h1 className="text-2xl font-semibold">暫時無法取得分析資料</h1>
        <p className="mt-3 text-sm leading-7 text-amber-100/80">{result.error}</p>
      </div>
    );
  }

  const data = result.data;

  return (
    <div className="space-y-8">
      <section className="rounded-[2rem] border border-white/[.09] bg-white/[.045] p-7 shadow-glass">
        <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <Badge>{data.period}</Badge>
              <span className="text-sm text-slate-500">最後更新：{data.lastUpdated}</span>
            </div>
            <h1 className="mt-5 text-4xl font-semibold tracking-tight text-white">
              {data.symbol} {data.name}
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-400">
              以多 Agent 觀點彙整價格、基本面、籌碼與風險，輸出可解釋的研究摘要。
            </p>
          </div>
          <div className="rounded-2xl border border-cyan-300/20 bg-cyan-300/10 px-6 py-4">
            <p className="text-sm text-cyan-100/75">目前評級</p>
            <p className="mt-1 text-3xl font-semibold text-white">{data.rating}</p>
          </div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="最新收盤價" value={data.metrics.latestClose} />
        <KpiCard label="20 日報酬" value={data.metrics.return20d} suffix="%" signed />
        <KpiCard label="MA20" value={data.metrics.ma20} />
        <KpiCard label="MA60" value={data.metrics.ma60} />
        <KpiCard label="本益比" value={data.metrics.peRatio} />
        <KpiCard label="EPS" value={data.metrics.eps} />
        <KpiCard label="營收成長" value={data.metrics.revenueGrowth} suffix="%" signed />
        <KpiCard label="外資買賣超" value={data.metrics.foreignBuy} signed />
      </section>

      <StockCharts data={data} />

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white">Agent 分析</h2>
          <span className="text-sm text-slate-500">示範資料預覽</span>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          {data.agents.map((agent) => (
            <Card key={agent.name}>
              <CardHeader>
                <CardTitle>{agent.name}</CardTitle>
                <p className="text-sm text-slate-400">{agent.role}</p>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-7 text-slate-300">{agent.view}</p>
                <div className="mt-5 flex items-center gap-3">
                  <div className="h-2 flex-1 rounded-full bg-white/[.07]">
                    <div className="h-full rounded-full bg-cyan-300/75" style={{ width: `${agent.confidence}%` }} />
                  </div>
                  <span className="text-sm font-semibold text-cyan-100">{agent.confidence}%</span>
                </div>
                <ul className="mt-5 space-y-2 text-sm text-slate-400">
                  {agent.reasons.map((reason) => (
                    <li key={reason}>- {reason}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <DecisionColumn title="支持理由" items={data.decision.supportReasons} />
        <DecisionColumn title="主要風險" items={data.decision.risks} tone="risk" />
        <DecisionColumn title="觀察重點" items={data.decision.watchPoints} />
      </section>

      <section className="rounded-3xl border border-white/[.08] bg-white/[.04] p-6">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <div className="flex items-center gap-2 text-cyan-100">
              <ShieldCheck className="h-5 w-5" />
              <h2 className="text-lg font-semibold">免責聲明</h2>
            </div>
            <p className="mt-3 text-sm leading-7 text-slate-400">{data.disclaimer}</p>
          </div>
          <Button variant="secondary">
            <Download className="h-4 w-4" />
            報告下載規劃中
          </Button>
        </div>
      </section>
    </div>
  );
}

async function loadAnalysis(symbol: string) {
  try {
    return { data: await analyzeStock(symbol), error: null };
  } catch (error) {
    return {
      data: null,
      error: error instanceof Error ? error.message : "系統發生未知錯誤。",
    };
  }
}

function DecisionColumn({ title, items, tone = "default" }: { title: string; items: string[]; tone?: "default" | "risk" }) {
  return (
    <Card className={tone === "risk" ? "border-amber-300/15" : undefined}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-3 text-sm leading-7 text-slate-300">
          {items.map((item) => (
            <li key={item} className="rounded-2xl border border-white/[.06] bg-white/[.035] p-3">
              {item}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
