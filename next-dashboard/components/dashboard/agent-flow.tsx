import { BarChart3, Database, LineChart, ShieldAlert, Workflow } from "lucide-react";

const agents = [
  { icon: Database, title: "資料蒐集 Agent", body: "整合價格、籌碼與基本面資料狀態。" },
  { icon: LineChart, title: "技術分析 Agent", body: "判讀股價、均線、成交量與短期趨勢。" },
  { icon: BarChart3, title: "基本面 Agent", body: "評估營收、EPS、評價與獲利支撐。" },
  { icon: ShieldAlert, title: "風險控管 Agent", body: "提出反方觀點、資料限制與壓力情境。" },
  { icon: Workflow, title: "決策整合 Agent", body: "整合觀點並輸出可解釋的研究摘要。" },
];

export function AgentFlow() {
  return (
    <section className="rounded-3xl border border-white/[.08] bg-slate-950/35 p-5 shadow-glass">
      <div className="mb-5 flex items-end justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-white">多 Agent 工作流程</h2>
          <p className="mt-2 text-sm text-slate-400">每個模組各自負責一種投資研究視角，最後形成可解釋摘要。</p>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-5">
        {agents.map((agent, index) => (
          <div
            key={agent.title}
            className="relative rounded-2xl border border-white/[.08] bg-white/[.045] p-4"
          >
            <div className="mb-4 flex items-center justify-between">
              <div className="rounded-xl bg-cyan-300/10 p-2 text-cyan-200">
                <agent.icon className="h-5 w-5" />
              </div>
              <span className="text-xs font-semibold text-slate-500">0{index + 1}</span>
            </div>
            <h3 className="text-sm font-semibold text-white">{agent.title}</h3>
            <p className="mt-3 text-sm leading-6 text-slate-400">{agent.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
