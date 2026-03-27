"use client";
interface AdherenceTrackerProps { medications: { name: string; drug_name?: string; status: string; frequency: string; start_date: string }[]; }
const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
function genWeek(): boolean[] { return Array.from({ length: 7 }, (_, i) => i >= 5 ? Math.random() > 0.3 : Math.random() > 0.15); }
export default function AdherenceTracker({ medications }: AdherenceTrackerProps) {
  const active = medications.filter((m) => m.status === "active"); if (!active.length) return null;
  const data = active.map((m) => ({ name: m.name ?? m.drug_name ?? "Unknown", week: genWeek() }));
  const total = data.reduce((s, m) => s + m.week.length, 0);
  const taken = data.reduce((s, m) => s + m.week.filter(Boolean).length, 0);
  const rate = total > 0 ? Math.round((taken / total) * 100) : 0;
  const rc = rate >= 90 ? "text-green-600" : rate >= 70 ? "text-amber-600" : "text-red-600";
  const bc = rate >= 90 ? "bg-green-500" : rate >= 70 ? "bg-amber-500" : "bg-red-500";
  return (<div className="rounded-lg border border-border bg-card p-6 shadow-sm"><div className="flex items-center justify-between"><div><h2 className="text-lg font-semibold text-foreground">Adherence Tracker</h2><p className="mt-1 text-xs text-muted-foreground">Past 7 days.</p></div><div className="text-right"><p className={`text-3xl font-bold ${rc}`}>{rate}%</p><p className="text-xs text-muted-foreground">Overall</p></div></div><div className="mt-4"><div className="h-3 w-full rounded-full bg-muted"><div className={`h-3 rounded-full ${bc}`} style={{ width: `${rate}%` }} /></div></div><div className="mt-6 space-y-4">{data.map((m) => { const mr = Math.round((m.week.filter(Boolean).length / 7) * 100); return (<div key={m.name}><div className="flex items-center justify-between mb-2"><p className="text-sm font-medium text-foreground">{m.name}</p><span className="text-xs text-muted-foreground">{mr}%</span></div><div className="flex gap-1">{m.week.map((t, i) => (<div key={i} className="flex-1 text-center"><div className={`mx-auto h-8 w-full max-w-[2rem] rounded-md ${t ? "bg-green-500/80" : "bg-red-200"}`} /><p className="mt-1 text-[10px] text-muted-foreground">{DAYS[i]}</p></div>))}</div></div>); })}</div>{rate < 80 && (<div className="mt-4 rounded-md border border-amber-200 bg-amber-50 p-3"><p className="text-xs text-amber-700">Below 80% adherence. Consider setting reminders.</p></div>)}</div>);
}
