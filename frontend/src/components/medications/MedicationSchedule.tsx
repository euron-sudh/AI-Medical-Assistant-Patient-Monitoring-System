"use client";
interface MedicationScheduleProps { medications: { name: string; drug_name?: string; dosage: string; frequency: string; status: string }[]; }
function ft(f: string): string[] { const l = f.toLowerCase(); if (l.includes("twice") || l.includes("bid")) return ["08:00 AM", "08:00 PM"]; if (l.includes("three") || l.includes("tid")) return ["08:00 AM", "02:00 PM", "08:00 PM"]; if (l.includes("night") || l.includes("bedtime")) return ["10:00 PM"]; return ["08:00 AM"]; }
const order = ["08:00 AM", "12:00 PM", "02:00 PM", "06:00 PM", "08:00 PM", "10:00 PM"];
export default function MedicationSchedule({ medications }: MedicationScheduleProps) {
  const active = medications.filter((m) => m.status === "active"); if (!active.length) return null;
  const map = new Map<string, { med: string; dose: string }[]>();
  active.forEach((m) => { ft(m.frequency).forEach((t) => { if (!map.has(t)) map.set(t, []); map.get(t)!.push({ med: m.name ?? m.drug_name ?? "Unknown", dose: m.dosage }); }); });
  const times = [...map.keys()].sort((a, b) => order.indexOf(a) - order.indexOf(b));
  return (<div className="rounded-lg border border-border bg-card p-6 shadow-sm"><h2 className="text-lg font-semibold text-foreground">Today&apos;s Schedule</h2><p className="mt-1 text-xs text-muted-foreground">Based on prescribed frequencies.</p><div className="mt-4 space-y-4">{times.map((t) => (<div key={t} className="flex gap-4"><div className="flex flex-col items-center"><div className="flex h-10 w-20 items-center justify-center rounded-md bg-primary/10 text-xs font-semibold text-primary">{t}</div><div className="mt-1 h-full w-px bg-border" /></div><div className="flex-1 space-y-2 pb-2">{map.get(t)!.map((e, i) => (<div key={i} className="flex items-center justify-between rounded-md border border-border px-3 py-2"><div><p className="text-sm font-medium text-foreground">{e.med}</p><p className="text-xs text-muted-foreground">{e.dose}</p></div><span className="rounded-full border-2 border-muted-foreground h-6 w-6 flex items-center justify-center text-xs text-transparent hover:border-green-400">&#10003;</span></div>))}</div></div>))}</div></div>);
}
