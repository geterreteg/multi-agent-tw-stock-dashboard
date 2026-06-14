import { ArrowRight, BarChart3, Database, FileText, Lightbulb, Search, ShieldCheck, Target, TrendingUp } from "lucide-react";
import Link from "next/link";

import { SearchBox } from "@/components/search-box";

const quickStocks = [
  { symbol: "2330", name: "台積電" },
  { symbol: "2317", name: "鴻海" },
  { symbol: "2454", name: "聯發科" },
];

const featureCards = [
  {
    icon: FileText,
    title: "研究特色",
    detail: "多維度整合分析，涵蓋技術、基本面、籌碼、產業與風險。",
  },
  {
    icon: ShieldCheck,
    title: "可信度機制",
    detail: "來源可追溯，推理可驗證，結論可解釋，輔助每一份研究判斷。",
  },
  {
    icon: Database,
    title: "資料來源",
    detail: "串接權威數據與公開資訊，定期更新，確保研究品質與時效性。",
  },
];

const workflow = [
  { icon: Search, title: "問題解析 Agent", detail: "理解投資問題與目標，定義研究範圍與關鍵假設。" },
  { icon: Database, title: "資料蒐集 Agent", detail: "從市場、財報、籌碼等來源蒐集與整理資料。" },
  { icon: BarChart3, title: "分析推理 Agent", detail: "進行技術、基本面、籌碼與產業分析，形成初步結論。" },
  { icon: ShieldCheck, title: "風險評估 Agent", detail: "評估潛在風險與劇情，檢視假設與敏感度。" },
  { icon: Lightbulb, title: "投資洞察 Agent", detail: "整合觀點與信心評分，產出可行的投資建議。" },
];

const insights = [
  "營收動能穩健成長，先進製程需求滾動",
  "外資與投信同步加碼，籌碼結構偏多",
  "半導體景氣回溫，長期趨勢向上",
  "評價位於合理區間，風險報酬具吸引力",
];

