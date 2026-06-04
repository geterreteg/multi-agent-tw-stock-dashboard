import type { AnalyzeResponse } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function analyzeStock(symbol: string, period = "6mo"): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol, period }),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("分析 API 暫時無法回應");
  }

  return response.json();
}

export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/api/health`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("API 健康檢查失敗");
  }
  return response.json() as Promise<{ status: string; service: string; version: string }>;
}
