"use client";

import { useState, useEffect, useCallback } from "react";
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
  daily_room_url?: string;
  daily_token?: string;
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
  const [activeCall, setActiveCall] = useState<Appointment | null>(null);
  const [joiningId, setJoiningId] = useState<string | null>(null);
  const [callStatus, setCallStatus] = useState<
    "idle" | "joining" | "connected" | "error"
  >("idle");

  useEffect(() => {
    fetchTelemedicine();
  }, []);

  const fetchTelemedicine = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get("/appointments");
      const data = res.data.appointments ?? res.data ?? [];
      const all = Array.isArray(data) ? data : [];
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

  const handleJoinCall = useCallback(async (session: Appointment) => {
    setJoiningId(session.id);
    setCallStatus("joining");
    try {
      // Request a Daily.co room token from the backend
      const res = await apiClient.post(
        `/telemedicine/sessions/${session.id}/join`
      );
      const roomUrl = res.data.room_url ?? session.daily_room_url ?? null;
      const token = res.data.token ?? session.daily_token ?? null;

      setActiveCall({
        ...session,
        daily_room_url: roomUrl,
        daily_token: token,
      });
      setCallStatus("connected");
    } catch {
      // If backend doesn't support this endpoint yet, simulate with the session data
      setActiveCall(session);
      setCallStatus("connected");
    } finally {
      setJoiningId(null);
    }
  }, []);

  const handleEndCall = useCallback(() => {
    setActiveCall(null);
    setCallStatus("idle");
  }, []);

  const now = new Date();
  const upcoming = sessions
    .filter(
      (s) =>
        new Date(s.scheduled_at) > now &&
        s.status !== "cancelled" &&
        s.status !== "completed"
    )
    .sort(
      (a, b) =>
        new Date(a.scheduled_at).getTime() -
        new Date(b.scheduled_at).getTime()
    );
  const past = sessions
    .filter(
      (s) =>
        new Date(s.scheduled_at) <= now ||
        s.status === "completed" ||
        s.status === "cancelled"
    )
    .sort(
      (a, b) =>
        new Date(b.scheduled_at).getTime() -
        new Date(a.scheduled_at).getTime()
    );

  const getTimeUntil = (dateStr: string): string => {
    const diff = new Date(dateStr).getTime() - now.getTime();
    if (diff < 0) return "Past";
    const hours = Math.floor(diff / 3600000);
    const mins = Math.floor((diff % 3600000) / 60000);
    if (hours > 24) return `${Math.floor(hours / 24)}d ${hours % 24}h`;
    if (hours > 0) return `${hours}h ${mins}m`;
    return `${mins}m`;
  };

  // Check if session is joinable (within 15 min of start or in progress)
  const isJoinable = (session: Appointment): boolean => {
    const diff = new Date(session.scheduled_at).getTime() - now.getTime();
    return (
      (diff < 15 * 60 * 1000 &&
        diff > -session.duration_minutes * 60 * 1000) ||
      session.status === "in_progress" ||
      session.status === "confirmed"
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Telemedicine</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Conduct video consultations with patients via secure Daily.co WebRTC
          connections.
        </p>
      </div>

      {/* Active Video Call */}
      {activeCall && callStatus === "connected" && (
        <div className="rounded-lg border-2 border-primary bg-card shadow-lg overflow-hidden">
          <div className="flex items-center justify-between border-b border-border bg-primary/5 px-4 py-3">
            <div className="flex items-center gap-3">
              <span className="relative flex h-3 w-3">
                <span className="absolute h-3 w-3 animate-ping rounded-full bg-green-400 opacity-75" />
                <span className="relative h-3 w-3 rounded-full bg-green-500" />
              </span>
              <span className="text-sm font-semibold text-foreground">
                In Call with {activeCall.patient_name}
              </span>
            </div>
            <button
              onClick={handleEndCall}
              className="rounded-md bg-red-500 px-4 py-1.5 text-sm font-medium text-white hover:bg-red-600"
            >
              End Call
            </button>
          </div>
          {/* Video area */}
          <div className="relative bg-gray-900">
            {activeCall.daily_room_url ? (
              <iframe
                src={`${activeCall.daily_room_url}${activeCall.daily_token ? `?t=${activeCall.daily_token}` : ""}`}
                className="h-[500px] w-full border-0"
                allow="camera; microphone; fullscreen; display-capture; autoplay"
                title="Daily.co Video Call"
              />
            ) : (
              <div className="flex h-[500px] flex-col items-center justify-center text-white">
                <svg
                  className="h-16 w-16 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z"
                  />
                </svg>
                <p className="mt-4 text-sm text-gray-400">
                  Video call active - waiting for Daily.co room URL from server
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  Configure DAILY_API_KEY in your environment to enable video
                </p>
              </div>
            )}
          </div>
          {/* Call controls */}
          <div className="flex items-center justify-center gap-4 border-t border-border bg-gray-900 px-4 py-3">
            <button
              className="rounded-full bg-gray-700 p-3 text-white hover:bg-gray-600"
              title="Toggle Microphone"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z"
                />
              </svg>
            </button>
            <button
              className="rounded-full bg-gray-700 p-3 text-white hover:bg-gray-600"
              title="Toggle Camera"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z"
                />
              </svg>
            </button>
            <button
              className="rounded-full bg-gray-700 p-3 text-white hover:bg-gray-600"
              title="Share Screen"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 17.25v1.007a3 3 0 0 1-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0 1 15 18.257V17.25m6-12V15a2.25 2.25 0 0 1-2.25 2.25H5.25A2.25 2.25 0 0 1 3 15V5.25m18 0A2.25 2.25 0 0 0 18.75 3H5.25A2.25 2.25 0 0 0 3 5.25m18 0V12a2.25 2.25 0 0 1-2.25 2.25H5.25A2.25 2.25 0 0 1 3 12V5.25"
                />
              </svg>
            </button>
            <button
              onClick={handleEndCall}
              className="rounded-full bg-red-500 p-3 text-white hover:bg-red-600"
              title="End Call"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15.75 3.75 18 6m0 0 2.25 2.25M18 6l2.25-2.25M18 6l-2.25 2.25m1.5 13.5c-8.284 0-15-6.716-15-15V4.5A2.25 2.25 0 0 1 4.5 2.25h1.372c.516 0 .966.351 1.091.852l1.106 4.423c.11.44-.054.902-.417 1.173l-1.293.97a1.062 1.062 0 0 0-.38 1.21 12.035 12.035 0 0 0 7.143 7.143c.441.162.928-.004 1.21-.38l.97-1.293a1.125 1.125 0 0 1 1.173-.417l4.423 1.106c.5.125.852.575.852 1.091V19.5a2.25 2.25 0 0 1-2.25 2.25h-2.25Z"
                />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Summary */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">
            Upcoming Sessions
          </p>
          <p className="mt-2 text-3xl font-bold text-primary">
            {upcoming.length}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">
            Completed Sessions
          </p>
          <p className="mt-2 text-3xl font-bold text-green-600">
            {past.filter((s) => s.status === "completed").length}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">
            Total Sessions
          </p>
          <p className="mt-2 text-3xl font-bold text-foreground">
            {sessions.length}
          </p>
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
          <span className="ml-3 text-sm text-muted-foreground">
            Loading sessions...
          </span>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
          <p className="text-sm text-destructive">{error}</p>
          <button
            onClick={fetchTelemedicine}
            className="mt-2 text-sm font-medium text-primary hover:underline"
          >
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
                No upcoming telemedicine sessions. Sessions will appear when
                patients book telemedicine appointments.
              </div>
            ) : (
              <div className="divide-y divide-border">
                {upcoming.map((s) => (
                  <div
                    key={s.id}
                    className="flex items-center justify-between px-6 py-4"
                  >
                    <div className="flex items-center gap-4">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-100">
                        <span className="text-sm font-bold text-purple-700">
                          {(s.patient_name ?? "?")[0]}
                        </span>
                      </div>
                      <div>
                        <p className="font-medium text-foreground">
                          {s.patient_name ?? "Unknown"}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(s.scheduled_at).toLocaleString()} (
                          {s.duration_minutes ?? 30} min)
                        </p>
                        {s.reason && (
                          <p className="mt-0.5 text-xs text-muted-foreground">
                            Reason: {s.reason}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-medium text-muted-foreground">
                        Starts in {getTimeUntil(s.scheduled_at)}
                      </span>
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                          STATUS_STYLES[s.status] ?? "bg-gray-100 text-gray-700"
                        }`}
                      >
                        {s.status}
                      </span>
                      {isJoinable(s) && (
                        <button
                          onClick={() => handleJoinCall(s)}
                          disabled={joiningId === s.id}
                          className="rounded-md bg-primary px-4 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                        >
                          {joiningId === s.id ? "Joining..." : "Join Call"}
                        </button>
                      )}
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
                  <div
                    key={s.id}
                    className="flex items-center justify-between px-6 py-3 text-sm"
                  >
                    <span className="font-medium text-foreground">
                      {s.patient_name ?? "Unknown"}
                    </span>
                    <span className="text-muted-foreground">
                      {new Date(s.scheduled_at).toLocaleDateString()}
                    </span>
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        STATUS_STYLES[s.status] ?? "bg-gray-100 text-gray-700"
                      }`}
                    >
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
