import { LucideIcon } from "lucide-react";

import { Card } from "@/components/ui/card";

type StatusCardProps = {
  icon: LucideIcon;
  label: string;
  value: string;
  detail: string;
};

export function StatusCard({ icon: Icon, label, value, detail }: StatusCardProps) {
  return (
    <Card className="group p-5 transition duration-300 hover:border-cyan-300/20 hover:bg-white/[.075]">
      <div className="flex items-start gap-4">
        <div className="rounded-2xl border border-cyan-300/15 bg-cyan-300/10 p-3 text-cyan-200">
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm text-slate-400">{label}</p>
          <p className="mt-1 text-xl font-semibold text-white">{value}</p>
          <p className="mt-2 text-sm leading-6 text-slate-500">{detail}</p>
        </div>
      </div>
    </Card>
  );
}
