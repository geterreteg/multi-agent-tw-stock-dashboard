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
      <section className="relative isolate overflow-hidden border-b border-white/[.08] pb-12 pt-8 sm:pb-16 lg:min-h-[calc(100vh-3rem)] lg:pb-20 lg:pt-12">
        <div className="absolute inset-x-[-6%] top-12 -z-10 h-px bg-gradient-to-r from-transparent via-[rgba(217,204,166,.34)] to-transparent" />
        <div className="absolute left-[-16%] top-[-18%] -z-10 h-[30rem] w-[30rem] rounded-full bg-[rgba(217,204,166,.16)] blur-3xl" />
        <div className="absolute right-[-12%] top-12 -z-10 h-[28rem] w-[28rem] rounded-full bg-[rgba(104,176,169,.16)] blur-3xl" />
        <div className="absolute bottom-[-20%] right-[18%] -z-10 h-72 w-72 rounded-full bg-[rgba(244,241,232,.08)] blur-3xl" />
        <div className="absolute inset-0 -z-20 bg-[linear-gradient(90deg,rgba(217,204,166,.035)_1px,transparent_1px),linear-gradient(rgba(217,204,166,.028)_1px,transparent_1px)] bg-[size:84px_84px] opacity-80" />
        <div className="grid gap-12 lg:grid-cols-[minmax(0,1.12fr)_minmax(340px,.88fr)] lg:items-end">
          <div className="max-w-5xl">
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[rgba(199,183,143,.78)]">
              Taiwan equity research workflow
            </p>
            <h1 className="mt-7 max-w-4xl text-balance text-4xl font-semibold leading-[1.08] tracking-tight text-[rgb(244,241,232)] sm:text-5xl lg:text-6xl">
              把台股分析，拆成可解釋的研究流程
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-8 text-slate-300">
              輸入台股代號，系統會整合價格、基本面、籌碼與風險觀點，整理成一份可追溯的多 Agent 研究摘要。
            </p>
            <div id="stock-search" className="mt-10 scroll-mt-24">
              <SearchBox />
            </div>
            <p className="mt-4 max-w-2xl border-l border-[rgba(199,183,143,.34)] pl-4 text-xs leading-6 text-slate-500">
              資料可能延遲或不完整；本系統分析結果僅供學術研究與投資參考，不構成任何買賣建議。
            </p>
            <div className="mt-7">
              <p className="text-xs font-medium tracking-[0.18em] text-slate-500">範例標的</p>
              <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-sm">
                {demos.map((demo) => (
                  <Link
                    key={demo.symbol}
                    href={`/stocks/${demo.symbol}`}
                    className="group inline-flex items-baseline gap-2 border-b border-white/10 pb-1 text-slate-500 transition hover:border-[rgba(199,183,143,.55)] hover:text-[rgb(229,218,190)]"
                  >
                    <span className="font-mono text-xs tabular-nums tracking-[0.18em]">{demo.symbol}</span>
                    <span>{demo.name}</span>
                  </Link>
                ))}
              </div>
            </div>
          </div>
          <aside className="relative min-h-[430px] overflow-hidden border border-white/[.08] bg-[rgba(9,13,16,.52)] p-5 shadow-[0_30px_120px_rgba(0,0,0,.28)] backdrop-blur-md sm:p-6">
            <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(217,204,166,.045)_1px,transparent_1px),linear-gradient(rgba(217,204,166,.038)_1px,transparent_1px)] bg-[size:48px_48px]" />
            <div className="absolute right-[-18%] top-[-14%] h-64 w-64 rounded-full bg-[rgba(132,190,184,.16)] blur-3xl" />
            <div className="absolute left-6 top-20 h-52 w-[72%] rotate-[-3deg] border border-[rgba(217,204,166,.22)] bg-[rgba(248,244,232,.08)]" />
            <div className="absolute bottom-12 right-5 h-48 w-[74%] rotate-[2deg] border border-white/[.08] bg-[rgba(248,244,232,.045)]" />
            <div className="relative flex items-start justify-between gap-6 border-b border-white/[.08] pb-5">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Research note</p>
                <h2 className="mt-3 text-2xl font-semibold tracking-tight text-[rgb(244,241,232)]">市場觀察票據</h2>
              </div>
              <span className="border border-[rgba(199,183,143,.35)] bg-[rgba(199,183,143,.08)] px-3 py-1 text-xs text-[rgb(229,218,190)]">
                demo
              </span>
            </div>
            <div className="relative mt-5 grid grid-cols-3 gap-2 text-xs">
              <span className="border border-white/[.08] bg-white/[.035] px-3 py-2 text-slate-400">Price</span>
              <span className="border border-[rgba(132,190,184,.2)] bg-[rgba(132,190,184,.06)] px-3 py-2 text-[rgb(184,218,213)]">Quality</span>
              <span className="border border-[rgba(199,183,143,.22)] bg-[rgba(199,183,143,.06)] px-3 py-2 text-[rgb(229,218,190)]">Risk</span>
            </div>
            <div className="relative my-7 h-24 border-y border-white/[.07]">
              <div className="absolute left-0 top-1/2 h-px w-full bg-[rgba(217,204,166,.12)]" />
              <div className="absolute bottom-5 left-[8%] h-8 w-px bg-[rgba(132,190,184,.45)]" />
              <div className="absolute bottom-5 left-[24%] h-12 w-px bg-[rgba(132,190,184,.28)]" />
              <div className="absolute bottom-5 left-[44%] h-16 w-px bg-[rgba(217,204,166,.34)]" />
              <div className="absolute bottom-5 left-[63%] h-10 w-px bg-[rgba(132,190,184,.34)]" />
              <div className="absolute bottom-5 left-[82%] h-14 w-px bg-[rgba(217,204,166,.24)]" />
              <div className="absolute left-[8%] top-9 h-px w-[74%] bg-gradient-to-r from-[rgba(132,190,184,.12)] via-[rgba(132,190,184,.52)] to-[rgba(217,204,166,.22)]" />
            </div>
            <div className="relative divide-y divide-white/[.07]">
              <PreviewRow label="台積電" value="Neutral / 中性" delta="+4.2%" />
              <PreviewRow label="鴻海" value="觀察" delta="+1.8%" />
              <PreviewRow label="聯發科" value="Buy / 看多" delta="+6.1%" />
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

function PreviewRow({ label, value, delta }: { label: string; value: string; delta: string }) {
  return (
    <div className="flex items-center justify-between gap-4 py-4">
      <div>
        <p className="font-medium text-[rgb(18,24,25)]">{label}</p>
        <p className="mt-1 text-xs text-[rgba(31,42,43,.48)]">多 Agent 評級：{value}</p>
      </div>
      <span className="font-mono text-sm font-semibold tabular-nums text-[rgb(28,101,91)]">{delta}</span>
    </div>
  );
}
