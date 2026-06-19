import { AlertTriangle, Scale } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { formatTaiwanPrice, formatTargetPe, formatTargetUpside, normalizeTargetPrice, TARGET_PRICE_DISCLOSURE } from "@/lib/target-price";
import type { HistoricalPE, TargetPrice } from "@/lib/types";

export function TargetPricePanel({ targetPrice, historicalPE }: { targetPrice?: TargetPrice; historicalPE?: HistoricalPE }) {
  const target = normalizeTargetPrice(targetPrice);

  if (target.valuationMethod === "INSUFFICIENT_DATA") {
    return (
      <section className="rounded-2xl border border-[#ead6ad] bg-[#fff9ee] p-5 text-[#4d3b1f] md:col-span-2">
        <div className="flex items-start gap-3">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-[#b7791f]" />
          <div>
            <h3 className="font-semibold">資料不足，暫不產生規則式估值區間</h3>
            <p className="mt-2 text-sm leading-7 text-[#7a6140]">規則式估值只在 EPS 與 PE 口徑可追溯時建立，不為展示需求補造數字。</p>
          </div>
        </div>
        <HistoricalPeSummary historicalPE={historicalPE} />
        <InfoList title="資料限制" items={target.limitations} />
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-[#dfd3c2] bg-[#fffdf9] p-5 shadow-[0_12px_30px_rgba(57,49,37,.045)] md:col-span-2">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <Scale className="mt-0.5 h-5 w-5 text-[#7d5d2e]" />
          <div>
            <h3 className="font-semibold text-[#2b2925]">規則式估值區間｜歷史 PE 估值參考</h3>
            <p className="mt-1 text-sm text-[#746b60]">Base 隱含空間 {formatTargetUpside(target.impliedUpsidePct)}</p>
          </div>
        </div>
        <Badge className="border-[#d8c29e] bg-[#fbf1df] text-[#76572a]">confidence {target.confidence}/65</Badge>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <ScenarioCard label="Bear" price={target.bearTargetPrice} pe={target.bearPERatio} />
        <ScenarioCard label="Base" price={target.baseTargetPrice} pe={target.fairPERatio} featured />
        <ScenarioCard label="Bull" price={target.bullTargetPrice} pe={target.bullPERatio} />
      </div>

      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-4">
        <Meta label="目前股價" value={formatTaiwanPrice(target.currentPrice)} />
        <Meta label="EPS basis" value={epsBasisLabel(target.epsBasis)} />
        <Meta label="EPS used" value={target.epsUsed === null ? "資料暫無" : target.epsUsed.toFixed(2)} />
        <Meta label="PE source" value={peSourceLabel(target.peSource)} />
      </dl>

      <HistoricalPeSummary historicalPE={historicalPE} />
      <p className="mt-5 rounded-xl border border-[#e8e0d5] bg-[#fbf7ef] p-4 text-xs leading-6 text-[#6f665c]">{TARGET_PRICE_DISCLOSURE}</p>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <InfoList title="假設" items={target.assumptions} />
        <InfoList title="限制" items={target.limitations} />
      </div>
    </section>
  );
}

function HistoricalPeSummary({ historicalPE }: { historicalPE?: HistoricalPE }) {
  if (!historicalPE) {
    return <p className="mt-4 rounded-xl border border-[#ead6ad] bg-[#fff9ee] p-4 text-sm text-[#7a6140]">歷史 PE 資料尚未隨 API 回傳。</p>;
  }
  const values = [
    ["Min", historicalPE.minPE],
    ["P25", historicalPE.p25PE],
    ["Median", historicalPE.medianPE],
    ["P75", historicalPE.p75PE],
    ["Max", historicalPE.maxPE],
  ] as const;

  return (
    <section className="mt-5 rounded-2xl border border-[#e8e0d5] bg-[#fbf7ef] p-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h4 className="font-semibold text-[#3d3933]">歷史 PE 估值參考</h4>
          <p className="mt-1 text-xs text-[#746b60]">有效樣本 {historicalPE.validSampleCount} 筆｜{historicalPE.source}</p>
        </div>
        <Badge className="border-[#d8c29e] bg-white text-[#76572a]">{historicalPE.cacheStatus === "cache" ? "快取降級" : historicalPE.cacheStatus === "live" ? "TWSE 本次取得" : "資料不足"}</Badge>
      </div>
      <dl className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-5">
        {values.map(([label, value]) => <Meta key={label} label={label} value={formatTargetPe(value)} />)}
      </dl>
      <InfoList title="資料限制" items={historicalPE.dataLimitations} />
    </section>
  );
}

function ScenarioCard({ label, price, pe, featured = false }: { label: string; price: number | null; pe: number | null; featured?: boolean }) {
  return (
    <div className={`rounded-2xl border p-4 ${featured ? "border-[#c9aa77] bg-[#fbf1df]" : "border-[#e8e0d5] bg-[#fbf7ef]"}`}>
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#8a8175]">{label}</p>
      <p className="mt-2 text-3xl font-semibold tabular-nums text-[#2b2925]">{formatTaiwanPrice(price)}</p>
      <p className="mt-2 text-xs text-[#746b60]">PE {formatTargetPe(pe)}</p>
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-[#e8e0d5] bg-[#fbf7ef] px-3 py-3">
      <dt className="text-xs text-[#8a8175]">{label}</dt>
      <dd className="mt-1 font-semibold text-[#3d3933]">{value}</dd>
    </div>
  );
}

function InfoList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mt-4">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#8a8175]">{title}</p>
      <ul className="mt-2 space-y-2 text-sm leading-6 text-[#625b52]">
        {(items.length > 0 ? items : ["資料暫無"]).map((item) => <li key={item}>• {item}</li>)}
      </ul>
    </div>
  );
}

function epsBasisLabel(basis: TargetPrice["epsBasis"]) {
  if (basis === "FORWARD") return "Forward EPS";
  if (basis === "TTM" || basis === "TTM_EPS") return "TTM EPS";
  if (basis === "FOUR_QUARTERS") return "近四季 EPS 合計";
  if (basis === "SINGLE_QUARTER") return "單季 EPS（不足）";
  return "資料不足";
}

function peSourceLabel(source: TargetPrice["peSource"]) {
  if (source === "HISTORICAL_TWSE") return "TWSE 歷史 PE 分位數";
  if (source === "EXTERNAL") return "currentPE 原始欄位";
  if (source === "DERIVED") return "price / EPS 推導";
  return "資料不足";
}
