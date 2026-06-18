"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, Database, Download, FileText, GaugeCircle, Lightbulb, Loader2, MessageSquareText, Scale, ShieldCheck } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { StockCharts } from "@/components/charts/stock-charts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { analyzeStock } from "@/lib/api";
import type { AnalyzeResponse } from "@/lib/types";

const COURSE_RESEARCH_DISCLAIMER =
  "本系統僅供課程研究與資料分析展示，所有評級與建議皆為規則式模型輸出，不構成正式投資建議或獲利保證。";
const RETRY_DELAY_MS = 1_500;
const TAB_CARD_PREVIEW_LIMIT = 3;

type ResearchReportView = {
  isLegacyFallback: boolean;
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

type ResearchTabId = "summary" | "technical" | "fundamental" | "risk" | "conclusion";

type ResearchTabGroup = {
  title: string;
  items: string[];
  tone?: "default" | "risk" | "gap";
  badges?: ResearchTabBadge[];
  metrics?: ResearchTabMetric[];
};

type ResearchTabHighlight = {
  label: string;
  value: string;
};

type ResearchTabBadge = {
  label: string;
  tone?: "default" | "ok" | "gap";
};

type ResearchTabMetric = {
  label: string;
  value: string;
  tone?: "default" | "positive" | "negative" | "muted";
};

type ResearchTab = {
  id: ResearchTabId;
  label: string;
  description: string;
  icon: LucideIcon;
  groups: ResearchTabGroup[];
  highlights?: ResearchTabHighlight[];
  showCharts?: boolean;
};

export function StockAnalysisClient({ symbol }: { symbol: string }) {
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isCachedResult, setIsCachedResult] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const requestIdRef = useRef(0);

  const loadAnalysis = useCallback(
    async ({ allowAutoRetry = true }: { allowAutoRetry?: boolean } = {}) => {
      const requestId = requestIdRef.current + 1;
      requestIdRef.current = requestId;
      setIsLoading(true);
      setError(null);
      try {
        const result = await analyzeStockWithRetry(symbol, allowAutoRetry);
        if (requestId !== requestIdRef.current) return;
        writeCachedAnalysis(symbol, result);
        setData(result);
        setIsCachedResult(false);
      } catch (loadError) {
        if (requestId !== requestIdRef.current) return;
        const cached = readCachedAnalysis(symbol);
        if (cached) {
          setData(cached);
          setIsCachedResult(true);
          setError(getAnalysisErrorMessage(loadError));
        } else {
          setData(null);
          setIsCachedResult(false);
          setError("資料來源回應較慢，可能是後端冷啟動或外部資料暫時延遲。請稍後重新取得分析。");
        }
      } finally {
        if (requestId === requestIdRef.current) setIsLoading(false);
      }
    },
    [symbol],
  );

  useEffect(() => {
    loadAnalysis();
    return () => {
      requestIdRef.current += 1;
    };
  }, [loadAnalysis]);

  if (isLoading) {
    return (
      <div className="rounded-3xl border border-[#e4dccf] bg-[#fffdf9] p-8 text-[#2b2925] shadow-[0_20px_50px_rgba(57,49,37,.08)]">
        <Loader2 className="mb-4 h-8 w-8 animate-spin text-[#2f6b4f]" />
        <h1 className="text-2xl font-semibold">正在取得股票分析資料</h1>
        <p className="mt-3 text-sm leading-7 text-[#746b60]">系統正在呼叫 FastAPI，若資料來源較慢會自動逾時並顯示提示。</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-3xl border border-[#ead6ad] bg-[#fff9ee] p-8 text-[#4d3b1f] shadow-[0_20px_50px_rgba(57,49,37,.08)]">
        <AlertTriangle className="mb-4 h-8 w-8 text-[#b7791f]" />
        <h1 className="text-2xl font-semibold">暫時無法取得分析資料</h1>
        <p className="mt-3 text-sm leading-7 text-[#7a6140]">{error}</p>
        <Button className="mt-6" variant="secondary" onClick={() => loadAnalysis({ allowAutoRetry: false })}>
          重新取得分析
        </Button>
      </div>
    );
  }

  const finalScore = typeof data.decision?.finalScore === "number" ? data.decision.finalScore : null;
  const researchReport = normalizeResearchReport(data);
  const displayedRating = data.decision?.rating ?? researchReport.recommendation ?? data.rating;
  const recommendationPreview = previewText(data.decision?.recommendationText);
  const hasFinMindPublicMode = hasFinMindPublicModeNotice(data, researchReport);
  const sourceIssues = (data.sources ?? []).filter((source) => isSourceDegraded(source, hasFinMindPublicMode));
  const hasDegradedAgent = data.agents.some((agent) => agent.degraded);
  const dataQualityLabel = sourceIssues.length === 0 && !hasDegradedAgent ? "資料來源正常" : "部分資料降級";
  const dataQualityTone = sourceIssues.length === 0 && !hasDegradedAgent ? "ok" : "degraded";

  return (
    <div className="w-full max-w-none space-y-5 font-['Noto_Serif_TC','Songti_TC','PMingLiU',serif] text-[#2b2925]">
      {isCachedResult ? <CachedAnalysisNotice onRetry={() => loadAnalysis({ allowAutoRetry: false })} /> : null}

      <ResearchHeader
        data={data}
        dataQualityLabel={dataQualityLabel}
        dataQualityTone={dataQualityTone}
        displayedRating={displayedRating}
        finalScore={finalScore}
        report={researchReport}
        recommendationPreview={recommendationPreview}
        sources={data.sources ?? []}
        hasFinMindPublicMode={hasFinMindPublicMode}
      />

      <StructuredResearchReport data={data} report={researchReport} />
    </div>
  );
}

function CachedAnalysisNotice({ onRetry }: { onRetry: () => void }) {
  return (
    <section className="rounded-3xl border border-amber-300/20 bg-amber-300/[.055] p-5 text-amber-50">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-100" />
          <div>
            <h2 className="text-base font-semibold">目前顯示最近一次成功分析</h2>
            <p className="mt-1 text-sm leading-6 text-amber-100/75">資料可能不是最新；後端可能正在冷啟動，或外部資料來源暫時延遲。</p>
          </div>
        </div>
        <Button variant="secondary" onClick={onRetry}>
          重新取得分析
        </Button>
      </div>
    </section>
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
  hasFinMindPublicMode,
}: {
  data: AnalyzeResponse;
  dataQualityLabel: string;
  dataQualityTone: "ok" | "degraded";
  displayedRating: string;
  finalScore: number | null;
  report: ResearchReportView;
  recommendationPreview: string;
  sources: AnalyzeResponse["sources"];
  hasFinMindPublicMode: boolean;
}) {
  return (
    <section className="overflow-hidden rounded-3xl border border-[#e4dccf] bg-[#fffdf9] shadow-[0_24px_70px_rgba(57,49,37,.08)]">
      <div className="grid gap-6 p-5 sm:p-8 xl:grid-cols-[minmax(0,1fr)_320px] xl:p-10">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-[#8a8175]">
            <span className="font-semibold uppercase tracking-[0.24em] text-[#b88a45]">equity research masthead</span>
            <span>研究期間 {data.period}</span>
            <span>最後更新：{data.lastUpdated}</span>
          </div>
          <p className="mt-2 text-xs leading-6 text-[#766d62]">資料來源：{formatSourceNames(sources, hasFinMindPublicMode)}</p>
          <h1 className="mt-6 break-words text-5xl font-semibold leading-none tracking-tight text-[#24221f] sm:text-6xl lg:text-7xl">
            <span className="tabular-nums">{data.symbol}</span>{" "}
            <span>{data.name}</span>
          </h1>
          <div className="mt-6 max-w-4xl border-l border-[#e2cfac] pl-5">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#b88a45]">recommendation preview</p>
            <p className="mt-3 text-sm leading-8 text-[#514b43]">{recommendationPreview}</p>
          </div>
        </div>
        <aside className="rounded-3xl border border-[#ddd3c6] bg-[#fbf7ef] p-5 shadow-[0_18px_46px_rgba(57,49,37,.06)] sm:p-6">
          <div className={verdictSealClass(displayedRating)}>
            <p className="text-xs font-semibold tracking-[0.18em] opacity-75">綜合判斷</p>
            <p className="mt-4 text-3xl font-semibold tracking-tight">{ratingDisplayLabel(displayedRating)}</p>
          </div>
          <dl className="mt-5 grid grid-cols-2 overflow-hidden rounded-2xl border border-[#e5ddd2] bg-white text-sm">
            <div className="border-r border-[#e5ddd2] p-4">
              <dt className="text-xs text-[#8a8175]">信心分數</dt>
              <dd className="mt-2 text-2xl font-semibold tabular-nums text-[#2f6b4f]">{formatConfidence(report.confidenceScore, report.isLegacyFallback)}</dd>
            </div>
            <div className="p-4">
              <dt className="text-xs text-[#8a8175]">資料缺口</dt>
              <dd className="mt-2 text-2xl font-semibold tabular-nums text-[#5e4631]">{report.dataGaps.length} 項</dd>
            </div>
          </dl>
          <p className="mt-4 text-xs leading-6 text-[#746b60]">來源狀態：{formatSourceNames(sources, hasFinMindPublicMode)}</p>
        </aside>
      </div>
      <div className="grid gap-3 border-t border-[#e8e0d5] bg-[#fbf7ef] p-3 sm:grid-cols-2 xl:grid-cols-5">
        <QuoteStripItem label="綜合分數" value={formatScore(finalScore)} />
        <QuoteStripItem label="最新收盤" value={formatPlainMetric(data.metrics.latestClose)} />
        <QuoteStripItem label="20 日報酬" value={formatSignedMetric(data.metrics.return20d, "%")} />
        <QuoteStripItem label="資料品質" value={dataQualityLabel} tone={dataQualityTone} />
        <QuoteStripItem label="來源狀態" value={formatSourceNames(sources, hasFinMindPublicMode)} tone={dataQualityTone} />
      </div>
    </section>
  );
}

function stanceBadgeClass(stance: string) {
  if (isBuyStance(stance)) return "border-red-200 bg-red-50 text-red-700";
  if (isSellStance(stance)) return "border-emerald-200 bg-emerald-50 text-emerald-700";
  return "border-amber-200 bg-amber-50 text-amber-700";
}

function verdictSealClass(stance: string) {
  const base = "rounded-2xl border px-6 py-5 text-center shadow-[0_18px_42px_rgba(57,49,37,.06)]";
  if (isBuyStance(stance)) {
    return `${base} border-red-200 bg-red-50 text-red-700`;
  }
  if (isSellStance(stance)) {
    return `${base} border-emerald-200 bg-emerald-50 text-emerald-700`;
  }
  return `${base} border-amber-200 bg-amber-50 text-amber-700`;
}

function isBuyStance(stance: string) {
  return /Buy|買進|偏多|強烈買進|買進傾向/i.test(stance);
}

function isSellStance(stance: string) {
  return /Sell|賣出|偏空|偏弱|賣出傾向/i.test(stance);
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
      ? "text-[#2f6b4f]"
      : tone === "degraded"
        ? "text-[#b7791f]"
        : "text-[#2b2925]";

  return (
    <div className="min-w-0 rounded-2xl border border-[#e4dccf] bg-white px-4 py-3 shadow-[0_8px_22px_rgba(57,49,37,.04)]">
      <p className="text-xs tracking-[0.12em] text-[#8a8175]">{label}</p>
      <p className={`mt-2 break-words text-lg font-semibold tabular-nums ${toneClass}`}>{value}</p>
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

function buildTechnicalHighlights(metrics: AnalyzeResponse["metrics"]): ResearchTabHighlight[] {
  return [
    { label: "最新收盤", value: formatPlainMetric(metrics.latestClose) },
    { label: "20 日報酬", value: formatSignedMetric(metrics.return20d, "%") },
    { label: "MA20", value: formatPlainMetric(metrics.ma20) },
    { label: "MA60", value: formatPlainMetric(metrics.ma60) },
    { label: "短線動能", value: formatMomentumLabel(metrics.return20d) },
    { label: "目前位階", value: formatMovingAveragePosition(metrics.latestClose, metrics.ma20, metrics.ma60) },
  ];
}

function formatMomentumLabel(return20d: number | null) {
  if (return20d === null) return "資料暫無";
  if (return20d > 0) return "偏正向";
  if (return20d < 0) return "偏弱";
  return "接近持平";
}

function formatMovingAveragePosition(latestClose: number | null, ma20: number | null, ma60: number | null) {
  if (latestClose === null) return "資料暫無";
  const positions = [
    ma20 === null ? null : `${latestClose >= ma20 ? "高於" : "低於"} MA20`,
    ma60 === null ? null : `${latestClose >= ma60 ? "高於" : "低於"} MA60`,
  ].filter(Boolean);

  return positions.length > 0 ? positions.join(" / ") : "資料暫無";
}

function buildResearchTabs(data: AnalyzeResponse, report: ResearchReportView): ResearchTab[] {
  const metrics = data.metrics;
  const institutional = data.chipData?.institutional ?? null;
  const margin = data.chipData?.margin ?? null;
  const chipDataGaps = formatChipDataGaps(data.chipData);
  const peWarning =
    metrics.peRatio === null
      ? "PE：資料暫無，無法用本益比判斷估值。"
      : displayPeRatio(metrics) === null
        ? `PE：EPS ${formatPlainMetric(metrics.eps)}，本益比不適合解讀，避免用無效 PE 下估值結論。`
        : `PE：${formatPlainMetric(metrics.peRatio)}`;
  const shortMomentum =
    metrics.return20d === null
      ? "短線動能：20 日報酬資料暫無。"
      : metrics.return20d > 0
        ? `短線動能：20 日報酬 ${formatSignedMetric(metrics.return20d, "%")}，價格動能偏正向。`
        : metrics.return20d < 0
          ? `短線動能：20 日報酬 ${formatSignedMetric(metrics.return20d, "%")}，價格動能偏弱。`
          : "短線動能：20 日報酬接近持平。";
  const maContext = [
    `最新收盤：${formatPlainMetric(metrics.latestClose)}`,
    `MA20：${formatPlainMetric(metrics.ma20)}`,
    `MA60：${formatPlainMetric(metrics.ma60)}`,
    `20 日報酬：${formatSignedMetric(metrics.return20d, "%")}`,
  ];

  return [
    {
      id: "summary",
      label: "摘要",
      description: "先看投資結論、信心分數、核心理由、資料缺口與主要風險。",
      icon: Lightbulb,
      groups: [
        { title: "Rating / Confidence", items: [`Rating：${ratingDisplayLabel(report.recommendation)}`, `Confidence：${formatConfidence(report.confidenceScore, report.isLegacyFallback)}`] },
        { title: "核心理由", items: report.investmentThesis },
        { title: "資料缺口", items: report.dataGaps.length > 0 ? report.dataGaps : ["未偵測到核心資料缺口，但資料仍可能延遲或不完整。"], tone: "gap" },
        { title: "主要風險", items: report.risks, tone: "risk" },
      ],
    },
    {
      id: "technical",
      label: "技術面",
      description: "聚焦官方日 K 股價、均線、20 日報酬與短線動能；若官方資料不可用，才使用 yfinance fallback。",
      icon: GaugeCircle,
      showCharts: true,
      highlights: buildTechnicalHighlights(metrics),
      groups: [
        { title: "價格與均線", items: maContext },
        { title: "短線動能", items: [shortMomentum] },
        { title: "技術結論", items: report.keyMetrics },
      ],
    },
    {
      id: "fundamental",
      label: "基本面 / 估值",
      description: "整理 EPS、PE、營收成長與估值文字；PE 不適合解讀時明確警示。",
      icon: Scale,
      groups: [
        { title: "獲利與營收", items: [`EPS：${formatPlainMetric(metrics.eps)}`, `營收成長：${formatSignedMetric(metrics.revenueGrowth, "%")}`] },
        { title: "估值說明", items: [peWarning, ...report.valuation] },
        { title: "基本面分析", items: [...report.businessQuality, ...report.financialAnalysis] },
      ],
    },
    {
      id: "risk",
      label: "籌碼與風險",
      description: "呈現官方三大法人、融資融券、風險與反方觀點；官方資料不可用時列為資料缺口。",
      icon: AlertTriangle,
      groups: [
        {
          title: "籌碼整體狀態",
          items: [`資料狀態：${formatChipStatus(data.chipData?.overallStatus)}`],
          tone: data.chipData?.overallStatus === "missing" || data.chipData?.overallStatus === "partial" ? "gap" : "default",
          badges: [{
            label: formatChipStatus(data.chipData?.overallStatus),
            tone: data.chipData?.overallStatus === "missing" || data.chipData?.overallStatus === "partial" ? "gap" : "ok",
          }],
        },
        {
          title: "三大法人買賣超",
          items: [
            `資料來源：${formatOfficialText(institutional?.source)}`,
            `資料狀態：${formatChipStatus(institutional?.status)}`,
            `資料日期：${formatOfficialDate(institutional?.dataDate ?? institutional?.asOfDate)}`,
          ],
          tone: institutional?.status === "missing" ? "gap" : "default",
          badges: [{ label: formatChipStatus(institutional?.status), tone: institutional?.status === "missing" ? "gap" : "ok" }],
          metrics: [
            { label: "外資買賣超", value: formatOfficialInteger(institutional?.foreignNetBuy, "股"), tone: officialNumberTone(institutional?.foreignNetBuy) },
            { label: "投信買賣超", value: formatOfficialInteger(institutional?.investmentTrustNetBuy, "股"), tone: officialNumberTone(institutional?.investmentTrustNetBuy) },
            { label: "自營商買賣超", value: formatOfficialInteger(institutional?.dealerNetBuy, "股"), tone: officialNumberTone(institutional?.dealerNetBuy) },
            { label: "三大法人合計", value: formatOfficialInteger(institutional?.institutionalNetBuyTotal, "股"), tone: officialNumberTone(institutional?.institutionalNetBuyTotal) },
          ],
        },
        {
          title: "融資融券",
          items: [
            `資料來源：${formatOfficialText(margin?.source)}`,
            `資料狀態：${formatChipStatus(margin?.status)}`,
            `資料日期：${formatOfficialDate(margin?.dataDate ?? margin?.asOfDate)}`,
          ],
          tone: margin?.status === "missing" ? "gap" : "default",
          badges: [{ label: formatChipStatus(margin?.status), tone: margin?.status === "missing" ? "gap" : "ok" }],
          metrics: [
            { label: "融資餘額", value: formatOfficialInteger(margin?.marginBalance, "張") },
            { label: "融資增減", value: formatOfficialInteger(margin?.marginChange, "張"), tone: officialNumberTone(margin?.marginChange) },
            { label: "融券餘額", value: formatOfficialInteger(margin?.shortBalance, "張") },
            { label: "融券增減", value: formatOfficialInteger(margin?.shortChange, "張"), tone: officialNumberTone(margin?.shortChange) },
            { label: "融資使用率", value: formatOfficialPercent(margin?.marginUtilizationRate) },
            { label: "融券使用率", value: formatOfficialPercent(margin?.shortUtilizationRate) },
          ],
        },
        { title: "官方資料缺口", items: chipDataGaps, tone: chipDataGaps.length > 0 ? "gap" : "default" },
        { title: "主要風險", items: report.risks, tone: "risk" },
        { title: "反方觀點", items: report.variantView, tone: "risk" },
      ],
    },
    {
      id: "conclusion",
      label: "總結",
      description: "把操作觀察、轉強與轉弱條件、免責聲明集中在最後判讀。",
      icon: CheckCircle2,
      groups: [
        { title: "操作觀察", items: data.decision.watchPoints.length > 0 ? data.decision.watchPoints : report.catalysts },
        { title: "轉強條件", items: data.decision.supportReasons.length > 0 ? data.decision.supportReasons : report.investmentThesis },
        { title: "轉弱條件", items: data.decision.risks.length > 0 ? data.decision.risks : report.risks, tone: "risk" },
        { title: "免責聲明", items: [COURSE_RESEARCH_DISCLAIMER, data.disclaimer] },
      ],
    },
  ];
}

function StructuredResearchReport({ data, report }: { data: AnalyzeResponse; report: ResearchReportView }) {
  const [activeTab, setActiveTab] = useState<ResearchTabId>("summary");
  const reportTabs = buildResearchTabs(data, report);
  const activePanel = reportTabs.find((tab) => tab.id === activeTab) ?? reportTabs[0];
  const ActiveIcon = activePanel.icon;
  const isRiskPanel = activePanel.id === "risk";
  const leftPanelGroups = isRiskPanel ? activePanel.groups.filter((group) => group.title === "官方資料缺口") : [];
  const mainPanelGroups = isRiskPanel ? activePanel.groups.filter((group) => group.title !== "官方資料缺口") : activePanel.groups;
  const summaryPanel = <TabSummaryPanel panel={activePanel} icon={ActiveIcon} extraGroups={leftPanelGroups} />;

  return (
    <section className="overflow-hidden rounded-3xl border border-[#e4dccf] bg-[#fffdf9] shadow-[0_24px_70px_rgba(57,49,37,.07)]">
      <Card className="rounded-none border-0 bg-transparent shadow-none">
        <CardContent className="p-0">
          <div className="border-b border-[#e8e0d5] bg-[#fffdf9] px-3 py-3 sm:px-5">
            <div className="overflow-x-auto pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
              <div className="flex min-w-max gap-2 rounded-2xl border border-[#e4dccf] bg-[#fbf7ef] p-1">
                {reportTabs.map((tab) => {
                  const isActive = tab.id === activePanel.id;
                  const Icon = tab.icon;

                  return (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#d8ad63]/60 ${
                        isActive
                          ? "bg-white text-[#2b2925] shadow-[0_10px_24px_rgba(57,49,37,.08)]"
                          : "text-[#7a7166] hover:bg-white/70 hover:text-[#2b2925]"
                      }`}
                      aria-pressed={isActive}
                    >
                      <Icon className="h-4 w-4" />
                      <span>{tab.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {activePanel.showCharts ? (
            <div className="grid gap-5 p-5 lg:p-6">
              <StockCharts data={data} summary={summaryPanel} />
              <TabDetailsDisclosure groups={activePanel.groups} label="查看技術面文字摘要" />
            </div>
          ) : (
            <div className="grid gap-5 p-5 lg:grid-cols-[260px_minmax(0,1fr)] lg:items-start lg:p-6">
              {summaryPanel}
              <div className={`min-w-0 grid gap-4 ${isRiskPanel ? "md:grid-cols-2 xl:grid-cols-2" : "md:grid-cols-2"}`}>
                {activePanel.showCharts ? (
                  <div className="md:col-span-2">
                    <StockCharts data={data} />
                  </div>
                ) : null}
                {activePanel.showCharts ? (
                <TabDetailsDisclosure groups={activePanel.groups} label="查看技術面文字摘要" />
                ) : (
                  mainPanelGroups.map((group) => <ResearchSectionCard key={group.title} {...group} />)
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </section>
  );
}

function TabSummaryPanel({ panel, icon: Icon, extraGroups = [] }: { panel: ResearchTab; icon: LucideIcon; extraGroups?: ResearchTabGroup[] }) {
  return (
    <div className="grid self-start gap-4">
      <aside className="rounded-2xl border border-[#e4dccf] bg-[#fbf7ef] p-5 shadow-[0_12px_30px_rgba(57,49,37,.045)]">
        <div className="flex items-center gap-2 text-[#7d5d2e]">
          <Icon className="h-5 w-5" />
          <p className="text-sm font-semibold">{panel.label}</p>
        </div>
        <p className="mt-3 text-xs leading-6 text-[#746b60]">{panel.description}</p>
        {panel.highlights && panel.highlights.length > 0 ? (
          <dl className="mt-5 grid gap-2.5 border-t border-[#e4dccf] pt-4">
            {panel.highlights.map((item) => (
              <div key={item.label} className="flex items-start justify-between gap-3 text-xs leading-5">
                <dt className="shrink-0 text-[#8a8175]">{item.label}</dt>
                <dd className="min-w-0 text-right font-medium leading-5 text-[#2b2925]">{item.value}</dd>
              </div>
            ))}
          </dl>
        ) : null}
      </aside>
      {extraGroups.map((group) => (
        <ResearchSectionCard key={group.title} {...group} />
      ))}
    </div>
  );
}

function ResearchBriefList({
  title,
  items,
  tone = "default",
}: {
  title: string;
  items: string[];
  tone?: "default" | "risk" | "gap";
}) {
  const visibleItems = items.length > 0 ? items.slice(0, 3) : ["資料暫無"];
  const toneClass =
    tone === "risk"
      ? "border-amber-200 bg-amber-50/70"
      : tone === "gap"
        ? "border-[#d7c7ad] bg-[#fbf7ef]"
        : "border-[#e4dccf] bg-white";

  return (
    <div className={`rounded-2xl border p-4 ${toneClass}`}>
      <p className="text-xs font-semibold tracking-[0.14em] text-[#8a8175]">{title}</p>
      <ul className="mt-3 space-y-2 text-xs leading-5 text-[#514b43]">
        {visibleItems.map((item) => (
          <li key={item} className="border-t border-[#eee7dd] pt-2 first:border-t-0 first:pt-0">
            {normalizeDisplayText(item)}
          </li>
        ))}
      </ul>
    </div>
  );
}

function ResearchSectionCard({
  title,
  items,
  tone = "default",
  badges,
  metrics,
}: ResearchTabGroup) {
  const visibleMetrics = (metrics ?? []).slice(0, TAB_CARD_PREVIEW_LIMIT);
  const hiddenMetrics = (metrics ?? []).slice(TAB_CARD_PREVIEW_LIMIT);
  const normalizedItems = items.length > 0 ? items : ["資料暫無"];
  const visibleItems = normalizedItems.slice(0, TAB_CARD_PREVIEW_LIMIT);
  const hiddenItems = normalizedItems.slice(TAB_CARD_PREVIEW_LIMIT);
  const hasHiddenContent = hiddenMetrics.length > 0 || hiddenItems.length > 0;
  const toneClass =
    tone === "risk"
      ? "border-amber-200 bg-amber-50/70"
      : tone === "gap"
        ? "border-[#d7c7ad] bg-[#fbf7ef]"
        : "border-[#e4dccf] bg-white";

  return (
    <Card className={`h-full rounded-2xl shadow-[0_14px_34px_rgba(57,49,37,.05)] ${toneClass}`}>
      <CardHeader className="px-4 pb-2 pt-4 sm:px-5 sm:pt-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <CardTitle className="text-base text-[#2b2925]">{title}</CardTitle>
          {badges && badges.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {badges.map((badge) => (
                <Badge key={`${title}-${badge.label}`} className={researchBadgeClass(badge.tone)}>
                  {badge.label}
                </Badge>
              ))}
            </div>
          ) : null}
        </div>
      </CardHeader>
      <CardContent className="px-4 pb-4 sm:px-5 sm:pb-5">
        {visibleMetrics.length > 0 ? (
          <dl className="mb-3 grid gap-2.5">
            {visibleMetrics.map((metric) => (
              <div key={`${title}-${metric.label}`} className="min-w-0 rounded-xl border border-[#eee7dd] bg-[#fffdf9] p-2.5">
                <dt className="text-xs leading-5 text-[#8a8175]">{metric.label}</dt>
                <dd className={`mt-1 whitespace-nowrap text-[13px] font-semibold tabular-nums sm:text-sm ${researchMetricClass(metric.tone)}`}>{metric.value}</dd>
              </div>
            ))}
          </dl>
        ) : null}
        <ul className="space-y-2 text-sm leading-6 text-[#514b43]">
          {visibleItems.map((item, index) => (
            <li key={`${title}-${index}-${item}`} className="rounded-xl border border-[#eee7dd] bg-[#fffdf9] p-2.5">
              <span className="block overflow-hidden [display:-webkit-box] [-webkit-box-orient:vertical] [-webkit-line-clamp:2]">
                {normalizeDisplayText(item)}
              </span>
            </li>
          ))}
        </ul>
        {hasHiddenContent ? (
          <details className="mt-3 rounded-xl border border-[#eee7dd] bg-white px-3 py-2 text-sm text-[#514b43]">
            <summary className="cursor-pointer select-none text-xs font-semibold text-[#7d5d2e]">查看完整內容</summary>
            <div className="mt-3 grid gap-2">
              {hiddenMetrics.map((metric) => (
                <div key={`${title}-hidden-${metric.label}`} className="rounded-lg border border-[#eee7dd] bg-[#fffdf9] p-2">
                  <p className="text-xs text-[#8a8175]">{metric.label}</p>
                  <p className={`mt-1 text-sm font-semibold tabular-nums ${researchMetricClass(metric.tone)}`}>{metric.value}</p>
                </div>
              ))}
              {hiddenItems.map((item, index) => (
                <p key={`${title}-hidden-${index}-${item}`} className="rounded-lg border border-[#eee7dd] bg-[#fffdf9] p-2 text-xs leading-6">
                  {normalizeDisplayText(item)}
                </p>
              ))}
            </div>
          </details>
        ) : null}
      </CardContent>
    </Card>
  );
}

function TabDetailsDisclosure({ groups, label }: { groups: ResearchTabGroup[]; label: string }) {
  if (groups.length === 0) return null;

  return (
    <details className="md:col-span-2 rounded-2xl border border-[#e4dccf] bg-[#fbf7ef] p-4 shadow-[0_12px_30px_rgba(57,49,37,.045)]">
      <summary className="cursor-pointer select-none text-sm font-semibold text-[#2b2925]">{label}</summary>
      <div className="mt-4 grid gap-4 md:grid-cols-3">
        {groups.map((group) => (
          <ResearchSectionCard key={group.title} {...group} />
        ))}
      </div>
    </details>
  );
}

function AgentDetailGroup({ title, items, tone = "default" }: { title: string; items: string[]; tone?: "default" | "risk" }) {
  const visibleItems = items.length > 0 ? items.slice(0, 3) : ["資料暫無"];

  return (
    <div className={`rounded-2xl border p-3 ${tone === "risk" ? "border-amber-300/10 bg-amber-300/[.035]" : "border-white/[.06] bg-white/[.025]"}`}>
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{title}</p>
      <ul className="mt-3 space-y-2 text-xs leading-5 text-slate-400">
        {visibleItems.map((item) => (
          <li key={item}>{normalizeDisplayText(item)}</li>
        ))}
      </ul>
    </div>
  );
}

function ResearchSummaryCard({ data }: { data: AnalyzeResponse }) {
  const report = normalizeResearchReport(data);
  const hasFinMindPublicMode = hasFinMindPublicModeNotice(data, report);

  return (
    <section className="overflow-hidden rounded-3xl border border-cyan-300/15 bg-cyan-300/[.045] shadow-glass">
      <div className="grid gap-0 lg:grid-cols-[1fr_280px]">
        <div className="p-6">
          <div className="flex items-center gap-2 text-cyan-100">
            <FileText className="h-5 w-5" />
            <h2 className="text-lg font-semibold text-white">綜合研究摘要</h2>
          </div>
          <p className="mt-4 text-sm leading-8 text-slate-200">{normalizeDisplayText(data.decision.recommendationText)}</p>
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
                    className={isSourceDegraded(source, hasFinMindPublicMode) ? "border-amber-300/20 bg-amber-300/10 text-amber-100" : "border-emerald-300/20 bg-emerald-300/10 text-emerald-100"}
                  >
                      {formatSourceLabel(source, hasFinMindPublicMode)}
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
  hasFinMindPublicMode,
}: {
  sources: AnalyzeResponse["sources"];
  hasDegradedAgent: boolean;
  hasFinMindPublicMode: boolean;
}) {
  const degradedSources = sources.filter((source) => isSourceDegraded(source, hasFinMindPublicMode));
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
                    {formatSourceLabel(source, hasFinMindPublicMode)}
                  </span>
                  <Badge className={isSourceDegraded(source, hasFinMindPublicMode) ? "border-amber-300/20 bg-amber-300/10 text-amber-100" : "border-emerald-300/20 bg-emerald-300/10 text-emerald-100"}>
                  {formatSourceStatus(source, hasFinMindPublicMode)}
                </Badge>
              </div>
              <p className="mt-2 text-xs leading-5 text-slate-500">{formatSourceMessage(source, hasFinMindPublicMode)}</p>
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
  isLegacyFallback,
}: {
  scoreBreakdown: Record<string, number>;
  finalScore: number | null;
  confidenceScore: number | null;
  isLegacyFallback: boolean;
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
          {isLegacyFallback ? (
            <p className="mt-2 text-xs leading-5 text-cyan-100/75">目前顯示舊版摘要模式；新版結構化評分欄位需搭配升級後端。</p>
          ) : null}
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-2xl border border-cyan-300/15 bg-cyan-300/[.06] px-4 py-3 text-right">
            <p className="text-xs text-cyan-100/70">總分</p>
            <p className="text-2xl font-semibold text-white">{formatResearchScore(finalScore)}</p>
          </div>
          <div className="rounded-2xl border border-cyan-300/15 bg-cyan-300/[.06] px-4 py-3 text-right">
            <p className="text-xs text-cyan-100/70">confidenceScore</p>
            <p className="text-2xl font-semibold text-white">
              {confidenceScore === null ? (isLegacyFallback ? "舊版資料來源未提供" : "資料暫無") : `${confidenceScore}/100`}
            </p>
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
              <span className="text-sm font-semibold text-cyan-100">{formatCategoryScore(item.score, item.max, isLegacyFallback)}</span>
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

async function analyzeStockWithRetry(symbol: string, allowAutoRetry: boolean) {
  try {
    return await analyzeStock(symbol);
  } catch (error) {
    if (!allowAutoRetry) throw error;
    await delay(RETRY_DELAY_MS);
    return analyzeStock(symbol);
  }
}

function delay(ms: number) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

function cacheKeyForSymbol(symbol: string) {
  return `stock-analysis-cache-${symbol}`;
}

function readCachedAnalysis(symbol: string) {
  try {
    const cached = window.localStorage.getItem(cacheKeyForSymbol(symbol));
    if (!cached) return null;
    return JSON.parse(cached) as AnalyzeResponse;
  } catch {
    return null;
  }
}

function writeCachedAnalysis(symbol: string, data: AnalyzeResponse) {
  try {
    window.localStorage.setItem(cacheKeyForSymbol(symbol), JSON.stringify(data));
  } catch {
    // Cache is a display fallback only; storage failures should not block analysis.
  }
}

function getAnalysisErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : "資料來源回應較慢，可能是後端冷啟動或外部資料暫時延遲。";
}

function normalizeResearchReport(data: AnalyzeResponse): ResearchReportView {
  const report = data.decision?.researchReport;
  const recommendationText = data.decision?.recommendationText || "舊版 API 未提供完整建議理由，請搭配現有分數、資料來源與風險項目保守判讀。";
  const fallbackGap = report
    ? "部分研究報告欄位未回傳，已使用可用資料保守呈現。"
    : "舊版 API 未提供 researchReport，已使用 recommendationText 與 scoreBreakdown 保守呈現。";

  return {
    isLegacyFallback: !report,
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

function formatConfidence(value: number | null, isLegacyFallback = false) {
  if (value === null) return isLegacyFallback ? "舊版資料來源未提供" : "資料暫無";
  return `${value}/100`;
}

function formatListSummary(items: string[]) {
  if (items.length === 0) return "資料暫無";
  return items.slice(0, 2).map(normalizeDisplayText).join("；");
}

function isSourceDegraded(source: AnalyzeResponse["sources"][number], hasFinMindPublicMode = false) {
  if (isFinMindPublicMode(source, hasFinMindPublicMode)) return true;
  const status = String(source.status ?? "").toLowerCase();
  return !(status === "ok" || status === "success" || status === "正常");
}

function hasFinMindPublicModeNotice(data: AnalyzeResponse, report: ResearchReportView) {
  const texts = [
    data.decision?.recommendationText,
    ...(report.dataGaps ?? []),
    ...(data.sources ?? []).map((source) => source.message),
  ];

  return texts.some((text) => {
    const value = String(text ?? "");
    return value.includes("未偵測到 FinMind API 權限") || value.includes("公開限制模式") || value.includes("FinMind 公開資料模式");
  });
}

function isFinMindPublicMode(source: AnalyzeResponse["sources"][number], hasFinMindPublicMode = false) {
  const name = String(source.name ?? "").toLowerCase();
  const message = String(source.message ?? "");
  return name.includes("finmind") && (hasFinMindPublicMode || message.includes("未偵測到 FinMind API 權限") || message.includes("公開限制模式") || message.includes("公開資料"));
}

function formatSourceLabel(source: AnalyzeResponse["sources"][number], hasFinMindPublicMode = false) {
  return isFinMindPublicMode(source, hasFinMindPublicMode) ? "FinMind 公開資料模式" : source.name;
}

function formatSourceStatus(source: AnalyzeResponse["sources"][number], hasFinMindPublicMode = false) {
  return isFinMindPublicMode(source, hasFinMindPublicMode) ? "公開資料模式" : source.status;
}

function formatSourceMessage(source: AnalyzeResponse["sources"][number], hasFinMindPublicMode = false) {
  if (isFinMindPublicMode(source, hasFinMindPublicMode)) {
    return "目前使用 FinMind 公開資料模式，部分欄位可能受限或延遲。";
  }
  return normalizeDisplayText(source.message);
}

function normalizeDisplayText(text: string) {
  return text
    .replaceAll("價格資料未顯示明確規則式風險", "目前未偵測到明確價格風險訊號")
    .replaceAll("財務資料未顯示明確規則式風險", "目前財務資料未顯示明確異常")
    .replaceAll("籌碼資料未顯示明確規則式風險", "目前籌碼資料未顯示明確壓力訊號")
    .replaceAll("未偵測到 FinMind API 權限，已嘗試公開限制模式；部分資料可能受限。", "目前使用 FinMind 公開資料模式，部分欄位可能受限或延遲。");
}

function previewText(text: string | undefined) {
  if (!text) return "系統已完成多 Agent 分析，請參考下方技術面、基本面、籌碼面與風險控管結果。";
  const normalizedText = normalizeDisplayText(text);
  return normalizedText.length > 112 ? `${normalizedText.slice(0, 112)}...` : normalizedText;
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

function formatCategoryScore(value: number | null, max: number, isLegacyFallback = false) {
  if (value === null) return isLegacyFallback ? "舊版未提供" : "資料暫無";
  return `${value.toFixed(1)}/${max}`;
}

function formatChipDataGaps(chipData: AnalyzeResponse["chipData"]) {
  if (!chipData) return ["官方籌碼與融資融券資料尚未隨分析回應提供。"];

  const gaps = [
    ...(chipData.dataGaps ?? []),
    ...(chipData.institutional?.dataGaps ?? []),
    ...(chipData.margin?.dataGaps ?? []),
  ];

  const uniqueMessages = Array.from(
    new Set(
      gaps
        .map((gap) => [gap.source, gap.code, gap.message].filter(Boolean).join("："))
        .filter((message) => message.trim().length > 0),
    ),
  );

  return uniqueMessages.length > 0 ? uniqueMessages : ["官方資料目前未回報缺口。"];
}

function formatOfficialText(value: string | null | undefined) {
  return value && value.trim().length > 0 ? value : "官方資料暫缺";
}

function formatOfficialDate(value: string | null | undefined) {
  return value && value.trim().length > 0 ? value : "日期未提供";
}

function formatChipStatus(value: "current" | "latest_available" | "partial" | "missing" | undefined) {
  if (value === "current") return "當日官方資料";
  if (value === "latest_available") return "最近可得官方資料";
  if (value === "partial") return "部分官方資料";
  return "官方資料缺失";
}

function formatOfficialInteger(value: number | null | undefined, unit = "") {
  if (typeof value !== "number" || !Number.isFinite(value)) return "官方資料暫缺";
  return `${value > 0 ? "+" : ""}${value.toLocaleString("zh-TW", { maximumFractionDigits: 0 })}${unit ? ` ${unit}` : ""}`;
}

function formatOfficialPercent(value: number | null | undefined) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "官方資料暫缺";
  return `${value.toLocaleString("zh-TW", { maximumFractionDigits: 2 })}%`;
}

function officialNumberTone(value: number | null | undefined): ResearchTabMetric["tone"] {
  if (typeof value !== "number" || !Number.isFinite(value) || value === 0) return "muted";
  return value > 0 ? "positive" : "negative";
}

function researchMetricClass(tone: ResearchTabMetric["tone"]) {
  if (tone === "positive") return "text-red-700";
  if (tone === "negative") return "text-emerald-700";
  if (tone === "muted") return "text-[#8a8175]";
  return "text-[#2b2925]";
}

function researchBadgeClass(tone: ResearchTabBadge["tone"]) {
  if (tone === "ok") return "border-emerald-200 bg-emerald-50 text-emerald-700";
  if (tone === "gap") return "border-amber-200 bg-amber-50 text-amber-700";
  return "border-[#e4dccf] bg-white text-[#746b60]";
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

function formatSourceNames(sources: AnalyzeResponse["sources"], hasFinMindPublicMode = false) {
  if (sources.length === 0) return "資料暫無";
  return sources.map((source) => formatSourceLabel(source, hasFinMindPublicMode)).join(" / ");
}
