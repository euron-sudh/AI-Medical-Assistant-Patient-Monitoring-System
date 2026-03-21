"use client";

import { useState, useEffect } from "react";
import apiClient from "@/lib/api-client";

interface Appointment {
  id: string;
  patient_name: string;
  doctor_name: string;
  appointment_type: string;
  status: string;
  scheduled_at: string;
  duration_minutes: number;
  reason: string | null;
}

const STATUS_STYLES: Record<string, string> = {
  scheduled: "bg-blue-50 text-blue-700",
  confirmed: "bg-green-50 text-green-700",
  in_progress: "bg-amber-50 text-amber-700",
  completed: "bg-gray-50 text-gray-600",
  cancelled: "bg-red-50 text-red-600",
};

export default function TelemedicinePage() {
  const [sessions, setSessions] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTelemedicine();
  }, []);

  const fetchTelemedicine = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get("/appointments");
      const data = res.data.appointments ?? res.data ?? [];
      const all = Array.isArray(data) ? data : [];
      // Filter for telemedicine appointments
      const teleAppts = all.filter(
        (a: Appointment) => a.appointment_type === "telemedicine"
      );
      setSessions(teleAppts);
      setError(null);
    } catch {
      setError("Failed to load telemedicine sessions.");
    } finally {
      setLoading(false);
    }
  };

  const now = new Date();
  const upcoming = sessions
    .filter((s) => new Date(s.scheduled_at) > now && s.status !== "cancelled" && s.status !== "completed")
    .sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime());
  const past = sessions
    .filter((s) => new Date(s.scheduled_at) <= now || s.status === "completed" || s.status === "cancelled")
    .sort((a, b) => new Date(b.scheduled_at).getTime() - new Date(a.scheduled_at).getTime());

  const getTimeUntil = (dateStr: string): string => {
    const diff = new Date(dateStr).getTime() - now.getTime();
    if (diff < 0) return "Past";
    const hours = Math.floor(diff / 3600000);
    const mins = Math.floor((diff % 3600000) / 60000);
    if (hours > 24) return `${Math.floor(hours / 24)}d ${hours % 24}h`;
    if (hours > 0) return `${hours}h ${mins}m`;
    return `${mins}m`;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Telemedicine</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Conduct video consultations with patients via secure WebRTC connections.
        </p>
      </div>

      {/* Summary */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Upcoming Sessions</p>
          <p className="mt-2 text-3xl font-bold text-primary">{upcoming.length}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Completed Sessions</p>
          <p className="mt-2 text-3xl font-bold text-green-600">
            {past.filter((s) => s.status === "completed").length}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Total Sessions</p>
          <p className="mt-2 text-3xl font-bold text-foreground">{sessions.length}</p>
        </div>
      </div>

      {/* Features info */}
      <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
        <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
            HD video via Daily.co WebRTC
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
            Screen sharing
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
            Real-time AI transcription
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
            Post-call SOAP notes
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
            AI assistant sidebar
          </span>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <span className="ml-3 text-sm text-muted-foreground">Loading sessions...</span>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
          <p className="text-sm text-destructive">{error}</p>
          <button onClick={fetchTelemedicine} className="mt-2 text-sm font-medium text-primary hover:underline">
            Retry
          </button>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* Upcoming Sessions */}
          <div className="rounded-lg border border-border bg-card shadow-sm">
            <div className="border-b border-border px-6 py-4">
              <h2 className="text-lg font-semibold text-foreground">
                Upcoming Sessions ({upcoming.length})
              </h2>
            </div>
            {upcoming.length === 0 ? (
              <div className="px-6 py-8 text-center text-sm text-muted-foreground">
                No upcoming telemedicine sessions. Sessions will appear when patients book telemedicine appointments.
              </div>
            ) : (
              <div className="divide-y divide-border">
                {upcoming.map((s) => (
                  <div key={s.id} className="flex items-center justify-between px-6 py-4">
                    <div className="flex items-center gap-4">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-100">
                        <span className="text-sm font-bold text-purple-700">
                          {(s.patient_name ?? "?")[0]}
                        </span>
                      </div>
                      <div>
                        <p className="font-medium text-foreground">{s.patient_name ?? "Unknown"}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(s.scheduled_at).toLocaleString()} ({s.duration_minutes ?? 30} min)
                        </p>
                        {s.reason && (
                          <p className="mt-0.5 text-xs text-muted-foreground">Reason: {s.reason}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-medium text-muted-foreground">
                        Starts in {getTimeUntil(s.scheduled_at)}
                      </span>
                      <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[s.status] ?? "bg-gray-100 text-gray-700"}`}>
                        {s.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Past Sessions */}
          {past.length > 0 && (
            <div className="rounded-lg border border-border bg-card shadow-sm">
              <div className="border-b border-border px-6 py-4">
                <h2 className="text-lg font-semibold text-foreground">
                  Past Sessions ({past.length})
                </h2>
              </div>
              <div className="divide-y divide-border">
                {past.slice(0, 15).map((s) => (
                  <div key={s.id} className="flex items-center justify-between px-6 py-3 text-sm">
                    <span className="font-medium text-foreground">{s.patient_name ?? "Unknown"}</span>
                    <span className="text-muted-foreground">
                      {new Date(s.scheduled_at).toLocaleDateString()}
                    </span>
                    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[s.status] ?? "bg-gray-100 text-gray-700"}`}>
                      {s.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
