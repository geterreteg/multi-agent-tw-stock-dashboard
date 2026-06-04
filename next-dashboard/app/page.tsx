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
              整合價格、籌碼、基本面與多代理人觀點，快速產生可解釋的投資分析摘要。
            </p>
            <div className="mt-8">
              <SearchBox />
            </div>
            <div className="mt-5 flex flex-wrap gap-3">
              {demos.map((demo) => (
                <Link
                  key={demo.symbol}
                  href={`/stocks/${demo.symbol}`}
                  className={cn(buttonVariants({ variant: "secondary", size: "sm" }))}
                >
                  {demo.symbol} {demo.name}
                </Link>
              ))}
            </div>
          </div>
          <div className="rounded-[1.75rem] border border-cyan-300/15 bg-slate-950/50 p-5">
            <div className="mb-4 flex items-center justify-between">
              <Badge>產品預覽</Badge>
              <span className="text-xs text-slate-500">示範資料</span>
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
        <StatusCard icon={Activity} label="API 狀態" value="正常" detail="FastAPI 示範後端可供前端串接。" />
        <StatusCard icon={Database} label="資料來源" value="示範資料" detail="下一階段接回 yfinance 與 FinMind。" />
        <StatusCard icon={Clock3} label="最後更新時間" value="2026/06/04 18:00" detail="示範資料時間戳。" />
        <StatusCard icon={Boxes} label="分析模組狀態" value="5 / 5 正常" detail="多 Agent 卡片與決策摘要已就緒。" />
      </section>

      <AgentFlow />

      <section className="rounded-3xl border border-white/[.08] bg-white/[.04] p-6">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h2 className="text-xl font-semibold text-white">準備進入新版分析頁</h2>
            <p className="mt-2 text-sm text-slate-400">先用示範資料驗證作品集等級 UI，下一階段再接回真實 Python 分析邏輯。</p>
          </div>
          <Link href="/stocks/2330" className={cn(buttonVariants(), "flex items-center gap-2")}>
            查看 2330 分析
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
