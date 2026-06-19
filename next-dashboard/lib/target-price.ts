import type { TargetPrice } from "@/lib/types";

export const TARGET_PRICE_DISCLOSURE =
  "本目標價採規則式 PE Multiple 法，以目前可驗證本益比作為 Base Case 估值基準，並以固定折溢價建立 Bear / Bull 情境。由於尚未納入歷史 PE 區間、同業估值、DCF 與法人一致性預估，本目標價應視為估值參考區間，而非正式法人目標價。";

export const INSUFFICIENT_TARGET_PRICE: TargetPrice = {
  currentPrice: null,
  baseTargetPrice: null,
  bearTargetPrice: null,
  bullTargetPrice: null,
  impliedUpsidePct: null,
  valuationMethod: "INSUFFICIENT_DATA",
  epsBasis: "UNAVAILABLE",
  epsUsed: null,
  fairPERatio: null,
  bearPERatio: null,
  bullPERatio: null,
  confidence: 0,
  assumptions: [],
  limitations: ["資料不足，暫不產生正式 12M 目標價。"],
  peSource: "UNAVAILABLE",
};

export function normalizeTargetPrice(targetPrice?: TargetPrice): TargetPrice {
  return targetPrice ?? INSUFFICIENT_TARGET_PRICE;
}

export function formatTaiwanPrice(value: number | null): string {
  return value === null || !Number.isFinite(value) ? "資料暫無" : Math.round(value).toLocaleString("zh-TW");
}

export function formatTargetUpside(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "資料暫無";
  return `${value >= 0 ? "+" : ""}${value.toFixed(1)}%`;
}

export function formatTargetPe(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "資料暫無";
  return value.toLocaleString("zh-TW", { minimumFractionDigits: 1, maximumFractionDigits: 2 });
}

export function targetPriceSummary(targetPrice?: TargetPrice): string {
  const target = normalizeTargetPrice(targetPrice);
  return target.valuationMethod === "RULE_BASED_PE_MULTIPLE"
    ? `${formatTaiwanPrice(target.baseTargetPrice)}（${formatTargetUpside(target.impliedUpsidePct)}）`
    : "資料不足，暫不產生正式 12M 目標價";
}
