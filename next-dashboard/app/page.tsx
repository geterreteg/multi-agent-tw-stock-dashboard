import { Activity, Boxes, Clock3, Database, ShieldCheck } from "lucide-react";
import Link from "next/link";

import { AgentFlow } from "@/components/dashboard/agent-flow";
import { StatusCard } from "@/components/dashboard/status-card";
import { SearchBox } from "@/components/search-box";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const demos = [
  { symbol: "2330", name: "台積電" },
  { symbol: "2317", name: "鴻海" },
  { symbol: "2454", name: "聯發科" },
];

export default function DashboardHome() {
  return (
    <div className="space-y-10">
      <section className="terminal-hero relative isolate overflow-hidden border border-white/[.08] bg-[rgba(7,10,12,.58)] px-5 py-6 shadow-[0_34px_140px_rgba(0,0,0,.36)] sm:px-8 sm:py-10 lg:min-h-[calc(100vh-3rem)] lg:px-10 lg:py-12">
        <div className="absolute inset-0 -z-20 bg-[linear-gradient(90deg,rgba(217,204,166,.022)_1px,transparent_1px),linear-gradient(rgba(217,204,166,.018)_1px,transparent_1px)] bg-[size:96px_96px]" />
        <div className="absolute left-[-18%] top-[-18%] -z-10 h-[36rem] w-[36rem] rounded-full bg-[rgba(199,183,143,.16)] blur-3xl" />
        <div className="absolute right-[-12%] top-10 -z-10 h-[32rem] w-[32rem] rounded-full bg-[rgba(90,148,141,.16)] blur-3xl" />
        <div className="absolute bottom-0 left-0 right-0 -z-10 h-40 bg-gradient-to-t from-[rgba(5,7,8,.92)] to-transparent" />
        <div className="mb-10 flex flex-wrap items-center justify-between gap-4 border-b border-white/[.08] pb-5">
          <div className="flex items-center gap-3">
            <span className="h-2 w-2 bg-[rgb(181,221,214)] shadow-[0_0_18px_rgba(181,221,214,.55)]" />
            <span className="font-mono text-xs uppercase tracking-[0.24em] text-[rgba(229,218,190,.72)]">
              TW Equity Research Terminal
            </span>
          </div>
          <span className="border border-[rgba(199,183,143,.22)] bg-[rgba(199,183,143,.06)] px-3 py-1 font-mono text-[11px] uppercase tracking-[0.18em] text-[rgba(229,218,190,.76)]">
            Rule-based multi-agent model
          </span>
        </div>
        <div className="grid gap-10 lg:grid-cols-[minmax(0,1.08fr)_minmax(360px,.92fr)] lg:items-end">
          <div className="max-w-5xl">
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-stone-300">
              Taiwan equity research cockpit
            </p>
            <h1 className="mt-6 max-w-4xl text-balance text-4xl font-semibold leading-[1.04] tracking-tight text-[rgb(244,241,232)] sm:text-5xl lg:text-[4.35rem]">
              台股多 Agent 研究終端
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-8 text-slate-300">
              將價格、基本面、籌碼、風險與反方觀點拆解成可追溯的研究流程，輸出帶有評級、信心分數與資料缺口的規則式分析摘要。
            </p>
            <div id="stock-search" className="mt-10 scroll-mt-24">
              <SearchBox />
            </div>
            <p className="mt-4 max-w-2xl border-l border-[rgba(199,183,143,.34)] pl-4 text-xs leading-6 text-slate-400">
              資料可能延遲或不完整；本系統分析結果僅供學術研究與投資參考，不構成任何買賣建議。
            </p>
            <div className="mt-7">
              <p className="text-xs font-medium tracking-[0.18em] text-stone-300">範例標的</p>
              <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-sm">
                {demos.map((demo) => (
                  <Link
                    key={demo.symbol}
                    href={`/stocks/${demo.symbol}`}
                    className="group inline-flex items-baseline gap-2 border-b border-white/10 pb-1 text-slate-400 transition hover:border-[rgba(199,183,143,.55)] hover:text-[rgb(229,218,190)]"
                  >
                    <span className="font-mono text-xs tabular-nums tracking-[0.18em]">{demo.symbol}</span>
                    <span>{demo.name}</span>
                  </Link>
                ))}
              </div>
            </div>
          </div>
          <aside className="relative overflow-hidden border border-[rgba(199,183,143,.18)] bg-[rgba(12,17,19,.92)] p-5 shadow-[0_30px_120px_rgba(0,0,0,.32)] sm:p-6">
            <div className="absolute right-[-20%] top-[-22%] h-72 w-72 rounded-full bg-[rgba(94,137,132,.12)] blur-3xl" />
            <div className="relative flex items-start justify-between gap-6 border-b border-[rgba(199,183,143,.16)] pb-5">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-stone-300">Research desk</p>
                <h2 className="mt-3 text-2xl font-semibold tracking-tight text-[rgb(244,241,232)]">多 Agent 研究桌</h2>
              </div>
              <span className="border border-[rgba(199,183,143,.35)] bg-[rgba(199,183,143,.1)] px-3 py-1 text-xs text-[rgb(238,229,203)]">
                preview
              </span>
            </div>
            <div className="relative mt-6 grid gap-3 sm:grid-cols-3">
              <PreviewMetric label="Rating" value="Buy" tone="positive" />
              <PreviewMetric label="Confidence" value="72/100" />
              <PreviewMetric label="Data gaps" value="2" tone="warning" />
            </div>
            <div className="relative mt-6 border border-[rgba(199,183,143,.16)] bg-[rgba(5,8,10,.34)] p-4">
              <div className="flex items-center justify-between gap-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-300">Agent consensus</p>
                <span className="text-xs text-[rgb(184,218,213)]">4 modules</span>
              </div>
              <div className="mt-4 grid gap-2">
                <ConsensusRow label="Price" value="偏多" strength="72%" />
                <ConsensusRow label="Fundamental" value="中性" strength="58%" />
                <ConsensusRow label="Chip" value="觀察" strength="51%" />
                <ConsensusRow label="Risk" value="保守" strength="46%" />
              </div>
            </div>
            <div className="relative mt-5 border border-[rgba(232,190,128,.18)] bg-[rgba(232,190,128,.055)] p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-300">Risk flags</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {["資料缺口", "短線波動", "估值敏感"].map((item) => (
                  <span key={item} className="border border-[rgba(232,190,128,.24)] bg-[rgba(232,190,128,.08)] px-3 py-1.5 text-xs text-[rgb(239,210,161)]">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </aside>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatusCard icon={Activity} label="API 狀態" value="已連線" detail="前端透過 FastAPI 取得分析結果。" />
        <StatusCard icon={Database} label="資料來源" value="雙來源整合" detail="價格資料、基本面與籌碼資料統一進入分析流程。" />
        <StatusCard icon={Clock3} label="資料時效" value="依來源更新" detail="資料可能延遲或不完整，不宣稱完全即時。" />
        <StatusCard icon={Boxes} label="分析模組" value="多 Agent 評分" detail="技術面、基本面、籌碼面與風險控管共同形成結論。" />
      </section>

      <AgentFlow />

      <section className="rounded-3xl border border-white/[.08] bg-white/[.04] p-6">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h2 className="text-xl font-semibold text-white">產出可解釋的台股研究摘要</h2>
            <p className="mt-2 text-sm text-slate-400">
              系統以規則式多 Agent 彙整資料與風險觀點，分析結果僅供課程研究與投資參考，不構成任何買賣建議。
            </p>
          </div>
          <Link href="/#stock-search" className={cn(buttonVariants(), "flex items-center gap-2")}>
            輸入股票代號
            <ShieldCheck className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </div>
  );
}

function PreviewMetric({ label, value, tone = "default" }: { label: string; value: string; tone?: "default" | "positive" | "warning" }) {
  const valueClass =
    tone === "positive" ? "text-[rgb(184,218,213)]" : tone === "warning" ? "text-[rgb(239,210,161)]" : "text-[rgb(244,241,232)]";

  return (
    <div className="border border-[rgba(199,183,143,.16)] bg-[rgba(244,241,232,.055)] p-4">
      <p className="text-[11px] uppercase tracking-[0.16em] text-stone-300">{label}</p>
      <p className={`mt-2 font-mono text-xl font-semibold tabular-nums ${valueClass}`}>{value}</p>
    </div>
  );
}

function ConsensusRow({ label, value, strength }: { label: string; value: string; strength: string }) {
  return (
    <div className="grid grid-cols-[110px_1fr_48px] items-center gap-3 text-sm">
      <span className="font-mono text-xs uppercase tracking-[0.16em] text-slate-300">{label}</span>
      <span className="text-[rgb(244,241,232)]">{value}</span>
      <span className="text-right font-mono text-xs text-[rgb(184,218,213)]">{strength}</span>
    </div>
  );
}
