export function formatNumber(value: number | null, suffix = "") {
  if (value === null || !Number.isFinite(value)) {
    return "資料暫無";
  }
  return `${new Intl.NumberFormat("zh-TW", { maximumFractionDigits: 2 }).format(value)}${suffix}`;
}

export function formatSigned(value: number | null, suffix = "") {
  if (value === null || !Number.isFinite(value)) {
    return "資料暫無";
  }
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatNumber(value, suffix)}`;
}
