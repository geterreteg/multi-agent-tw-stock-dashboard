"use client";

import { useEffect, useState } from "react";
import { NotebookPen, Save, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";

type DecisionNote = {
  action: "觀察" | "買進" | "持有" | "減碼" | "賣出";
  thesis: string;
  targetPrice: string;
  stopLoss: string;
  invalidation: string;
  tracking: string;
  remarks: string;
};

const EMPTY_NOTE: DecisionNote = {
  action: "觀察",
  thesis: "",
  targetPrice: "",
  stopLoss: "",
  invalidation: "",
  tracking: "",
  remarks: "",
};

export function DecisionNotes({ symbol }: { symbol: string }) {
  const [note, setNote] = useState<DecisionNote>(EMPTY_NOTE);
  const [status, setStatus] = useState("尚未儲存");
  const storageKey = `tw-stock-decision-note:${symbol}`;

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(storageKey);
      if (saved) {
        setNote({ ...EMPTY_NOTE, ...(JSON.parse(saved) as Partial<DecisionNote>) });
        setStatus("已載入此瀏覽器的筆記");
      } else {
        setNote(EMPTY_NOTE);
        setStatus("尚未儲存");
      }
    } catch {
      setStatus("瀏覽器儲存不可用；仍可在本頁暫時編輯");
    }
  }, [storageKey]);

  const update = (field: keyof DecisionNote, value: string) => setNote((current) => ({ ...current, [field]: value }));

  const save = () => {
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(note));
      setStatus("已儲存在此瀏覽器");
    } catch {
      setStatus("儲存失敗；內容仍保留在本頁");
    }
  };

  const clear = () => {
    try {
      window.localStorage.removeItem(storageKey);
      setNote(EMPTY_NOTE);
      setStatus("已清除此股票的瀏覽器筆記");
    } catch {
      setStatus("無法清除瀏覽器儲存");
    }
  };

  return (
    <section className="rounded-2xl border border-[#e4dccf] bg-[#fffdf9] p-5 sm:p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <NotebookPen className="mt-0.5 h-5 w-5 text-[#7d5d2e]" />
          <div>
            <h3 className="font-semibold text-[#2b2925]">{symbol} 決策筆記</h3>
            <p className="mt-1 text-sm leading-6 text-[#746b60]">僅儲存在此瀏覽器，不會同步雲端，也不會送往後端。</p>
          </div>
        </div>
        <p className="text-xs text-[#8a8175]">{status}</p>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <Field label="我的動作">
          <select value={note.action} onChange={(event) => update("action", event.target.value)} className={inputClass()}>
            {["觀察", "買進", "持有", "減碼", "賣出"].map((action) => <option key={action}>{action}</option>)}
          </select>
        </Field>
        <Field label="目標價">
          <input type="number" inputMode="decimal" value={note.targetPrice} onChange={(event) => update("targetPrice", event.target.value)} className={inputClass()} placeholder="輸入你的目標價" />
        </Field>
        <Field label="投資假說" wide><textarea value={note.thesis} onChange={(event) => update("thesis", event.target.value)} className={inputClass("min-h-28")} /></Field>
        <Field label="停損條件"><textarea value={note.stopLoss} onChange={(event) => update("stopLoss", event.target.value)} className={inputClass("min-h-24")} /></Field>
        <Field label="看錯條件"><textarea value={note.invalidation} onChange={(event) => update("invalidation", event.target.value)} className={inputClass("min-h-24")} /></Field>
        <Field label="追蹤重點" wide><textarea value={note.tracking} onChange={(event) => update("tracking", event.target.value)} className={inputClass("min-h-24")} /></Field>
        <Field label="備註" wide><textarea value={note.remarks} onChange={(event) => update("remarks", event.target.value)} className={inputClass("min-h-24")} /></Field>
      </div>

      <div className="mt-5 flex flex-wrap gap-3">
        <Button type="button" onClick={save}><Save className="mr-2 h-4 w-4" />儲存筆記</Button>
        <Button type="button" variant="secondary" onClick={clear}><Trash2 className="mr-2 h-4 w-4" />清除此股票筆記</Button>
      </div>
    </section>
  );
}

function Field({ label, wide = false, children }: { label: string; wide?: boolean; children: React.ReactNode }) {
  return <label className={`grid gap-2 text-sm font-semibold text-[#5f574e] ${wide ? "md:col-span-2" : ""}`}><span>{label}</span>{children}</label>;
}

function inputClass(extra = "") {
  return `w-full rounded-xl border border-[#ded5c8] bg-[#fbf7ef] px-3 py-2.5 font-sans text-sm font-normal text-[#2b2925] outline-none transition focus:border-[#b88a45] focus:ring-2 focus:ring-[#d8ad63]/25 ${extra}`;
}
