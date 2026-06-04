import { StockAnalysisClient } from "@/components/stocks/stock-analysis-client";

export const dynamic = "force-dynamic";

type PageProps = {
  params: Promise<{ symbol: string }>;
};

export default async function StockAnalysisPage({ params }: PageProps) {
  const { symbol } = await params;
  return <StockAnalysisClient symbol={symbol} />;
}
