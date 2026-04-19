"use client";

import { useState, useEffect, useMemo } from "react";
import apiClient from "@/lib/api-client";
import {
  Calendar,
  List,
  ChevronLeft,
  ChevronRight,
  Check,
  X,
  Filter,
  Clock,
  RefreshCw,
} from "lucide-react";

interface Appointment {
  id: string;
  patient_id: string;
  patient_name: string;
  doctor_id: string;
  doctor_name: string;
  appointment_type: string;
  status: string;
  scheduled_at: string;
  duration_minutes: number;
  reason: string | null;
  notes: string | null;
}

const TYPE_STYLES: Record<string, string> = {
  in_person: "bg-blue-100 text-blue-800",
  telemedicine: "bg-purple-100 text-purple-800",
  follow_up: "bg-teal-100 text-teal-800",
  emergency: "bg-red-100 text-red-800",
};

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-amber-50 text-amber-800",
  scheduled: "bg-blue-50 text-blue-700",
  confirmed: "bg-green-50 text-green-700",
  in_progress: "bg-amber-50 text-amber-700",
  completed: "bg-gray-50 text-gray-600",
  cancelled: "bg-red-50 text-red-600",
  no_show: "bg-orange-50 text-orange-700",
  denied: "bg-slate-100 text-slate-600",
};

