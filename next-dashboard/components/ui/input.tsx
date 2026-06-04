import * as React from "react";

import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      className={cn(
        "h-12 w-full rounded-xl border border-white/10 bg-slate-950/55 px-4 text-sm text-white placeholder:text-slate-500 outline-none transition focus:border-cyan-300/55 focus:ring-4 focus:ring-cyan-300/10",
        className,
      )}
      ref={ref}
      {...props}
    />
  ),
);
Input.displayName = "Input";

export { Input };
