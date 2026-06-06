import Link from "next/link";
import { Activity, Boxes, Clock3, Database, ShieldCheck } from "lucide-react";

import { AgentFlow } from "@/components/dashboard/agent-flow";
import { StatusCard } from "@/components/dashboard/status-card";
import { SearchBox } from "@/components/search-box";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const demos = [
  { symbol: "2330", name: "台積電" },
  { symbol: "2317", name: "鴻海" },
  { symbol: "2454", name: "聯發科" },
];

export default function DashboardHome() {
  return (
    <div className="space-y-8">
      <section className="relative overflow-hidden rounded-[2rem] border border-white/[.09] bg-white/[.045] p-8 shadow-glass backdrop-blur-xl lg:p-12">
        <div className="absolute right-0 top-0 h-72 w-72 rounded-full bg-cyan-300/10 blur-3xl" />
        <div className="relative grid gap-10 lg:grid-cols-[1.05fr_.95fr] lg:items-center">
          <div>
            <h1 className="max-w-4xl text-4xl font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl">
              多 Agent 台股智慧分析儀表板
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-8 text-slate-300">
              串接 FastAPI 分析後端，整合價格、基本面、籌碼與多 Agent 評分，快速產生可解釋的台股研究摘要。
            </p>
            <div id="stock-search" className="mt-8 scroll-mt-24">
              <SearchBox />
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-500">
              輸入台股代號，系統將整合價格、基本面、籌碼與多 Agent 評分產生研究摘要。
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              {demos.map((demo) => (
                <Link
                  key={demo.symbol}
                  href={`/stocks/${demo.symbol}`}
                  className={cn(
                    buttonVariants({ variant: "secondary", size: "sm" }),
                    "border-white/[.08] bg-white/[.035] text-slate-300 hover:bg-white/[.075] hover:text-white"
                  )}
                >
                  範例分析：{demo.symbol} {demo.name}
                </Link>
              ))}
            </div>
          </div>
          <div className="rounded-[1.75rem] border border-cyan-300/15 bg-slate-950/50 p-5">
            <div className="mb-4 flex items-center justify-between">
              <Badge>分析快照</Badge>
              <span className="text-xs text-slate-500">課程研究用途</span>
            </div>
            <div className="space-y-4">
              <PreviewRow label="台積電" value="中立" delta="+4.2%" />
              <PreviewRow label="鴻海" value="觀察" delta="+1.8%" />
              <PreviewRow label="聯發科" value="偏多" delta="+6.1%" />
            </div>
          </div>
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
    <div className="flex items-center justify-between rounded-2xl border border-white/[.08] bg-white/[.04] p-4">
      <div>
        <p className="font-medium text-white">{label}</p>
        <p className="mt-1 text-sm text-slate-500">多 Agent 評級：{value}</p>
      </div>
      <span className="text-sm font-semibold text-emerald-200">{delta}</span>
    </div>
  );
}
