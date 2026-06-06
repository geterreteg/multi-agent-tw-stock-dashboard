"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Home } from "lucide-react";

function currentPageName(pathname: string) {
  if (pathname === "/") return "首頁總覽";
  if (pathname.startsWith("/stocks/")) return "股票分析";
  if (pathname.startsWith("/backtest")) return "回測結果";
  if (pathname.startsWith("/events")) return "事件研究";
  if (pathname.startsWith("/settings")) return "設定";
  return "儀表板";
}

export function MobileTopBar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-30 border-b border-white/[.08] bg-slate-950/80 px-4 py-3 backdrop-blur-xl lg:hidden">
      <div className="flex items-center justify-between gap-3">
        <Link href="/" className="flex min-w-0 items-center gap-3">
          <div className="rounded-xl bg-cyan-300/10 p-2 text-cyan-200">
            <BarChart3 className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-white">台股智慧分析</p>
            <p className="text-xs text-slate-500">{currentPageName(pathname)}</p>
          </div>
        </Link>
        <nav className="flex shrink-0 items-center gap-2">
          <Link
            href="/"
            className="inline-flex h-9 items-center gap-1 rounded-full border border-white/[.08] bg-white/[.04] px-3 text-xs font-medium text-slate-300"
          >
            <Home className="h-3.5 w-3.5" />
            首頁
          </Link>
          <Link
            href="/#stock-search"
            className="inline-flex h-9 items-center rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 text-xs font-semibold text-cyan-100"
          >
            分析
          </Link>
        </nav>
      </div>
    </header>
  );
}
