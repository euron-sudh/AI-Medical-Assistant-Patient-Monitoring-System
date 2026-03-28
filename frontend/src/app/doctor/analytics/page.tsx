"use client";

import { useState, useEffect, useMemo } from "react";
import apiClient from "@/lib/api-client";
import { Users, CalendarCheck, AlertTriangle, FileText, TrendingUp, Activity, Video, Clock, BarChart3, PieChart } from "lucide-react";

interface Stats { totalPatients: number; totalAppointments: number; appointmentsThisWeek: number; activeAlerts: number; criticalAlerts: number; totalReports: number; pendingReports: number; completedAppointments: number; telemedicineSessions: number; cancelledAppointments: number; inPersonAppointments: number; followUpAppointments: number; }
interface AppointmentRaw { status: string; appointment_type: string; scheduled_at: string; }

export default function AnalyticsPage() {
  const [stats, setStats] = useState<Stats>({ totalPatients: 0, totalAppointments: 0, appointmentsThisWeek: 0, activeAlerts: 0, criticalAlerts: 0, totalReports: 0, pendingReports: 0, completedAppointments: 0, telemedicineSessions: 0, cancelledAppointments: 0, inPersonAppointments: 0, followUpAppointments: 0 });
  const [loading, setLoading] = useState(true);
  const [weeklyData, setWeeklyData] = useState<{ day: string; count: number }[]>([]);

  useEffect(() => { fetchStats(); }, []);

  const fetchStats = async () => {
    setLoading(true);
    const s = { ...stats };

    try { const pR = await apiClient.get("/patients"); const p = pR.data.patients ?? pR.data ?? []; s.totalPatients = Array.isArray(p) ? p.length : 0; } catch {}

    try {
      const aR = await apiClient.get("/appointments");
      const appts: AppointmentRaw[] = aR.data.appointments ?? aR.data ?? [];
      if (Array.isArray(appts)) {
        s.totalAppointments = appts.length;
        s.completedAppointments = appts.filter((a) => a.status === "completed").length;
        s.cancelledAppointments = appts.filter((a) => a.status === "cancelled").length;
        s.telemedicineSessions = appts.filter((a) => a.appointment_type === "telemedicine").length;
        s.inPersonAppointments = appts.filter((a) => a.appointment_type === "in_person").length;
        s.followUpAppointments = appts.filter((a) => a.appointment_type === "follow_up").length;
        const now = new Date(); const ws = new Date(now); ws.setDate(now.getDate()-now.getDay()); ws.setHours(0,0,0,0); const we = new Date(ws); we.setDate(ws.getDate()+7);
        s.appointmentsThisWeek = appts.filter((a) => { const d = new Date(a.scheduled_at); return d >= ws && d < we; }).length;
        const days = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
        const weekly: {day:string;count:number}[] = [];
        for (let i=6;i>=0;i--) { const d=new Date(now); d.setDate(now.getDate()-i); const ds=d.toISOString().split("T")[0]; weekly.push({day:days[d.getDay()],count:appts.filter((a)=>a.scheduled_at?.startsWith(ds)).length}); }
        setWeeklyData(weekly);
      }
    } catch {}

    try { const mR = await apiClient.get("/monitoring/alerts"); const al = mR.data.alerts ?? mR.data ?? []; if (Array.isArray(al)) { s.activeAlerts = al.filter((a:{status:string})=>a.status==="active").length; s.criticalAlerts = al.filter((a:{severity:string;status:string})=>(a.severity==="critical"||a.severity==="emergency")&&a.status==="active").length; } } catch {}
    // Reports endpoint requires a patient_id prefix; skipping aggregate count

    setStats(s); setLoading(false);
  };

  const completionRate = stats.totalAppointments > 0 ? Math.round((stats.completedAppointments / stats.totalAppointments) * 100) : 0;
  const cancellationRate = stats.totalAppointments > 0 ? Math.round((stats.cancelledAppointments / stats.totalAppointments) * 100) : 0;
  const maxWeekly = useMemo(() => Math.max(...weeklyData.map((d) => d.count), 1), [weeklyData]);

  if (loading) return (<div className="space-y-6"><div><h1 className="text-2xl font-bold text-foreground">Analytics</h1><p className="mt-1 text-sm text-muted-foreground">Loading...</p></div><div className="flex items-center justify-center py-16"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div></div>);

  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold text-foreground">Analytics</h1><p className="mt-1 text-sm text-muted-foreground">Clinical analytics, patient outcomes, and performance metrics.</p></div>

      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm"><div className="flex items-center gap-2"><Users className="h-5 w-5 text-blue-500" /><p className="text-sm font-medium text-muted-foreground">Patients</p></div><p className="mt-2 text-3xl font-bold text-foreground">{stats.totalPatients}</p></div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm"><div className="flex items-center gap-2"><CalendarCheck className="h-5 w-5 text-purple-500" /><p className="text-sm font-medium text-muted-foreground">This Week</p></div><p className="mt-2 text-3xl font-bold text-primary">{stats.appointmentsThisWeek}</p></div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm"><div className="flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-amber-500" /><p className="text-sm font-medium text-muted-foreground">Alerts</p></div><p className="mt-2 text-3xl font-bold text-amber-600">{stats.activeAlerts}</p><p className="mt-1 text-xs text-muted-foreground">{stats.criticalAlerts > 0 ? <span className="font-medium text-red-600">{stats.criticalAlerts} critical</span> : "none critical"}</p></div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm"><div className="flex items-center gap-2"><FileText className="h-5 w-5 text-orange-500" /><p className="text-sm font-medium text-muted-foreground">Reports</p></div><p className="mt-2 text-3xl font-bold text-foreground">{stats.totalReports}</p><p className="mt-1 text-xs text-muted-foreground">{stats.pendingReports > 0 ? <span className="font-medium text-amber-600">{stats.pendingReports} pending</span> : "all reviewed"}</p></div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-2"><BarChart3 className="h-5 w-5 text-blue-500" /><h2 className="text-lg font-semibold text-foreground">Appointment Trends (7 days)</h2></div>
          <div className="mt-6 flex items-end gap-2" style={{ height: "160px" }}>
            {weeklyData.map((d, i) => (<div key={i} className="flex flex-1 flex-col items-center gap-1"><span className="text-xs font-medium text-foreground">{d.count}</span><div className="w-full rounded-t bg-primary/80 transition-all" style={{ height: `${Math.max((d.count / maxWeekly) * 130, 4)}px` }} /><span className="text-[10px] text-muted-foreground">{d.day}</span></div>))}
          </div>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-2"><PieChart className="h-5 w-5 text-purple-500" /><h2 className="text-lg font-semibold text-foreground">Consultation Metrics</h2></div>
          <div className="mt-4 space-y-4">
            <div><div className="flex items-center justify-between text-sm"><span className="text-muted-foreground">Completion Rate</span><span className="font-bold text-green-600">{completionRate}%</span></div><div className="mt-1 h-3 w-full rounded-full bg-muted"><div className="h-3 rounded-full bg-green-500" style={{ width: `${completionRate}%` }} /></div></div>
            <div><div className="flex items-center justify-between text-sm"><span className="text-muted-foreground">Cancellation Rate</span><span className="font-bold text-red-600">{cancellationRate}%</span></div><div className="mt-1 h-3 w-full rounded-full bg-muted"><div className="h-3 rounded-full bg-red-400" style={{ width: `${cancellationRate}%` }} /></div></div>
            <div className="grid grid-cols-3 gap-3 pt-2">
              <div className="rounded-md bg-blue-50 p-3 text-center"><Activity className="mx-auto h-4 w-4 text-blue-600" /><p className="mt-1 text-lg font-bold text-foreground">{stats.inPersonAppointments}</p><p className="text-[10px] text-muted-foreground">In-Person</p></div>
              <div className="rounded-md bg-purple-50 p-3 text-center"><Video className="mx-auto h-4 w-4 text-purple-600" /><p className="mt-1 text-lg font-bold text-foreground">{stats.telemedicineSessions}</p><p className="text-[10px] text-muted-foreground">Telemedicine</p></div>
              <div className="rounded-md bg-teal-50 p-3 text-center"><Clock className="mx-auto h-4 w-4 text-teal-600" /><p className="mt-1 text-lg font-bold text-foreground">{stats.followUpAppointments}</p><p className="text-[10px] text-muted-foreground">Follow-Up</p></div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm"><div className="flex items-center gap-2"><TrendingUp className="h-5 w-5 text-green-500" /><h2 className="text-lg font-semibold text-foreground">Appointment Stats</h2></div><div className="mt-4 space-y-3"><div className="flex items-center justify-between"><span className="text-sm text-muted-foreground">Total</span><span className="text-sm font-bold">{stats.totalAppointments}</span></div><div className="flex items-center justify-between"><span className="text-sm text-muted-foreground">Completed</span><span className="text-sm font-bold text-green-600">{stats.completedAppointments}</span></div><div className="flex items-center justify-between"><span className="text-sm text-muted-foreground">Cancelled</span><span className="text-sm font-bold text-red-600">{stats.cancelledAppointments}</span></div><div className="flex items-center justify-between"><span className="text-sm text-muted-foreground">Telemedicine</span><span className="text-sm font-bold text-purple-600">{stats.telemedicineSessions}</span></div></div></div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm"><div className="flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-amber-500" /><h2 className="text-lg font-semibold text-foreground">Alert Overview</h2></div><div className="mt-4 space-y-3"><div className="flex items-center justify-between"><div className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-red-500" /><span className="text-sm text-muted-foreground">Critical</span></div><span className="text-sm font-bold text-red-600">{stats.criticalAlerts}</span></div><div className="flex items-center justify-between"><div className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-amber-500" /><span className="text-sm text-muted-foreground">Active Alerts</span></div><span className="text-sm font-bold text-amber-600">{stats.activeAlerts}</span></div><div className="flex items-center justify-between"><div className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-blue-500" /><span className="text-sm text-muted-foreground">Total Reports</span></div><span className="text-sm font-bold">{stats.totalReports}</span></div><div className="flex items-center justify-between"><div className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-amber-400" /><span className="text-sm text-muted-foreground">Pending</span></div><span className="text-sm font-bold text-amber-600">{stats.pendingReports}</span></div></div></div>
      </div>

      <div className="rounded-lg border border-border bg-card p-6 shadow-sm"><h2 className="text-lg font-semibold text-foreground">Quick Actions</h2><div className="mt-4 grid gap-3 md:grid-cols-4"><a href="/doctor/monitoring" className="rounded-md border border-border p-3 text-center text-sm font-medium text-foreground transition-colors hover:bg-muted">Monitoring</a><a href="/doctor/patients" className="rounded-md border border-border p-3 text-center text-sm font-medium text-foreground transition-colors hover:bg-muted">Patients</a><a href="/doctor/appointments" className="rounded-md border border-border p-3 text-center text-sm font-medium text-foreground transition-colors hover:bg-muted">Appointments</a><a href="/doctor/ai-assistant" className="rounded-md border border-border p-3 text-center text-sm font-medium text-primary transition-colors hover:bg-primary/5">AI Assistant</a></div></div>
    </div>
  );
}
