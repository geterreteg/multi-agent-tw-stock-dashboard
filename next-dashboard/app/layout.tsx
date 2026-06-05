import type { Metadata } from "next";
import Link from "next/link";
import { BarChart3, FlaskConical, Home, Settings, Sparkles } from "lucide-react";

import { MobileTopBar } from "@/components/mobile-top-bar";

import "./globals.css";

export const metadata: Metadata = {
  title: "多 Agent 台股智慧分析儀表板",
  description: "Next.js + FastAPI 新版金融科技儀表板。",
};

const nav = [
  { href: "/", label: "首頁總覽", icon: Home },
  { href: "/stocks/2330", label: "股票分析", icon: BarChart3 },
  { href: "/backtest", label: "回測結果", icon: FlaskConical },
  { href: "/events", label: "事件研究", icon: Sparkles },
  { href: "/settings", label: "設定", icon: Settings },
];

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-Hant" className="dark">
      <body>
        <MobileTopBar />
        <div className="relative mx-auto flex min-h-screen max-w-[1500px]">
          <aside className="sticky top-0 hidden h-screen w-72 shrink-0 border-r border-white/[.08] bg-slate-950/35 p-6 backdrop-blur-xl lg:block">
            <Link href="/" className="flex items-center gap-3">
              <div className="rounded-2xl bg-cyan-300/10 p-3 text-cyan-200">
                <BarChart3 className="h-6 w-6" />
              </div>
              <div>
                <p className="font-semibold text-white">台股智慧分析</p>
                <p className="text-xs text-slate-500">多代理分析系統</p>
              </div>
            </Link>
            <nav className="mt-10 space-y-2">
              {nav.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium text-slate-400 transition hover:bg-white/[.06] hover:text-white"
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </Link>
              ))}
            </nav>
            <div className="absolute bottom-6 left-6 right-6 rounded-2xl border border-white/[.08] bg-white/[.04] p-4">
              <p className="text-sm font-semibold text-emerald-200">系統狀態</p>
              <p className="mt-2 text-sm leading-6 text-slate-400">已串接 FastAPI 分析後端，投資結論僅供課程研究與參考。</p>
            </div>
          </aside>
          <main className="w-full px-5 py-6 sm:px-8 lg:px-10">{children}</main>
        </div>
      </body>
    </html>
  );
}
