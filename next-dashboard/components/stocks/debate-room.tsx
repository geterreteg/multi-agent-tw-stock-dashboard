import { MessageSquareText } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { DebateMessage } from "@/lib/types";

export function DebateRoom({ messages }: { messages: DebateMessage[] }) {
  return (
    <section className="rounded-2xl border border-[#e4dccf] bg-[#fbf7ef] p-4 sm:p-6">
      <div className="flex items-start gap-3">
        <MessageSquareText className="mt-0.5 h-5 w-5 text-[#7d5d2e]" />
        <div>
          <h3 className="font-semibold text-[#2b2925]">投資委員會聊天室</h3>
          <p className="mt-1 text-sm leading-6 text-[#746b60]">所有發言均由規則式資料與既有 Agent 證據組成，不代表真實法人會議或獲利保證。</p>
        </div>
      </div>

      <div className="mt-6 space-y-4">
        {messages.length > 0 ? messages.map((message, index) => (
          <article key={`${message.role ?? message.speaker}-${index}`} className={`flex ${message.tone === "risk" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-3xl rounded-2xl border p-4 shadow-[0_8px_22px_rgba(57,49,37,.04)] ${bubbleClass(message.tone)}`}>
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-semibold text-[#312e29]">{message.role || message.speaker}</p>
                <Badge className="border-[#ded3c4] bg-white/70 text-[#6d6256]">{message.stance}</Badge>
              </div>
              <p className="mt-3 text-sm leading-7 text-[#554f47]">{message.content || message.message}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {(message.evidenceTags ?? []).map((tag) => (
                  <span key={tag} className="rounded-full border border-[#dfd5c8] bg-white/75 px-2.5 py-1 text-xs text-[#746b60]">{tag}</span>
                ))}
              </div>
            </div>
          </article>
        )) : (
          <div className="rounded-2xl border border-[#ead6ad] bg-[#fff9ee] p-5 text-sm leading-7 text-[#7a6140]">本次無可用辯論資料，請以研究報告與資料限制為準。</div>
        )}
      </div>
    </section>
  );
}

function bubbleClass(tone: DebateMessage["tone"]) {
  if (tone === "risk") return "border-[#e7c7b3] bg-[#fff7f2]";
  if (tone === "support") return "border-[#cdddcf] bg-[#f4faf5]";
  if (tone === "summary") return "border-[#d8c29e] bg-[#fff9ee]";
  return "border-[#dfd5c8] bg-[#fffdf9]";
}
