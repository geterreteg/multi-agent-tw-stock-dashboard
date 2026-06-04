import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";

export function PlaceholderPage({ title, description }: { title: string; description: string }) {
  return (
    <section className="rounded-[2rem] border border-white/[.09] bg-white/[.045] p-8 shadow-glass">
      <h1 className="text-4xl font-semibold tracking-tight text-white">{title}</h1>
      <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-400">{description}</p>
      <div className="mt-8">
        <Link href="/" className={buttonVariants({ variant: "secondary" })}>
          返回首頁總覽
        </Link>
      </div>
    </section>
  );
}
