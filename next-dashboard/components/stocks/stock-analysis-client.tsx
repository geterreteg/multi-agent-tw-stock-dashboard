"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Database, Download, GaugeCircle, Loader2, MessageSquareText, ShieldCheck } from "lucide-react";

import { KpiCard } from "@/components/analysis/kpi-card";
import { StockCharts } from "@/components/charts/stock-charts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { analyzeStock } from "@/lib/api";
import type { AnalyzeResponse } from "@/lib/types";

export function StockAnalysisClient({ symbol }: { symbol: string }) {
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let ignore = false;

    async function loadAnalysis() {
      setIsLoading(true);
      setError(null);
      try {
        const result = await analyzeStock(symbol);
        if (!ignore) setData(result);
      } catch (loadError) {
        if (!ignore) {
          setData(null);
          setError(loadError instanceof Error ? loadError.message : "系統發生未知錯誤。");
        }
      } finally {
        if (!ignore) setIsLoading(false);
      }
    }

    loadAnalysis();
    return () => {
      ignore = true;
    };
  }, [symbol]);

  if (isLoading) {
    return (
      <div className="rounded-3xl border border-cyan-300/20 bg-cyan-300/10 p-8 text-cyan-50">
        <Loader2 className="mb-4 h-8 w-8 animate-spin" />
        <h1 className="text-2xl font-semibold">正在取得股票分析資料</h1>
        <p className="mt-3 text-sm leading-7 text-cyan-100/80">系統正在呼叫 FastAPI，若資料來源較慢會自動逾時並顯示提示。</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-3xl border border-amber-300/20 bg-amber-300/10 p-8 text-amber-50">
        <AlertTriangle className="mb-4 h-8 w-8" />
        <h1 className="text-2xl font-semibold">暫時無法取得分析資料</h1>
        <p className="mt-3 text-sm leading-7 text-amber-100/80">{error}</p>
      </div>
    );
  }

  const finalScore = typeof data.decision?.finalScore === "number" ? data.decision.finalScore : null;
  const scoreBreakdown = data.decision?.scoreBreakdown ?? {};
  const recommendationPreview = previewText(data.decision?.recommendationText);
  const sourceIssues = (data.sources ?? []).filter(isSourceDegraded);
  const hasDegradedAgent = data.agents.some((agent) => agent.degraded);
  const dataQualityLabel = sourceIssues.length === 0 && !hasDegradedAgent ? "資料來源正常" : "部分資料降級";
  const dataQualityTone = sourceIssues.length === 0 && !hasDegradedAgent ? "ok" : "degraded";

  return (
    <div className="space-y-8">
      <section className="overflow-hidden rounded-[2rem] border border-cyan-300/15 bg-slate-950/65 shadow-glass">
        <div className="grid gap-0 lg:grid-cols-[1.2fr_.8fr]">
          <div className="border-b border-white/[.08] p-6 lg:border-b-0 lg:border-r">
            <div className="flex flex-wrap items-center gap-3">
              <Badge className={stanceBadgeClass(data.rating)}>{data.rating}</Badge>
              <span className="text-sm text-slate-400">最終評分：{formatScore(finalScore)}</span>
              <span className="text-sm text-slate-500">最後更新：{data.lastUpdated}</span>
            </div>
            <p className="mt-4 max-w-4xl text-base leading-8 text-slate-200">{recommendationPreview}</p>
          </div>
          <div className="grid grid-cols-2 gap-px bg-white/[.08]">
            <SummaryMetric label="研究標的" value={`${data.symbol} ${data.name}`} />
            <SummaryMetric label="資料品質" value={dataQualityLabel} tone={dataQualityTone} />
          </div>
        </div>
      </section>

      <DataQualitySummary sources={data.sources ?? []} hasDegradedAgent={hasDegradedAgent} />

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

      <ScoreBreakdown scoreBreakdown={scoreBreakdown} finalScore={finalScore} />

      <StockCharts data={data} />

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white">Agent 分析</h2>
          <span className="text-sm text-slate-500">規則式多 Agent 協作</span>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          {data.agents.map((agent) => (
            <Card key={agent.name}>
              <CardHeader>
                <div className="flex items-start justify-between gap-3">
                  <CardTitle>{agent.name}</CardTitle>
                  <div className="flex flex-wrap justify-end gap-2">
                    {agent.degraded ? <Badge className="border-amber-300/20 bg-amber-300/10 text-amber-100">資料降級</Badge> : null}
                    <Badge className={stanceBadgeClass(agent.stance)}>{agent.stance}</Badge>
                  </div>
                </div>
                <p className="text-sm text-slate-400">{agent.role}</p>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-7 text-slate-300">{agent.summary}</p>
                <p className="mt-4 rounded-2xl border border-white/[.06] bg-white/[.03] p-4 text-sm leading-7 text-slate-300">
                  {agent.narrative}
                </p>
                <div className="mt-5 flex items-center gap-3">
                  <div className="h-2 flex-1 rounded-full bg-white/[.07]">
                    <div className="h-full rounded-full bg-cyan-300/75" style={{ width: `${agent.confidence * 100}%` }} />
                  </div>
                  <span className="text-sm font-semibold text-cyan-100">{Math.round(agent.confidence * 100)}%</span>
                </div>
                <div className="mt-5">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">使用數據</p>
                  <ul className="mt-3 grid gap-2 text-sm text-slate-400 sm:grid-cols-2">
                    {agent.evidence.map((item) => (
                      <li key={item} className="rounded-xl border border-white/[.06] bg-white/[.025] px-3 py-2">
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
                <ul className="mt-5 space-y-2 text-sm text-slate-400">
                  {agent.reasons.map((reason) => (
                    <li key={reason}>- {reason}</li>
                  ))}
                </ul>
                {agent.risks.length > 0 ? (
                  <div className="mt-5 rounded-2xl border border-amber-300/10 bg-amber-300/[.04] p-3 text-sm leading-7 text-amber-100/80">
                    {agent.risks.slice(0, 2).map((risk) => (
                      <p key={risk}>風險：{risk}</p>
                    ))}
                  </div>
                ) : null}
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="rounded-3xl border border-white/[.08] bg-white/[.035] p-6">
        <div className="mb-5 flex items-center gap-2 text-white">
          <MessageSquareText className="h-5 w-5 text-cyan-200" />
          <h2 className="text-xl font-semibold">Agent 辯論室</h2>
        </div>
        <div className="space-y-3">
          {data.debate.map((item) => (
            <div key={`${item.speaker}-${item.message}`} className={debateBubbleClass(item.tone)}>
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-semibold text-white">{item.speaker}</span>
                <Badge className={stanceBadgeClass(item.stance)}>{item.stance}</Badge>
              </div>
              <p className="mt-2 text-sm leading-7 text-slate-300">{item.message}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <DecisionColumn title="支持理由" items={data.decision.supportReasons} />
        <DecisionColumn title="主要風險" items={data.decision.risks} tone="risk" />
        <DecisionColumn title="觀察重點" items={data.decision.watchPoints} />
      </section>

      <section className="rounded-3xl border border-cyan-300/10 bg-cyan-300/[.045] p-6">
        <h2 className="text-lg font-semibold text-white">總結觀察建議</h2>
        <p className="mt-3 text-sm leading-7 text-slate-300">{data.decision.recommendationText}</p>
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

function stanceBadgeClass(stance: string) {
  if (stance === "偏多") return "border-emerald-300/20 bg-emerald-300/10 text-emerald-100";
  if (stance === "偏空") return "border-amber-300/20 bg-amber-300/10 text-amber-100";
  return "border-cyan-300/20 bg-cyan-300/10 text-cyan-100";
}

function debateBubbleClass(tone: string) {
  const base = "rounded-2xl border p-4";
  if (tone === "support") return `${base} border-emerald-300/10 bg-emerald-300/[.04]`;
  if (tone === "risk") return `${base} border-amber-300/10 bg-amber-300/[.04]`;
  if (tone === "summary") return `${base} border-cyan-300/15 bg-cyan-300/[.06]`;
  return `${base} border-white/[.06] bg-white/[.035]`;
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

function SummaryMetric({ label, value, tone = "default" }: { label: string; value: string; tone?: "default" | "ok" | "degraded" }) {
  const toneClass = tone === "ok" ? "text-emerald-100" : tone === "degraded" ? "text-amber-100" : "text-white";

  return (
    <div className="bg-white/[.035] p-5">
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className={`mt-2 text-lg font-semibold ${toneClass}`}>{value}</p>
    </div>
  );
}

function DataQualitySummary({
  sources,
  hasDegradedAgent,
}: {
  sources: AnalyzeResponse["sources"];
  hasDegradedAgent: boolean;
}) {
  const degradedSources = sources.filter(isSourceDegraded);
  const isHealthy = degradedSources.length === 0 && !hasDegradedAgent;

  return (
    <section
      className={`rounded-3xl border p-5 ${
        isHealthy ? "border-emerald-300/15 bg-emerald-300/[.045]" : "border-amber-300/15 bg-amber-300/[.045]"
      }`}
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start gap-3">
          <div className={`rounded-2xl p-2 ${isHealthy ? "bg-emerald-300/10 text-emerald-100" : "bg-amber-300/10 text-amber-100"}`}>
            {isHealthy ? <CheckCircle2 className="h-5 w-5" /> : <AlertTriangle className="h-5 w-5" />}
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">{isHealthy ? "資料來源正常" : "資料來源部分降級"}</h2>
            <p className="mt-1 text-sm leading-6 text-slate-400">
              {isHealthy
                ? "yfinance 與 FinMind 資料已進入分析流程。"
                : "部分資料來源可能缺漏或延遲，系統已保留可用資料並降低相關 Agent 信心。"}
            </p>
          </div>
        </div>
        <div className="grid gap-2 sm:grid-cols-2 lg:min-w-[420px]">
          {sources.length > 0 ? (
            sources.map((source) => (
              <div key={`${source.name}-${source.status}`} className="rounded-2xl border border-white/[.07] bg-slate-950/35 px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="flex items-center gap-2 text-sm font-medium text-white">
                    <Database className="h-4 w-4 text-cyan-200" />
                    {source.name}
                  </span>
                  <Badge className={isSourceDegraded(source) ? "border-amber-300/20 bg-amber-300/10 text-amber-100" : "border-emerald-300/20 bg-emerald-300/10 text-emerald-100"}>
                    {source.status}
                  </Badge>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-500">{source.message}</p>
              </div>
            ))
          ) : (
            <div className="rounded-2xl border border-white/[.07] bg-slate-950/35 px-4 py-3 text-sm text-slate-400">
              資料來源狀態暫無回傳，請以 Agent 降級提示輔助判讀。
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function ScoreBreakdown({ scoreBreakdown, finalScore }: { scoreBreakdown: Record<string, number>; finalScore: number | null }) {
  const items = [
    { label: "技術面", rawKey: "technical", weightedKey: "technicalWeighted", weight: "40%" },
    { label: "基本面", rawKey: "fundamental", weightedKey: "fundamentalWeighted", weight: "30%" },
    { label: "籌碼面", rawKey: "chip", weightedKey: "chipWeighted", weight: "20%" },
    { label: "風險面", rawKey: "risk", weightedKey: "riskWeighted", weight: "10%" },
  ].map((item) => ({
    ...item,
    rawScore: safeNumber(scoreBreakdown[item.rawKey]),
    weightedScore: safeNumber(scoreBreakdown[item.weightedKey]),
  }));

  return (
    <section className="rounded-3xl border border-white/[.08] bg-white/[.04] p-6 shadow-glass">
      <div className="mb-5 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <div className="flex items-center gap-2 text-cyan-100">
            <GaugeCircle className="h-5 w-5" />
            <h2 className="text-lg font-semibold text-white">多 Agent 加權分數</h2>
          </div>
          <p className="mt-2 text-sm text-slate-400">分數區間為 -2 到 +2，最終分數由技術、基本面、籌碼與風險權重整合。</p>
        </div>
        <div className="rounded-2xl border border-cyan-300/15 bg-cyan-300/[.06] px-4 py-3 text-right">
          <p className="text-xs text-cyan-100/70">finalScore</p>
          <p className="text-2xl font-semibold text-white">{formatScore(finalScore)}</p>
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {items.map((item) => (
          <div key={item.label} className="rounded-2xl border border-white/[.07] bg-slate-950/35 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-medium text-white">{item.label}</p>
                <p className="mt-1 text-xs text-slate-500">權重 {item.weight}</p>
              </div>
              <span className={scoreTextClass(item.rawScore)}>{formatScore(item.rawScore)}</span>
            </div>
            <ScoreBar score={item.rawScore} />
            <p className="mt-3 text-xs text-slate-500">加權貢獻：{formatScore(item.weightedScore)}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function ScoreBar({ score }: { score: number | null }) {
  const width = score === null ? 0 : (Math.min(Math.abs(score), 2) / 2) * 50;
  const isNegative = score !== null && score < 0;
  const color = score === null ? "bg-slate-500/50" : isNegative ? "bg-amber-300/75" : "bg-emerald-300/75";

  return (
    <div className="relative mt-4 h-2 rounded-full bg-white/[.08]">
      <div className="absolute left-1/2 top-[-3px] h-4 w-px bg-white/20" />
      <div
        className={`absolute top-0 h-full rounded-full ${color}`}
        style={{
          width: `${width}%`,
          left: isNegative ? `${50 - width}%` : "50%",
        }}
      />
    </div>
  );
}

function isSourceDegraded(source: AnalyzeResponse["sources"][number]) {
  const status = String(source.status ?? "").toLowerCase();
  return !(status === "ok" || status === "success" || status === "正常");
}

function previewText(text: string | undefined) {
  if (!text) return "系統已完成多 Agent 分析，請參考下方技術面、基本面、籌碼面與風險控管結果。";
  return text.length > 96 ? `${text.slice(0, 96)}...` : text;
}

function safeNumber(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function formatScore(value: number | null) {
  if (value === null) return "資料暫無";
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}`;
}

function scoreTextClass(score: number | null) {
  if (score === null) return "text-sm font-semibold text-slate-500";
  if (score > 0) return "text-sm font-semibold text-emerald-100";
  if (score < 0) return "text-sm font-semibold text-amber-100";
  return "text-sm font-semibold text-cyan-100";
}
