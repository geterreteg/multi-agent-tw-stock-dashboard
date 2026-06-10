import type { Metadata } from "next";
import Link from "next/link";
import { BarChart3, Home } from "lucide-react";

import { MobileTopBar } from "@/components/mobile-top-bar";

import "./globals.css";

export const metadata: Metadata = {
  title: "多 Agent 台股智慧分析儀表板",
  description: "整合價格、基本面、籌碼與多 Agent 評分的台股研究分析儀表板。",
};

const nav = [
  { href: "/", label: "首頁總覽", icon: Home },
  { href: "/#stock-search", label: "股票分析", icon: BarChart3 },
];

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-Hant" className="dark">
      <body>
        <MobileTopBar />
        <div className="relative mx-auto flex min-h-screen max-w-[1540px]">
          <aside className="sticky top-0 hidden h-screen w-72 shrink-0 border-r border-[rgba(199,183,143,.14)] bg-[rgba(5,8,10,.68)] p-6 backdrop-blur-xl lg:block">
            <Link href="/" className="flex items-center gap-3">
              <div className="border border-[rgba(199,183,143,.22)] bg-[rgba(199,183,143,.07)] p-3 text-[rgb(207,224,203)]">
                <BarChart3 className="h-6 w-6" />
              </div>
              <div>
                <p className="font-semibold text-[rgb(244,241,232)]">台股研究終端</p>
                <p className="text-xs text-slate-500">Multi-Agent Research</p>
              </div>
            </Link>
            <nav className="mt-10 space-y-2">
              {nav.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-3 border border-transparent px-4 py-3 text-sm font-medium text-slate-400 transition hover:border-[rgba(199,183,143,.16)] hover:bg-white/[.045] hover:text-[rgb(244,241,232)]"
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </Link>
              ))}
            </nav>
            <div className="absolute bottom-6 left-6 right-6 border border-[rgba(199,183,143,.14)] bg-white/[.035] p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[rgb(207,224,203)]">System Status</p>
              <p className="mt-2 text-sm leading-6 text-slate-400">已串接 FastAPI 分析後端，投資結論僅供課程研究與參考。</p>
            </div>
          </aside>
          <main className="w-full px-5 py-6 sm:px-8 lg:px-10">{children}</main>
        </div>
      </body>
    </html>
  );
}
