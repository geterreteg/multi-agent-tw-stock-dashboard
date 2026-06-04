import { formatNumber, formatSigned } from "@/lib/formatters";

type KpiCardProps = {
  label: string;
  value: number | null;
  suffix?: string;
  signed?: boolean;
};

export function KpiCard({ label, value, suffix = "", signed = false }: KpiCardProps) {
  const formatted = signed ? formatSigned(value, suffix) : formatNumber(value, suffix);
  const positive = signed && value !== null && value > 0;

  return (
    <div className="rounded-2xl border border-white/[.08] bg-white/[.045] p-5 shadow-glass">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-3 text-2xl font-semibold tracking-tight text-white">{formatted}</p>
      <div className="mt-4 h-1 rounded-full bg-white/[.06]">
        <div className={`h-full w-2/3 rounded-full ${positive ? "bg-emerald-300/75" : "bg-cyan-300/75"}`} />
      </div>
    </div>
  );
}
