"use client";

import { ArrowRight, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function SearchBox() {
  const router = useRouter();
  const [symbol, setSymbol] = useState("2330");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = symbol.trim();
    if (normalized) {
      router.push(`/stocks/${normalized}`);
    }
  }

  return (
    <form onSubmit={submit} className="flex w-full max-w-2xl flex-col gap-3 sm:flex-row">
      <div className="relative flex-1">
        <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500" />
        <Input
          aria-label="股票代碼"
          className="pl-12"
          value={symbol}
          onChange={(event) => setSymbol(event.target.value)}
          placeholder="輸入股票代碼，例如 2330"
        />
      </div>
      <Button type="submit" size="lg">
        開始分析
        <ArrowRight className="h-4 w-4" />
      </Button>
    </form>
  );
}