const ALL_STATUSES = [
  "pending",
  "scheduled",
  "confirmed",
  "in_progress",
  "completed",
  "cancelled",
  "no_show",
  "denied",
];
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export default function DoctorAppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"list" | "calendar">("list");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [calendarDate, setCalendarDate] = useState(new Date());

  useEffect(() => { fetchAppointments(); }, []);

  const fetchAppointments = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get("/appointments");
      const data = res.data.appointments ?? res.data ?? [];
      setAppointments(Array.isArray(data) ? data : []);
      setError(null);
    } catch { setError("Failed to load appointments."); }
    finally { setLoading(false); }
  };

  const filtered = useMemo(() => {
    if (statusFilter === "all") return appointments;
    return appointments.filter((a) => a.status === statusFilter);
  }, [appointments, statusFilter]);

  const now = new Date();
  const todayStr = now.toISOString().split("T")[0];
  const todayAppointments = appointments.filter((a) => a.scheduled_at?.startsWith(todayStr));
  const upcoming = filtered.filter((a) => new Date(a.scheduled_at) > now && a.status !== "cancelled" && a.status !== "completed" && a.status !== "denied")
    .sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime());
  const past = filtered.filter(
    (a) =>
      new Date(a.scheduled_at) <= now ||
      ["completed", "cancelled", "denied"].includes(a.status)
  )
    .sort((a, b) => new Date(b.scheduled_at).getTime() - new Date(a.scheduled_at).getTime());

  const totalThisWeek = appointments.filter((a) => {
    const d = new Date(a.scheduled_at); const ws = new Date(now);
    ws.setDate(now.getDate() - now.getDay()); ws.setHours(0,0,0,0);
    const we = new Date(ws); we.setDate(ws.getDate() + 7);
    return d >= ws && d < we;
  }).length;

  const pending = appointments.filter(
    (a) =>
      (a.status === "pending" || a.status === "scheduled") &&
      new Date(a.scheduled_at) > now
  ).length;

  const handleConfirm = async (id: string) => {
    setActionLoading(id);
    try {
      await apiClient.put(`/appointments/${id}/confirm`, {});
      setAppointments((prev) => prev.map((a) => (a.id === id ? { ...a, status: "confirmed" } : a)));
    } catch { alert("Failed to confirm appointment."); }
    finally { setActionLoading(null); }
  };

  const handleDeny = async (id: string) => {
    if (!confirm("Deny this booking request? The patient will see it as denied.")) return;
    setActionLoading(id);
    try {
      await apiClient.put(`/appointments/${id}/deny`, {});
      setAppointments((prev) => prev.map((a) => (a.id === id ? { ...a, status: "denied" } : a)));
    } catch {
      alert("Failed to deny appointment.");
    } finally {
      setActionLoading(null);
    }
  };

  const handleCancel = async (id: string) => {
    if (!confirm("Cancel this appointment?")) return;
    setActionLoading(id);
    try {
      await apiClient.put(`/appointments/${id}/cancel`, { reason: "Cancelled by doctor" });
      setAppointments((prev) => prev.map((a) => (a.id === id ? { ...a, status: "cancelled" } : a)));
    } catch { alert("Failed to cancel appointment."); }
    finally { setActionLoading(null); }
  };

  const calYear = calendarDate.getFullYear();
  const calMonth = calendarDate.getMonth();
  const firstDay = new Date(calYear, calMonth, 1).getDay();
  const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();

  const calendarDays = useMemo(() => {
    const days: (number | null)[] = [];
    for (let i = 0; i < firstDay; i++) days.push(null);
    for (let d = 1; d <= daysInMonth; d++) days.push(d);
    return days;
  }, [firstDay, daysInMonth]);

  const appointmentsByDate = useMemo(() => {
    const map: Record<string, Appointment[]> = {};
    filtered.forEach((a) => { const k = a.scheduled_at?.split("T")[0]; if (k) { if (!map[k]) map[k] = []; map[k].push(a); } });
    return map;
  }, [filtered]);

  const renderRow = (appt: Appointment) => (
    <div key={appt.id} className="grid grid-cols-7 items-center px-6 py-3 text-sm transition-colors hover:bg-muted/50">
      <span className="font-medium text-foreground">{appt.patient_name ?? "Unknown"}</span>
      <span className="text-muted-foreground">{new Date(appt.scheduled_at).toLocaleDateString()} {new Date(appt.scheduled_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
      <span className="text-muted-foreground">{appt.duration_minutes ?? 30} min</span>
      <span><span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${TYPE_STYLES[appt.appointment_type] ?? "bg-gray-100 text-gray-700"}`}>{(appt.appointment_type ?? "unknown").replace("_", " ")}</span></span>
      <span><span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[appt.status] ?? "bg-gray-100 text-gray-700"}`}>{appt.status}</span></span>
      <span className="truncate text-muted-foreground">{appt.reason ?? "--"}</span>
      <span className="flex items-center justify-end gap-1">
        {(appt.status === "pending" || appt.status === "scheduled") && (<>
          <button onClick={() => handleConfirm(appt.id)} disabled={actionLoading === appt.id} className="inline-flex items-center gap-1 rounded-md bg-green-50 px-2 py-1 text-xs font-medium text-green-700 hover:bg-green-100 disabled:opacity-50"><Check className="h-3 w-3" /> Confirm</button>
          <button onClick={() => handleDeny(appt.id)} disabled={actionLoading === appt.id} className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-200 disabled:opacity-50"><X className="h-3 w-3" /> Deny</button>
          <button onClick={() => handleCancel(appt.id)} disabled={actionLoading === appt.id} className="inline-flex items-center gap-1 rounded-md bg-red-50 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-100 disabled:opacity-50"><X className="h-3 w-3" /> Cancel</button>
        </>)}
        {appt.status === "confirmed" && (
          <button onClick={() => handleCancel(appt.id)} disabled={actionLoading === appt.id} className="inline-flex items-center gap-1 rounded-md bg-red-50 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-100 disabled:opacity-50"><X className="h-3 w-3" /> Cancel</button>
        )}
      </span>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Appointments</h1>
          <p className="mt-1 text-sm text-muted-foreground">Manage your appointment schedule and patient consultations.</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setView("list")} className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${view === "list" ? "bg-primary text-primary-foreground" : "border border-input hover:bg-muted"}`}><List className="h-4 w-4" /> List</button>
          <button onClick={() => setView("calendar")} className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${view === "calendar" ? "bg-primary text-primary-foreground" : "border border-input hover:bg-muted"}`}><Calendar className="h-4 w-4" /> Calendar</button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm"><div className="flex items-center gap-2"><Clock className="h-5 w-5 text-blue-500" /><p className="text-sm font-medium text-muted-foreground">Today</p></div><p className="mt-2 text-3xl font-bold text-foreground">{todayAppointments.length}</p></div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm"><div className="flex items-center gap-2"><Calendar className="h-5 w-5 text-purple-500" /><p className="text-sm font-medium text-muted-foreground">This Week</p></div><p className="mt-2 text-3xl font-bold text-foreground">{totalThisWeek}</p></div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm"><div className="flex items-center gap-2"><RefreshCw className="h-5 w-5 text-amber-500" /><p className="text-sm font-medium text-muted-foreground">Pending</p></div><p className="mt-2 text-3xl font-bold text-primary">{pending}</p></div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium text-muted-foreground">Status:</span>
        <button onClick={() => setStatusFilter("all")} className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${statusFilter === "all" ? "bg-primary text-primary-foreground" : "border border-input text-muted-foreground hover:bg-muted"}`}>All</button>
        {ALL_STATUSES.map((s) => (<button key={s} onClick={() => setStatusFilter(s)} className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${statusFilter === s ? "bg-primary text-primary-foreground" : `border border-input hover:bg-muted ${STATUS_STYLES[s] ?? "text-muted-foreground"}`}`}>{s.replace("_", " ")}</button>))}
      </div>

      {loading && (<div className="flex items-center justify-center py-12"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /><span className="ml-3 text-sm text-muted-foreground">Loading...</span></div>)}
      {error && (<div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4"><p className="text-sm text-destructive">{error}</p><button onClick={fetchAppointments} className="mt-2 text-sm font-medium text-primary hover:underline">Retry</button></div>)}

      {!loading && !error && view === "calendar" && (
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <button onClick={() => setCalendarDate(new Date(calYear, calMonth - 1, 1))} className="rounded-md p-1.5 hover:bg-muted"><ChevronLeft className="h-5 w-5" /></button>
            <h2 className="text-lg font-semibold text-foreground">{calendarDate.toLocaleString("default", { month: "long", year: "numeric" })}</h2>
            <button onClick={() => setCalendarDate(new Date(calYear, calMonth + 1, 1))} className="rounded-md p-1.5 hover:bg-muted"><ChevronRight className="h-5 w-5" /></button>
          </div>
          <div className="mt-4 grid grid-cols-7 text-center text-xs font-semibold uppercase text-muted-foreground">{DAYS.map((d) => (<div key={d} className="py-2">{d}</div>))}</div>
          <div className="grid grid-cols-7 gap-px bg-border">
            {calendarDays.map((day, idx) => {
              if (day === null) return <div key={`e-${idx}`} className="min-h-[80px] bg-card p-1" />;
              const ds = `${calYear}-${String(calMonth+1).padStart(2,"0")}-${String(day).padStart(2,"0")}`;
              const da = appointmentsByDate[ds] ?? [];
              const it = ds === todayStr;
              return (<div key={ds} className={`min-h-[80px] bg-card p-1 ${it ? "ring-2 ring-inset ring-primary" : ""}`}>
                <div className={`mb-1 text-xs font-medium ${it ? "text-primary" : "text-foreground"}`}>{day}</div>
                {da.slice(0,3).map((a) => (<div key={a.id} className={`mb-0.5 truncate rounded px-1 py-0.5 text-[10px] font-medium ${STATUS_STYLES[a.status] ?? "bg-gray-50 text-gray-600"}`} title={`${a.patient_name}`}>{new Date(a.scheduled_at).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})} {a.patient_name?.split(" ")[0]}</div>))}
                {da.length > 3 && <div className="text-[10px] text-muted-foreground">+{da.length-3} more</div>}
              </div>);
            })}
          </div>
        </div>
      )}

      {!loading && !error && view === "list" && (<>
        <div className="rounded-lg border border-border bg-card shadow-sm">
          <div className="border-b border-border px-6 py-4"><h2 className="text-lg font-semibold text-foreground">Upcoming ({upcoming.length})</h2></div>
          {upcoming.length === 0 ? (<div className="px-6 py-8 text-center text-sm text-muted-foreground">No upcoming appointments.</div>) : (<>
            <div className="border-b border-border px-6 py-2"><div className="grid grid-cols-7 text-xs font-semibold uppercase tracking-wider text-muted-foreground"><span>Patient</span><span>Date & Time</span><span>Duration</span><span>Type</span><span>Status</span><span>Reason</span><span className="text-right">Actions</span></div></div>
            <div className="divide-y divide-border">{upcoming.slice(0,20).map(renderRow)}</div>
          </>)}
        </div>
        {past.length > 0 && (<div className="rounded-lg border border-border bg-card shadow-sm">
          <div className="border-b border-border px-6 py-4"><h2 className="text-lg font-semibold text-foreground">Past ({past.length})</h2></div>
          <div className="border-b border-border px-6 py-2"><div className="grid grid-cols-7 text-xs font-semibold uppercase tracking-wider text-muted-foreground"><span>Patient</span><span>Date & Time</span><span>Duration</span><span>Type</span><span>Status</span><span>Reason</span><span className="text-right">Actions</span></div></div>
          <div className="divide-y divide-border">{past.slice(0,20).map(renderRow)}</div>
        </div>)}
      </>)}
    </div>
  );
}
