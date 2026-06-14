import type { Metadata } from "next";
import Link from "next/link";
import { BarChart3, Database, Home } from "lucide-react";

import { MobileTopBar } from "@/components/mobile-top-bar";

import "./globals.css";

export const metadata: Metadata = {
  title: "多 Agent 台股智慧分析儀表板",
  description: "整合價格、基本面、籌碼與多 Agent 評分的台股研究分析儀表板。",
};

const nav = [
  { href: "/", label: "首頁總覽", icon: Home },
  { href: "/#stock-search", label: "股票分析", icon: BarChart3 },
  { href: "/#data", label: "資料來源", icon: Database },
];

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-Hant" className="dark">
      <body>
        <MobileTopBar />
        <div className="relative flex min-h-screen w-full">
          <aside className="sticky top-0 hidden h-screen w-72 shrink-0 border-r border-[#e7dfd3] bg-[#fbf8f2] p-6 text-[#2b2925] lg:block">
            <Link href="/" className="flex items-center gap-3">
              <div className="rounded-lg border border-[#ded5c8] bg-white p-3 text-[#2f6b4f] shadow-sm">
                <BarChart3 className="h-6 w-6" />
              </div>
              <div>
                <p className="font-semibold text-[#2b2925]">台股多 Agent 研究終端</p>
                <p className="text-xs text-[#7d7469]">Multi-Agent Research</p>
              </div>
            </Link>
            <nav className="mt-10 space-y-2">
              {nav.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-3 rounded-lg border border-transparent px-4 py-3 text-sm font-semibold text-[#514b43] transition hover:border-[#e3dbcf] hover:bg-[#f1ece4] hover:text-[#2b2925]"
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </Link>
              ))}
            </nav>
            <div className="absolute bottom-6 left-6 right-6 overflow-hidden rounded-xl border border-[#e3dbcf] bg-[#fffdf9] p-4 shadow-[0_14px_34px_rgba(57,49,37,.06)]">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#2f6b4f]">System Status</p>
              <p className="mt-2 text-sm leading-6 text-[#6f665b]">已連線 FastAPI 分析模組，投資組合與策略研習中。</p>
              <svg
                className="mt-5 h-[118px] w-full"
                viewBox="0 0 212 118"
                role="img"
                aria-label="財金成長狀態插圖"
              >
                <defs>
                  <linearGradient id="statusGold" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#e9c47a" />
                    <stop offset="100%" stopColor="#c79038" />
                  </linearGradient>
                  <linearGradient id="statusBase" x1="0" x2="1" y1="0" y2="1">
                    <stop offset="0%" stopColor="#f8efe0" />
                    <stop offset="100%" stopColor="#ead8bd" />
                  </linearGradient>
                  <radialGradient id="statusCoin" cx="42%" cy="38%" r="62%">
                    <stop offset="0%" stopColor="#fff8ea" />
                    <stop offset="58%" stopColor="#e7bf70" />
                    <stop offset="100%" stopColor="#b9812e" />
                  </radialGradient>
                  <filter id="statusShadow" x="-20%" y="-20%" width="140%" height="150%">
                    <feDropShadow dx="0" dy="8" stdDeviation="6" floodColor="#8a5d21" floodOpacity=".16" />
                  </filter>
                </defs>
                <path d="M15 102 C52 91 151 90 197 101 L185 111 L28 112 Z" fill="url(#statusBase)" />
                <ellipse cx="104" cy="101" rx="86" ry="10" fill="#c99a50" opacity=".16" />
                <g filter="url(#statusShadow)">
                  <circle cx="43" cy="76" r="20" fill="url(#statusCoin)" />
                  <circle cx="43" cy="76" r="13" fill="none" stroke="#fff2cf" strokeWidth="1.4" opacity=".8" />
                  <path d="M39 66 h8 M39 72 h8 M43 66 v21" stroke="#9b6c27" strokeWidth="1.2" strokeLinecap="round" opacity=".72" />
                </g>
                <g filter="url(#statusShadow)">
                  <rect x="83" y="73" width="24" height="28" rx="3" fill="url(#statusGold)" />
                  <rect x="116" y="61" width="27" height="40" rx="3" fill="url(#statusGold)" />
                  <rect x="153" y="42" width="29" height="59" rx="3" fill="url(#statusGold)" />
                  <path d="M78 100 H188" stroke="#a9742c" strokeWidth="1.2" opacity=".35" />
                  <path d="M61 96 C85 85 104 77 125 64 C147 51 162 44 190 27" fill="none" stroke="#b47a28" strokeWidth="2.4" strokeLinecap="round" />
                  <path d="M181 27 H190 V36" fill="none" stroke="#b47a28" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
                  <circle cx="83" cy="87" r="4" fill="#fff4d7" stroke="#bf8431" />
                  <circle cx="124" cy="65" r="4" fill="#fff4d7" stroke="#bf8431" />
                </g>
                <g opacity=".62">
                  <circle cx="68" cy="87" r="7" fill="#f1d291" />
                  <path d="M65 86 h6 M65 90 h6" stroke="#ad7629" strokeWidth="1" />
                  <circle cx="195" cy="81" r="5" fill="#f1d291" />
                </g>
              </svg>
            </div>
          </aside>
          <main className="min-w-0 flex-1 bg-[#fbf8f2] px-5 py-6 sm:px-8 lg:px-10">{children}</main>
        </div>
      </body>
    </html>
  );
}
