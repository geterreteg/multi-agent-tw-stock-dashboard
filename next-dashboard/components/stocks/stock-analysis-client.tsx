"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Database, Download, FileText, GaugeCircle, Lightbulb, Loader2, MessageSquareText, Scale, ShieldCheck } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { KpiCard } from "@/components/analysis/kpi-card";
import { StockCharts } from "@/components/charts/stock-charts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { analyzeStock } from "@/lib/api";
import type { AnalyzeResponse } from "@/lib/types";

const COURSE_RESEARCH_DISCLAIMER =
  "本系統僅供課程研究與資料分析展示，所有評級與建議皆為規則式模型輸出，不構成正式投資建議或獲利保證。";

type ResearchReportView = {
  investmentThesis: string[];
  keyMetrics: string[];
  businessQuality: string[];
  financialAnalysis: string[];
  valuation: string[];
  catalysts: string[];
  risks: string[];
  variantView: string[];
  recommendation: string;
  confidenceScore: number | null;
  dataGaps: string[];
  scoreBreakdown: Record<string, number>;
};

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
  const researchReport = normalizeResearchReport(data);
  const scoreBreakdown = researchReport.scoreBreakdown;
  const displayedRating = data.decision?.rating ?? researchReport.recommendation ?? data.rating;
  const recommendationPreview = previewText(data.decision?.recommendationText);
  const sourceIssues = (data.sources ?? []).filter(isSourceDegraded);
  const hasDegradedAgent = data.agents.some((agent) => agent.degraded);
  const dataQualityLabel = sourceIssues.length === 0 && !hasDegradedAgent ? "資料來源正常" : "部分資料降級";
  const dataQualityTone = sourceIssues.length === 0 && !hasDegradedAgent ? "ok" : "degraded";

  return (
    <div className="space-y-8">
      <ResearchHeader
        data={data}
        dataQualityLabel={dataQualityLabel}
        dataQualityTone={dataQualityTone}
        displayedRating={displayedRating}
        finalScore={finalScore}
        report={researchReport}
        recommendationPreview={recommendationPreview}
        sources={data.sources ?? []}
      />

      <DataQualitySummary sources={data.sources ?? []} hasDegradedAgent={hasDegradedAgent} />

      <StructuredResearchReport data={data} report={researchReport} />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="最新收盤價" value={data.metrics.latestClose} />
        <KpiCard label="20 日報酬" value={data.metrics.return20d} suffix="%" signed />
        <KpiCard label="MA20" value={data.metrics.ma20} />
        <KpiCard label="MA60" value={data.metrics.ma60} />
        <KpiCard label="本益比" value={displayPeRatio(data.metrics)} />
        <KpiCard label="EPS" value={data.metrics.eps} />
        <KpiCard label="營收成長" value={data.metrics.revenueGrowth} suffix="%" signed />
        <KpiCard label="外資買賣超" value={data.metrics.foreignBuy} signed />
      </section>

      <ScoreBreakdown scoreBreakdown={scoreBreakdown} finalScore={finalScore} confidenceScore={researchReport.confidenceScore} />

      <StockCharts data={data} />

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white">Agent 分析明細</h2>
          <span className="text-sm text-slate-500">保留各 Agent 的數據、理由與風險</span>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          {data.agents.map((agent) => (
            <AgentInsightCard key={agent.name} agent={agent} />
          ))}
        </div>
      </section>

      <section className="rounded-3xl border border-white/[.08] bg-white/[.035] p-6 shadow-glass">
        <div className="mb-5 flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
          <div className="flex items-center gap-2 text-white">
            <MessageSquareText className="h-5 w-5 text-cyan-200" />
            <h2 className="text-xl font-semibold">Agent 辯論室</h2>
          </div>
          <p className="text-sm text-slate-500">支持觀點、反方風險與決策整合分層呈現</p>
        </div>
        <div className="grid gap-3">
          {data.debate.map((item) => (
            <div key={`${item.speaker}-${item.message}`} className={debateBubbleClass(item.tone)}>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-semibold text-white">{item.speaker}</span>
                  <span className={debateToneLabelClass(item.tone)}>{debateToneLabel(item.tone)}</span>
                </div>
                <Badge className={stanceBadgeClass(item.stance)}>{ratingDisplayLabel(item.stance)}</Badge>
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

      <ResearchSummaryCard data={data} />

      <section className="rounded-3xl border border-white/[.08] bg-white/[.04] p-6">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <div className="flex items-center gap-2 text-cyan-100">
              <ShieldCheck className="h-5 w-5" />
              <h2 className="text-lg font-semibold">免責聲明</h2>
            </div>
            <p className="mt-3 text-sm leading-7 text-slate-400">{COURSE_RESEARCH_DISCLAIMER}</p>
            <p className="mt-2 text-xs leading-6 text-slate-500">{data.disclaimer}</p>
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

function ResearchHeader({
  data,
  dataQualityLabel,
  dataQualityTone,
  displayedRating,
  finalScore,
  report,
  recommendationPreview,
  sources,
}: {
  data: AnalyzeResponse;
  dataQualityLabel: string;
  dataQualityTone: "ok" | "degraded";
  displayedRating: string;
  finalScore: number | null;
  report: ResearchReportView;
  recommendationPreview: string;
  sources: AnalyzeResponse["sources"];
}) {
  return (
    <section className="relative isolate overflow-hidden border-b border-white/[.08] pb-8 pt-4 sm:pb-10">
      <div className="absolute inset-x-0 top-0 -z-10 h-px bg-gradient-to-r from-transparent via-[rgba(199,183,143,.34)] to-transparent" />
      <div className="absolute right-[-10%] top-16 -z-10 h-72 w-72 rounded-full bg-[rgba(94,137,132,.12)] blur-3xl" />
      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_220px] lg:items-start">
        <div>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs">
            <span className="font-mono uppercase tracking-[0.22em] text-[rgba(199,183,143,.72)]">public equity research</span>
            <span className="text-slate-500">期間：{data.period}</span>
            <span className="text-slate-500">最後更新：{data.lastUpdated}</span>
          </div>
          <h1 className="mt-6 text-balance text-5xl font-semibold leading-none tracking-tight text-[rgb(244,241,232)] sm:text-6xl">
            <span className="font-mono tabular-nums">{data.symbol}</span>{" "}
            <span>{data.name}</span>
          </h1>
          <p className="mt-6 max-w-4xl border-l border-[rgba(199,183,143,.32)] pl-5 text-base leading-8 text-slate-300">
            {recommendationPreview}
          </p>
        </div>
        <div className={verdictSealClass(displayedRating)}>
          <p className="text-xs tracking-[0.24em] opacity-70">投資評級</p>
          <p className="mt-4 text-3xl font-semibold tracking-tight">{ratingDisplayLabel(displayedRating)}</p>
          <dl className="mt-6 space-y-3 border-t border-current/20 pt-4 text-left text-xs leading-5 opacity-75">
            <div className="flex justify-between gap-3">
              <dt>信心</dt>
              <dd className="font-medium">{formatConfidence(report.confidenceScore)}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt>缺口</dt>
              <dd className="font-medium">{report.dataGaps.length} 項</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt>期間</dt>
              <dd className="font-medium">{data.period}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt>更新</dt>
              <dd className="font-medium">{data.lastUpdated}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt>品質</dt>
              <dd className="font-medium">{dataQualityLabel}</dd>
            </div>
            <div>
              <dt>來源</dt>
              <dd className="mt-1 font-medium">{formatSourceNames(sources)}</dd>
            </div>
          </dl>
        </div>
      </div>
      <div className="mt-9 grid border border-white/[.08] bg-[rgba(8,12,14,.58)] sm:grid-cols-2 xl:grid-cols-4">
        <QuoteStripItem label="綜合分數" value={formatScore(finalScore)} />
        <QuoteStripItem label="資料品質" value={dataQualityLabel} tone={dataQualityTone} />
        <QuoteStripItem label="最新收盤" value={formatPlainMetric(data.metrics.latestClose)} />
        <QuoteStripItem label="20 日報酬" value={formatSignedMetric(data.metrics.return20d, "%")} />
      </div>
    </section>
  );
}

function stanceBadgeClass(stance: string) {
  if (stance.includes("Buy")) return "border-emerald-300/20 bg-emerald-300/10 text-emerald-100";
  if (stance.includes("Sell")) return "border-amber-300/20 bg-amber-300/10 text-amber-100";
  return "border-cyan-300/20 bg-cyan-300/10 text-cyan-100";
}

function verdictSealClass(stance: string) {
  const base =
    "border px-6 py-5 text-center shadow-[0_28px_90px_rgba(0,0,0,.22)] lg:justify-self-end";
  if (stance.includes("Buy")) {
    return `${base} border-[rgba(140,174,145,.42)] bg-[rgba(74,104,82,.18)] text-[rgb(207,224,203)]`;
  }
  if (stance.includes("Sell")) {
    return `${base} border-[rgba(202,162,103,.42)] bg-[rgba(130,91,45,.16)] text-[rgb(234,204,153)]`;
  }
  return `${base} border-[rgba(199,183,143,.42)] bg-[rgba(93,86,66,.18)] text-[rgb(229,218,190)]`;
}

function QuoteStripItem({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "ok" | "degraded";
}) {
  const toneClass =
    tone === "ok"
      ? "text-[rgb(194,211,196)]"
      : tone === "degraded"
        ? "text-[rgb(232,190,128)]"
        : "text-[rgb(244,241,232)]";

  return (
    <div className="border-b border-white/[.08] p-4 last:border-b-0 sm:border-r xl:border-b-0 xl:last:border-r-0">
      <p className="text-xs tracking-[0.18em] text-slate-500">{label}</p>
      <p className={`mt-2 font-mono text-xl font-semibold tabular-nums ${toneClass}`}>{value}</p>
    </div>
  );
}

function debateBubbleClass(tone: string) {
  const base = "rounded-2xl border p-4";
  if (tone === "support") return `${base} border-emerald-300/15 bg-emerald-300/[.045]`;
  if (tone === "risk") return `${base} border-amber-300/15 bg-amber-300/[.05]`;
  if (tone === "summary") return `${base} border-cyan-300/20 bg-cyan-300/[.075] shadow-glass`;
  return `${base} border-white/[.06] bg-white/[.035]`;
}

function debateToneLabel(tone: string) {
  if (tone === "support") return "支持觀點";
  if (tone === "risk") return "反方風險";
  if (tone === "summary") return "決策整合";
  return "中性觀察";
}

function debateToneLabelClass(tone: string) {
  const base = "rounded-full px-2.5 py-1 text-xs font-semibold";
  if (tone === "support") return `${base} bg-emerald-300/10 text-emerald-100`;
  if (tone === "risk") return `${base} bg-amber-300/10 text-amber-100`;
  if (tone === "summary") return `${base} bg-cyan-300/10 text-cyan-100`;
  return `${base} bg-white/[.06] text-slate-300`;
}

function AgentInsightCard({ agent }: { agent: AnalyzeResponse["agents"][number] }) {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="border-b border-white/[.06] pb-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <CardTitle>{agent.name}</CardTitle>
            <p className="mt-2 text-sm leading-6 text-slate-500">{agent.role}</p>
          </div>
          <div className="flex flex-wrap gap-2 sm:justify-end">
            {agent.degraded ? <Badge className="border-amber-300/20 bg-amber-300/10 text-amber-100">資料降級</Badge> : null}
            <Badge className={stanceBadgeClass(agent.stance)}>{ratingDisplayLabel(agent.stance)}</Badge>
          </div>
        </div>
        <div className="grid gap-3 pt-3 sm:grid-cols-2">
          <AgentMetric label="score" value={formatScore(agent.score)} tone={agent.score > 0 ? "positive" : agent.score < 0 ? "risk" : "neutral"} />
          <AgentMetric label="confidence" value={`${Math.round(agent.confidence * 100)}%`} tone="neutral" />
        </div>
      </CardHeader>
      <CardContent className="pt-5">
        <p className="rounded-2xl border border-cyan-300/10 bg-cyan-300/[.045] p-4 text-sm leading-7 text-slate-200">{agent.narrative}</p>
        <div className="mt-5 flex items-center gap-3">
          <div className="h-2 flex-1 rounded-full bg-white/[.07]">
            <div className="h-full rounded-full bg-cyan-300/75" style={{ width: `${agent.confidence * 100}%` }} />
          </div>
          <span className="text-xs font-semibold text-cyan-100">信心程度</span>
        </div>

        <div className="mt-5 grid gap-3 xl:grid-cols-3">
          <AgentDetailGroup title="使用數據" items={agent.evidence} />
          <AgentDetailGroup title="主要理由" items={agent.reasons} />
          <AgentDetailGroup title="風險提醒" items={agent.risks} tone="risk" />
        </div>
      </CardContent>
    </Card>
  );
}

function AgentMetric({ label, value, tone }: { label: string; value: string; tone: "positive" | "risk" | "neutral" }) {
  const toneClass = tone === "positive" ? "text-emerald-100" : tone === "risk" ? "text-amber-100" : "text-cyan-100";

  return (
    <div className="rounded-2xl border border-white/[.06] bg-slate-950/35 px-4 py-3">
      <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className={`mt-1 text-lg font-semibold ${toneClass}`}>{value}</p>
    </div>
  );
}

function StructuredResearchReport({ data, report }: { data: AnalyzeResponse; report: ResearchReportView }) {
  const sections = [
    { title: "投資論點", items: report.investmentThesis, icon: Lightbulb },
    { title: "估值與財務分析", items: [...report.valuation, ...report.financialAnalysis], icon: Scale },
    { title: "商業品質", items: report.businessQuality, icon: FileText },
    { title: "催化因素", items: report.catalysts, icon: CheckCircle2 },
    { title: "風險與反方觀點", items: [...report.risks, ...report.variantView], icon: AlertTriangle, tone: "risk" as const },
    { title: "資料缺口", items: report.dataGaps.length > 0 ? report.dataGaps : ["未偵測到核心資料缺口，但資料仍可能延遲或不完整。"], icon: Database, tone: "gap" as const },
  ];

  return (
    <section className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,.9fr)]">
      <Card className="border-[rgba(199,183,143,.18)] bg-[rgba(199,183,143,.045)]">
        <CardHeader className="border-b border-white/[.06]">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <CardTitle>投資結論</CardTitle>
              <p className="mt-3 text-sm leading-7 text-slate-300">{data.decision.recommendationText}</p>
              <p className="mt-3 rounded-2xl border border-amber-300/15 bg-amber-300/[.045] p-3 text-xs leading-6 text-amber-100/85">
                {COURSE_RESEARCH_DISCLAIMER}
              </p>
            </div>
            <div className="min-w-[240px] rounded-2xl border border-white/[.08] bg-slate-950/35 p-4">
              <p className="text-xs tracking-[0.16em] text-slate-500">RESEARCH RATING</p>
              <Badge className={`mt-3 ${stanceBadgeClass(report.recommendation)}`}>{ratingDisplayLabel(report.recommendation)}</Badge>
              <dl className="mt-4 grid gap-3 text-xs">
                <div>
                  <dt className="text-slate-500">信心分數</dt>
                  <dd className="mt-1 font-mono text-2xl font-semibold text-white">{formatConfidence(report.confidenceScore)}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">資料缺口</dt>
                  <dd className="mt-1 text-slate-300">{formatListSummary(report.dataGaps)}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">主要風險</dt>
                  <dd className="mt-1 text-slate-300">{formatListSummary(report.risks)}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">反方觀點</dt>
                  <dd className="mt-1 text-slate-300">{formatListSummary(report.variantView)}</dd>
                </div>
              </dl>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-5">
          <div className="mb-5 rounded-2xl border border-cyan-300/10 bg-cyan-300/[.045] p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-cyan-100/70">建議理由</p>
            <p className="mt-2 text-sm leading-7 text-slate-200">{data.decision.recommendationText || "舊版 API 未提供完整建議理由，請搭配下方分數與風險項目判讀。"}</p>
          </div>
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">關鍵數據</p>
          <div className="grid gap-2 sm:grid-cols-2">
            {report.keyMetrics.map((metric) => (
              <div key={metric} className="rounded-2xl border border-white/[.06] bg-slate-950/30 px-4 py-3 text-sm text-slate-300">
                {metric}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-1">
        {sections.map((section) => (
          <ResearchSectionCard key={section.title} title={section.title} items={section.items} icon={section.icon} tone={section.tone} />
        ))}
      </div>
    </section>
  );
}

function ResearchSectionCard({
  title,
  items,
  icon: Icon,
  tone = "default",
}: {
  title: string;
  items: string[];
  icon: LucideIcon;
  tone?: "default" | "risk" | "gap";
}) {
  const toneClass =
    tone === "risk"
      ? "border-amber-300/15 bg-amber-300/[.045]"
      : tone === "gap"
        ? "border-cyan-300/15 bg-cyan-300/[.04]"
        : "border-white/[.08] bg-white/[.035]";

  return (
    <Card className={toneClass}>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Icon className="h-5 w-5 text-cyan-100" />
          <CardTitle>{title}</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2 text-sm leading-6 text-slate-300">
          {(items.length > 0 ? items : ["資料暫無"]).map((item) => (
            <li key={item} className="rounded-2xl border border-white/[.06] bg-slate-950/25 p-3">
              {item}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

function AgentDetailGroup({ title, items, tone = "default" }: { title: string; items: string[]; tone?: "default" | "risk" }) {
  const visibleItems = items.length > 0 ? items.slice(0, 3) : ["資料暫無"];

  return (
    <div className={`rounded-2xl border p-3 ${tone === "risk" ? "border-amber-300/10 bg-amber-300/[.035]" : "border-white/[.06] bg-white/[.025]"}`}>
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{title}</p>
      <ul className="mt-3 space-y-2 text-xs leading-5 text-slate-400">
        {visibleItems.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function ResearchSummaryCard({ data }: { data: AnalyzeResponse }) {
  return (
    <section className="overflow-hidden rounded-3xl border border-cyan-300/15 bg-cyan-300/[.045] shadow-glass">
      <div className="grid gap-0 lg:grid-cols-[1fr_280px]">
        <div className="p-6">
          <div className="flex items-center gap-2 text-cyan-100">
            <FileText className="h-5 w-5" />
            <h2 className="text-lg font-semibold text-white">綜合研究摘要</h2>
          </div>
          <p className="mt-4 text-sm leading-8 text-slate-200">{data.decision.recommendationText}</p>
          <p className="mt-4 text-xs leading-5 text-slate-500">本摘要僅供課程研究與投資參考，不構成任何買賣建議。</p>
        </div>
        <aside className="border-t border-white/[.08] bg-slate-950/35 p-6 lg:border-l lg:border-t-0">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">研究資訊</p>
          <dl className="mt-4 space-y-4 text-sm">
            <div>
              <dt className="text-slate-500">最後更新</dt>
              <dd className="mt-1 font-medium text-white">{data.lastUpdated}</dd>
            </div>
            <div>
              <dt className="text-slate-500">綜合評級</dt>
              <dd className="mt-1">
                <Badge className={stanceBadgeClass(data.rating)}>{ratingDisplayLabel(data.rating)}</Badge>
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">資料來源</dt>
              <dd className="mt-2 flex flex-wrap gap-2">
                {(data.sources ?? []).map((source) => (
                  <Badge
                    key={`${source.name}-${source.status}`}
                    className={isSourceDegraded(source) ? "border-amber-300/20 bg-amber-300/10 text-amber-100" : "border-emerald-300/20 bg-emerald-300/10 text-emerald-100"}
                  >
                    {source.name}
                  </Badge>
                ))}
              </dd>
            </div>
          </dl>
        </aside>
      </div>
    </section>
  );
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

function ScoreBreakdown({
  scoreBreakdown,
  finalScore,
  confidenceScore,
}: {
  scoreBreakdown: Record<string, number>;
  finalScore: number | null;
  confidenceScore: number | null;
}) {
  const items = [
    { label: "財務或價格表現", key: "financialOrPricePerformance", max: 25 },
    { label: "成長性", key: "growth", max: 20 },
    { label: "估值合理性", key: "valuationReasonableness", max: 20 },
    { label: "催化因素", key: "catalysts", max: 15 },
    { label: "風險控制", key: "riskControl", max: 20 },
  ].map((item) => ({
    ...item,
    score: safeNumber(scoreBreakdown[item.key]),
  }));

  return (
    <section className="rounded-3xl border border-white/[.08] bg-white/[.04] p-6 shadow-glass">
      <div className="mb-5 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <div className="flex items-center gap-2 text-cyan-100">
            <GaugeCircle className="h-5 w-5" />
            <h2 className="text-lg font-semibold text-white">研究評分拆解</h2>
          </div>
          <p className="mt-2 text-sm text-slate-400">總分 100 分，由財務或價格表現、成長性、估值、催化因素與風險控制組成。</p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-2xl border border-cyan-300/15 bg-cyan-300/[.06] px-4 py-3 text-right">
            <p className="text-xs text-cyan-100/70">總分</p>
            <p className="text-2xl font-semibold text-white">{formatResearchScore(finalScore)}</p>
          </div>
          <div className="rounded-2xl border border-cyan-300/15 bg-cyan-300/[.06] px-4 py-3 text-right">
            <p className="text-xs text-cyan-100/70">confidenceScore</p>
            <p className="text-2xl font-semibold text-white">{confidenceScore === null ? "資料暫無" : `${confidenceScore}/100`}</p>
          </div>
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        {items.map((item) => (
          <div key={item.label} className="rounded-2xl border border-white/[.07] bg-slate-950/35 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-medium text-white">{item.label}</p>
                <p className="mt-1 text-xs text-slate-500">滿分 {item.max}</p>
              </div>
              <span className="text-sm font-semibold text-cyan-100">{formatCategoryScore(item.score, item.max)}</span>
            </div>
            <ScoreBar score={item.score} max={item.max} />
          </div>
        ))}
      </div>
    </section>
  );
}

function ScoreBar({ score, max }: { score: number | null; max: number }) {
  const width = score === null ? 0 : Math.max(0, Math.min(100, (score / max) * 100));
  const color = score === null ? "bg-slate-500/50" : width >= 70 ? "bg-emerald-300/75" : width >= 45 ? "bg-cyan-300/75" : "bg-amber-300/75";

  return (
    <div className="relative mt-4 h-2 rounded-full bg-white/[.08]">
      <div
        className={`absolute left-0 top-0 h-full rounded-full ${color}`}
        style={{ width: `${width}%` }}
      />
    </div>
  );
}

function normalizeResearchReport(data: AnalyzeResponse): ResearchReportView {
  const report = data.decision?.researchReport;
  const recommendationText = data.decision?.recommendationText || "舊版 API 未提供完整建議理由，請搭配現有分數、資料來源與風險項目保守判讀。";
  const fallbackGap = report
    ? "部分研究報告欄位未回傳，已使用可用資料保守呈現。"
    : "舊版 API 未提供 researchReport，已使用 recommendationText 與 scoreBreakdown 保守呈現。";

  return {
    investmentThesis: safeStringList(report?.investmentThesis, [recommendationText]),
    keyMetrics: safeStringList(report?.keyMetrics, buildFallbackKeyMetrics(data)),
    businessQuality: safeStringList(report?.businessQuality, ["商業品質資料暫無完整回傳，需搭配後續財報與營收資料判讀。"]),
    financialAnalysis: safeStringList(report?.financialAnalysis, data.decision?.supportReasons),
    valuation: safeStringList(report?.valuation, ["估值資料不足時，不應單獨依賴本評級作為買賣依據。"]),
    catalysts: safeStringList(report?.catalysts, data.decision?.watchPoints, ["催化因素暫無完整資料。"]),
    risks: safeStringList(report?.risks, data.decision?.risks, ["風險資料暫無完整回傳，請以資料來源狀態與 Agent 降級提示輔助判讀。"]),
    variantView: safeStringList(report?.variantView, ["若後續基本面、籌碼或價格資料不支持目前訊號，評級應下修或重新評估。"]),
    recommendation: report?.recommendation ?? data.rating ?? "Neutral / 中性",
    confidenceScore: safeNumber(report?.confidenceScore),
    dataGaps: safeStringList(report?.dataGaps, [fallbackGap]),
    scoreBreakdown: report?.scoreBreakdown ?? data.decision?.scoreBreakdown ?? {},
  };
}

function buildFallbackKeyMetrics(data: AnalyzeResponse) {
  return [
    `最新收盤：${formatPlainMetric(data.metrics.latestClose)}`,
    `20 日報酬：${formatSignedMetric(data.metrics.return20d, "%")}`,
    `本益比：${formatPeMetric(data.metrics)}`,
    `EPS：${formatPlainMetric(data.metrics.eps)}`,
  ];
}

function safeStringList(...candidates: unknown[]) {
  for (const candidate of candidates) {
    if (!Array.isArray(candidate)) continue;
    const items = candidate.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
    if (items.length > 0) return items;
  }
  return ["資料暫無"];
}

function ratingDisplayLabel(stance: string) {
  if (stance.startsWith("Strong Buy")) return "Strong Buy｜強烈買進傾向";
  if (stance.startsWith("Buy")) return "Buy｜買進傾向";
  if (stance.startsWith("Neutral")) return "Neutral｜中立觀察";
  if (stance.startsWith("Strong Sell")) return "Strong Sell｜強烈賣出傾向";
  if (stance.startsWith("Sell")) return "Sell｜賣出傾向";
  return stance || "Neutral｜中立觀察";
}

function formatConfidence(value: number | null) {
  return value === null ? "資料暫無" : `${value}/100`;
}

function formatListSummary(items: string[]) {
  if (items.length === 0) return "資料暫無";
  return items.slice(0, 2).join("；");
}

function isSourceDegraded(source: AnalyzeResponse["sources"][number]) {
  const status = String(source.status ?? "").toLowerCase();
  return !(status === "ok" || status === "success" || status === "正常");
}

function previewText(text: string | undefined) {
  if (!text) return "系統已完成多 Agent 分析，請參考下方技術面、基本面、籌碼面與風險控管結果。";
  return text.length > 112 ? `${text.slice(0, 112)}...` : text;
}

function safeNumber(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function formatScore(value: number | null) {
  if (value === null) return "資料暫無";
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}`;
}

function formatResearchScore(value: number | null) {
  if (value === null) return "資料暫無";
  return `${value.toFixed(1)}/100`;
}

function formatCategoryScore(value: number | null, max: number) {
  if (value === null) return "資料暫無";
  return `${value.toFixed(1)}/${max}`;
}

function formatPlainMetric(value: number | null) {
  if (value === null) return "資料暫無";
  return value.toLocaleString("zh-TW", { maximumFractionDigits: 2 });
}

function formatSignedMetric(value: number | null, suffix = "") {
  if (value === null) return "資料暫無";
  return `${value > 0 ? "+" : ""}${value.toLocaleString("zh-TW", { maximumFractionDigits: 2 })}${suffix}`;
}

function displayPeRatio(metrics: AnalyzeResponse["metrics"]) {
  if (metrics.eps !== null && metrics.eps < 0) return null;
  if (metrics.peRatio !== null && metrics.peRatio <= 0) return null;
  return metrics.peRatio;
}

function formatPeMetric(metrics: AnalyzeResponse["metrics"]) {
  if (metrics.peRatio === null) return "資料暫無";
  if (displayPeRatio(metrics) === null) {
    return `不適用（EPS ${formatPlainMetric(metrics.eps)}，PE 不具一般估值意義）`;
  }
  return formatPlainMetric(metrics.peRatio);
}

function formatSourceNames(sources: AnalyzeResponse["sources"]) {
  if (sources.length === 0) return "資料暫無";
  return sources.map((source) => source.name).join(" / ");
}