export default function DashboardHome() {
  return (
    <div className="fixed inset-0 z-30 overflow-y-auto bg-[#f7f3ec] font-['Noto_Serif_TC','Songti_TC','PMingLiU',serif] text-[#2b2925]">
      <div className="min-h-screen bg-[radial-gradient(circle_at_50%_0%,#fffdf8_0%,#f7f3ec_45%,#f4efe7_100%)]">
        <header className="border-b border-[#e6ded3] bg-[#fffdf9]/88 backdrop-blur">
          <nav className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6 lg:px-10">
            <Link href="/" className="text-lg font-semibold tracking-[-0.01em] text-[#2b2925]">
              台股多 Agent 研究終端
            </Link>
            <div className="hidden items-center gap-10 text-sm text-[#5f5a51] md:flex">
              <a href="#overview" className="transition hover:text-[#2b2925]">
                首頁
              </a>
              <a href="#stock-search" className="transition hover:text-[#2b2925]">
                股票分析
              </a>
              <a href="#data" className="transition hover:text-[#2b2925]">
                資料來源
              </a>
            </div>
            <a
              href="#stock-search"
              className="rounded-lg bg-[#282521] px-5 py-2.5 text-sm font-medium text-white shadow-[0_10px_24px_rgba(43,39,33,.16)] transition hover:bg-[#3a352f]"
            >
              開始研究
            </a>
          </nav>
        </header>

        <main id="overview">
          <section className="mx-auto grid max-w-7xl gap-10 px-6 py-14 lg:grid-cols-[minmax(0,460px)_minmax(520px,610px)] lg:items-center lg:justify-between lg:px-10 lg:py-16">
            <div className="max-w-[460px]">
              <div className="inline-flex items-center gap-2 text-xs font-medium text-[#8a7e6b]">
                <span className="h-2 w-2 rounded-full bg-[#9b927f]" />
                專為台股投資者打造
              </div>
              <h1 className="mt-7 text-[34px] font-semibold leading-[1.22] text-[#282521] sm:text-[46px] lg:text-[48px]">
                <span className="block whitespace-nowrap">多 Agent 台股研究，</span>
                <span className="block whitespace-nowrap">快速又可追溯</span>
              </h1>
              <p className="mt-5 text-[15px] leading-8 text-[#6b6459]">
                整合技術面、基本面、籌碼與產業動態，由多個專業 Agent 並行分析，提供可驗證、可追溯的投資洞察，幫助你做出更有依據的投資決策。
              </p>

              <div id="stock-search" className="mt-8 scroll-mt-24">
                <SearchBox />
              </div>

              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className="text-xs text-[#8a8175]">快速查看</span>
                {quickStocks.map((stock) => (
                  <Link
                    key={stock.symbol}
                    href={`/stocks/${stock.symbol}`}
                    className="rounded-full border border-[#e1d8ca] bg-[#fffdf9] px-3 py-1.5 text-xs text-[#5d554b] shadow-sm transition hover:border-[#cbbfac] hover:text-[#282521]"
                  >
                    <span className="tabular-nums">{stock.symbol}</span> {stock.name}
                  </Link>
                ))}
              </div>
              <p className="mt-3 text-xs leading-6 text-[#8b8275]">支援個股與產業研究</p>
            </div>

            <ResearchPreviewCard />
          </section>

          <section id="data" className="border-y border-[#e8e1d7] bg-[#fffdf9]">
            <div className="mx-auto grid max-w-7xl gap-4 px-6 py-5 md:grid-cols-3 lg:px-10">
              {featureCards.map((card) => (
                <div key={card.title} className="rounded-xl border border-[#e8e1d7] bg-white px-6 py-5 shadow-[0_12px_28px_rgba(62,54,42,.045)]">
                  <div className="flex items-start gap-5">
                    <span className="grid h-14 w-14 shrink-0 place-items-center rounded-full bg-[#f2eee7] text-[#2f302b]">
                      <card.icon className="h-6 w-6" />
                    </span>
                    <div>
                      <h2 className="text-lg font-semibold tracking-[-0.01em] text-[#2b2925]">{card.title}</h2>
                      <p className="mt-2 text-sm leading-6 text-[#726a5f]">{card.detail}</p>
                      <a href="#stock-search" className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-[#2b2925]">
                        了解更多 <ArrowRight className="h-3.5 w-3.5" />
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section id="workflow" className="border-b border-[#e8e1d7] bg-[#fffdf9]">
            <div className="mx-auto max-w-7xl px-6 py-8 lg:px-10">
              <div className="text-center">
                <h2 className="text-2xl font-semibold tracking-[-0.01em] text-[#2b2925]">多 Agent 協作流程</h2>
                <p className="mt-2 text-sm text-[#7c7469]">五大專業 Agent 並行協作，從問題定義到投資洞察，一氣呵成。</p>
              </div>
              <div className="relative mt-8 grid gap-5 lg:grid-cols-5">
                <div className="pointer-events-none absolute left-[5%] right-[5%] top-4 hidden h-px bg-[#ded5c8] lg:block" />
                {workflow.map((agent, index) => (
                  <div key={agent.title} className="relative text-center lg:text-left">
                    <span className="mx-auto grid h-8 w-8 place-items-center rounded-full bg-[#ebe5dc] text-sm font-semibold text-[#756d62] lg:mx-0">
                      {index + 1}
                    </span>
                    <div className="mt-5 flex flex-col items-center gap-3 lg:items-start">
                      <span className="grid h-16 w-16 place-items-center rounded-full bg-[#f1ede6] text-[#2b2925]">
                        <agent.icon className="h-7 w-7" />
                      </span>
                      <div>
                        <h3 className="text-base font-semibold text-[#2b2925]">{agent.title}</h3>
                        <p className="mt-2 text-sm leading-6 text-[#756d62]">{agent.detail}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

function ResearchPreviewCard() {
  return (
    <aside className="rounded-2xl border border-[#ded6cb] bg-white p-6 shadow-[0_22px_70px_rgba(58,50,40,.12)]">
      <div className="grid gap-6 sm:grid-cols-[1fr_170px] sm:items-start">
        <div>
          <h2 className="text-3xl font-semibold tracking-[-0.03em] text-[#2b2925]">2330 台積電</h2>
          <p className="mt-2 text-sm text-[#80786d]">TSMC・半導體</p>
        </div>
        <div className="sm:text-right">
          <p className="text-xs text-[#8a8175]">綜合信心分數</p>
          <div className="mt-2 flex items-end gap-2 sm:justify-end">
            <span className="text-3xl font-semibold text-[#426553]">82</span>
            <span className="pb-1 text-sm text-[#6f665b]">/ 100</span>
            <span className="mb-1 rounded-md bg-[#e6f0e7] px-3 py-1 text-xs text-[#3d6b51]">偏多</span>
          </div>
          <p className="mt-2 text-xs text-[#9a9185]">圖片僅供參考</p>
        </div>
      </div>

      <div className="mt-7 rounded-xl border border-[#e7dfd5] bg-[#fffdf9] p-4">
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_260px]">
          <div>
            <div className="mb-3 flex items-center justify-between">
              <p className="text-sm font-semibold text-[#2b2925]">股價走勢</p>
              <div className="flex gap-1 text-xs text-[#8b8275]">
                {["1M", "3M", "6M", "1Y", "3Y"].map((range) => (
                  <span key={range} className={`rounded-md px-2 py-1 ${range === "3M" ? "bg-[#efebe4] text-[#2b2925]" : ""}`}>
                    {range}
                  </span>
                ))}
              </div>
            </div>
            <MiniTrendLine />
          </div>
          <div>
            <p className="mb-3 text-sm font-semibold text-[#2b2925]">重點洞察</p>
            <div className="space-y-3">
              {insights.map((item, index) => (
                <div key={item} className="flex items-center gap-3 rounded-lg bg-[#f7f3ef] px-3 py-3 text-sm text-[#5f574d]">
                  <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-[#e7efe4] text-[#426553]">
                    {index === 0 ? <TrendingUp className="h-4 w-4" /> : index === 3 ? <Target className="h-4 w-4" /> : <ShieldCheck className="h-4 w-4" />}
                  </span>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      <p className="mt-4 text-xs text-[#8b8275]">本分析由多 Agent 協作產生，僅供參考，非投資建議。請詳閱免責聲明。</p>
    </aside>
  );
}

function MiniTrendLine() {
  return (
    <svg className="h-48 w-full" viewBox="0 0 330 184" role="img" aria-label="簡化股價走勢圖">
      {[28, 66, 104, 142].map((y) => (
        <line key={y} x1="0" x2="330" y1={y} y2={y} stroke="#ece6dd" />
      ))}
      <path
        d="M4 138 C18 132 26 116 40 120 C54 124 62 102 76 108 C90 114 98 88 114 96 C130 104 138 78 154 86 C170 94 180 106 194 98 C210 88 216 132 232 124 C248 116 256 74 272 82 C288 90 296 54 312 60 C320 62 324 48 328 50"
        fill="none"
        stroke="#496958"
        strokeWidth="2.2"
      />
      <text x="4" y="178" fill="#9a9185" fontSize="11">
        02/22
      </text>
      <text x="112" y="178" fill="#9a9185" fontSize="11">
        03/22
      </text>
      <text x="222" y="178" fill="#9a9185" fontSize="11">
        05/22
      </text>
    </svg>
  );
}
