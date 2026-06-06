"use client";

import { ArrowRight, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

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
    <form onSubmit={submit} className="w-full max-w-2xl">
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500" />
          <Input
            aria-describedby={error ? "stock-search-error" : undefined}
            aria-invalid={Boolean(error)}
            aria-label="股票代號"
            className="pl-12"
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
        </div>
        <Button type="submit" size="lg">
          開始分析
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
      {error ? (
        <p id="stock-search-error" className="mt-2 text-sm font-medium text-amber-200">
          {error}
        </p>
      ) : null}
    </form>
  );
}
