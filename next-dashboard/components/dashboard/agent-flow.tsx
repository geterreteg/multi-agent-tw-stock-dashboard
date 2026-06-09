const agents = [
  { title: "資料蒐集 Agent", body: "整合價格、籌碼與基本面資料狀態。" },
  { title: "技術分析 Agent", body: "判讀股價、均線、成交量與短期趨勢。" },
  { title: "基本面 Agent", body: "評估營收、EPS、評價與獲利支撐。" },
  { title: "風險控管 Agent", body: "提出反方觀點、資料限制與壓力情境。" },
  { title: "決策整合 Agent", body: "整合觀點並輸出可解釋的研究摘要。" },
];

export function AgentFlow() {
  return (
    <section className="border-y border-white/[.08] py-8">
      <div className="grid gap-8 lg:grid-cols-[280px_minmax(0,1fr)] lg:items-start">
        <div className="lg:sticky lg:top-8">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[rgba(199,183,143,.72)]">
            research protocol
          </p>
          <h2 className="mt-4 text-2xl font-semibold tracking-tight text-[rgb(244,241,232)]">多 Agent 工作流程</h2>
          <p className="mt-3 text-sm leading-7 text-slate-400">
            每個模組只處理一種研究視角，最後再整合成可解釋摘要。
          </p>
        </div>
        <ol className="divide-y divide-white/[.08] border-l border-[rgba(199,183,143,.28)]">
          {agents.map((agent, index) => (
            <li key={agent.title} className="grid gap-3 py-5 pl-5 sm:grid-cols-[72px_minmax(0,1fr)] sm:gap-6">
              <span className="font-mono text-sm font-semibold tabular-nums tracking-[0.18em] text-[rgb(229,218,190)]">
                0{index + 1}
              </span>
              <div>
                <h3 className="text-base font-semibold text-white">{agent.title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-400">{agent.body}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
