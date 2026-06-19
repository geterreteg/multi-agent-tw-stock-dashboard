import type { TargetPrice } from "@/lib/types";

export const TARGET_PRICE_DISCLOSURE =
  "本規則式估值區間採 PE Multiple 法：TTM EPS 且歷史 PE 樣本足夠時，使用 p25 / median / p75 建立 Bear / Base / Bull；樣本不足時才以 currentPE 固定折溢價降級。本結果僅為規則式估值參考。";

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
  limitations: ["資料不足，暫不產生規則式估值區間。"],
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
    : "資料不足，暫不產生規則式估值區間";
}
