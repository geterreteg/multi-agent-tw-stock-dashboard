"use client";

import { ArrowRight, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

export function SearchBox() {
  const router = useRouter();
  const [symbol, setSymbol] = useState("");
  const [error, setError] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = symbol.trim();
    if (!/^\d{4}$/.test(normalized)) {
      setError("請輸入 4 位數台股代號");
      return;
    }
    setError("");
    router.push(`/stocks/${normalized}`);
  }

  return (
    <form onSubmit={submit} className="w-full max-w-3xl">
      <div className="relative overflow-hidden border border-[rgba(217,204,166,.36)] bg-[rgba(250,246,235,.94)] p-3 shadow-[0_24px_90px_rgba(0,0,0,.26),0_0_0_1px_rgba(255,255,255,.08)_inset] backdrop-blur-md">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[rgba(32,100,93,.45)] to-transparent" />
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2 px-1">
          <span className="text-xs font-semibold tracking-[0.22em] text-[rgb(32,100,93)]">研究票據</span>
          <span className="font-mono text-[11px] uppercase tracking-[0.16em] text-[rgba(31,42,43,.48)]">TWSE / TPEX</span>
        </div>
        <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]">
          <label className="relative block min-w-0">
            <span className="sr-only">股票代號</span>
            <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-[rgba(32,100,93,.76)]" />
            <input
              aria-describedby={error ? "stock-search-error" : undefined}
              aria-invalid={Boolean(error)}
              aria-label="股票代號"
              className="h-14 w-full border border-[rgba(31,42,43,.14)] bg-[rgb(248,244,232)] pl-12 pr-4 font-mono text-lg tabular-nums tracking-[0.22em] text-[rgb(18,24,25)] outline-none transition placeholder:font-sans placeholder:text-sm placeholder:tracking-normal placeholder:text-[rgba(31,42,43,.42)] focus:border-[rgba(32,100,93,.55)] focus:ring-4 focus:ring-[rgba(32,100,93,.1)]"
              inputMode="numeric"
              maxLength={4}
              pattern="[0-9]{4}"
              value={symbol}
              onChange={(event) => {
                setSymbol(event.target.value.replace(/\D/g, "").slice(0, 4));
                if (error) setError("");
              }}
              placeholder="輸入股票代號，例如 2330"
            />
          </label>
          <button
            className="inline-flex h-14 items-center justify-center gap-2 border border-[rgba(31,42,43,.16)] bg-[rgb(22,30,31)] px-5 text-sm font-semibold text-[rgb(248,244,232)] shadow-[0_16px_34px_rgba(22,30,31,.18)] transition hover:bg-[rgb(31,86,81)] active:translate-y-px sm:px-7"
            type="submit"
          >
            建立研究摘要
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>
      {error ? (
        <p id="stock-search-error" className="mt-3 border-l border-[rgba(170,107,39,.55)] pl-3 text-sm font-medium text-[rgb(125,74,25)]">
          {error}
        </p>
      ) : null}
    </form>
  );
}
