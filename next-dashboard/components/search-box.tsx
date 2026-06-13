"use client";

import { Search } from "lucide-react";
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
    <form onSubmit={submit} className="w-full">
      <div>
        <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_118px]">
          <label className="relative block min-w-0">
            <span className="sr-only">股票代號</span>
            <Search className="pointer-events-none absolute right-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8c8377]" />
            <input
              aria-describedby={error ? "stock-search-error" : undefined}
              aria-invalid={Boolean(error)}
              aria-label="股票代號"
              className="h-11 w-full rounded-lg border border-[#dfd6ca] bg-[#fffdf9] pl-4 pr-11 text-sm text-[#2b2925] shadow-[0_10px_24px_rgba(58,50,40,.04)] outline-none transition placeholder:text-[#9a9185] focus:border-[#b8aa98] focus:ring-4 focus:ring-[#b8aa98]/[.12]"
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
            className="inline-flex h-11 items-center justify-center rounded-lg bg-[#282521] px-5 text-sm font-medium text-white shadow-[0_12px_26px_rgba(43,39,33,.18)] transition hover:bg-[#3a352f] active:translate-y-px"
            type="submit"
          >
            開始研究
          </button>
        </div>
      </div>
      {error ? (
        <p id="stock-search-error" className="mt-3 border-l border-[#b0834f] pl-3 text-sm font-medium text-[#7d4a19]">
          {error}
        </p>
      ) : null}
    </form>
  );
}
