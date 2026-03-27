"use client";

import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Activity,
  ArrowRight,
  Calendar,
  Check,
  Circle,
  Pill,
  Sparkles,
  Stethoscope,
} from "lucide-react";
import apiClient from "@/lib/api-client";
import SpecialtySelector from "@/components/shared/SpecialtySelector";
import LoadingSkeleton from "@/components/shared/LoadingSkeleton";

interface UserInfo {
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  id?: string;
  patient_id?: string;
}

interface SymptomSession {
  id: string;
  status: string;
  chief_complaint?: string | null;
  initial_complaint?: string | null;
  ai_analysis?: Record<string, unknown> | null;
  recommended_action?: string | null;
  triage_level?: string | null;
  conversation_log?: unknown;
  created_at: string;
}

interface ReportRow {
  id: string;
  title: string;
  report_type: string;
  status: string;
  ai_summary?: string | null;
  ai_analysis?: Record<string, unknown> | null;
  created_at: string;
}

interface MedicationRow {
  id: string;
  drug_name?: string;
  name?: string;
  dosage: string;
  frequency: string;
  status: string;
}

interface VitalsReading {
  heart_rate: number | null;
  blood_pressure_systolic?: number | null;
  blood_pressure_diastolic?: number | null;
  spo2?: number | null;
  oxygen_saturation?: number | null;
  temperature?: number | null;
  recorded_at: string;
}

interface AppointmentRow {
  id: string;
  scheduled_at: string;
  status: string;
  doctor_name?: string;
  appointment_type?: string;
}

const JOURNEY_LABELS = [
  "Select Specialty",
  "Describe Symptoms",
  "Tests Recommended",
  "Upload Reports",
  "AI Analysis",
  "Advice / Referral",
] as const;

function parseConversationLen(log: unknown): number {
  if (Array.isArray(log)) return log.length;
  return 0;
}

function computeJourney(
  specialtyKey: string | null,
  sessions: SymptomSession[],
  reports: ReportRow[]
): { completed: boolean[]; currentIndex: number; allDone: boolean } {
  const completed = [false, false, false, false, false, false];

  const hasSpecialty = specialtyKey != null && specialtyKey.length > 0;
  const hasAnySession = sessions.length > 0;
  completed[0] = hasSpecialty || hasAnySession;

  const inProgress = sessions.some((s) => s.status === "in_progress");
  const hasCompleted = sessions.some((s) => s.status === "completed");
  const describeDone =
    inProgress ||
    hasCompleted ||
    sessions.some((s) => parseConversationLen(s.conversation_log) > 0 || !!s.chief_complaint);
  completed[1] = describeDone;

  const testsDone = sessions.some(
    (s) =>
      (s.ai_analysis != null && Object.keys(s.ai_analysis).length > 0) ||
      (s.recommended_action != null && s.recommended_action.length > 0) ||
      s.triage_level != null
  );
  completed[2] = testsDone;

  completed[3] = reports.length > 0;

  const analysisDone = reports.some(
    (r) => (r.ai_analysis != null && Object.keys(r.ai_analysis).length > 0) || r.status === "completed"
  );
  completed[4] = analysisDone;

  completed[5] = hasCompleted;

  let currentIndex = 0;
  for (let i = 0; i < 6; i += 1) {
    if (!completed[i]) {
      currentIndex = i;
      break;
    }
    currentIndex = i;
  }
  const allDone = completed.every(Boolean);
  if (allDone) {
    return { completed, currentIndex: 5, allDone: true };
  }
  return { completed, currentIndex, allDone: false };
}

function sessionStageLabel(s: SymptomSession): string {
  if (s.status === "completed") return "Advice / referral ready";
  if (s.ai_analysis && Object.keys(s.ai_analysis).length > 0) return "AI analysis";
  if (s.recommended_action) return "Recommendations";
  if (s.triage_level) return "Triage & tests";
  return "Describe symptoms";
}

function countMedsDueToday(meds: MedicationRow[]): number {
  return meds.filter(
    (m) =>
      m.status === "active" &&
      /daily|once|every day|each day|qd|bid|tid|qid|q\s*d|morning|evening|weekly/i.test(
        m.frequency ?? ""
      )
  ).length;
}

function formatVitalsSummary(v: VitalsReading | null): string {
  if (!v) return "No readings yet";
  const parts: string[] = [];
  if (v.heart_rate != null) parts.push(`HR ${v.heart_rate}`);
  const sys = v.blood_pressure_systolic;
  const dia = v.blood_pressure_diastolic;
  if (sys != null && dia != null) parts.push(`BP ${sys}/${dia}`);
  const o2 = v.spo2 ?? v.oxygen_saturation;
  if (o2 != null) parts.push(`SpO₂ ${o2}%`);
  if (v.temperature != null) parts.push(`${v.temperature}°C`);
  return parts.length > 0 ? parts.join(" · ") : "Recorded";
}

export default function PatientDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<UserInfo | null>(null);
  const [specialtyModalOpen, setSpecialtyModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [specialtyKey, setSpecialtyKey] = useState<string | null>(null);

  const [sessions, setSessions] = useState<SymptomSession[]>([]);
  const [reports, setReports] = useState<ReportRow[]>([]);
  const [medications, setMedications] = useState<MedicationRow[]>([]);
  const [vitalsLatest, setVitalsLatest] = useState<VitalsReading | null>(null);
  const [appointments, setAppointments] = useState<AppointmentRow[]>([]);

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (stored) {
      try {
        setUser(JSON.parse(stored) as UserInfo);
      } catch {
        setUser(null);
      }
    }
    setSpecialtyKey(
      typeof window !== "undefined" ? localStorage.getItem("medassist_specialty") : null
    );
  }, []);

  const patientId = user?.id ?? user?.patient_id ?? null;

  const loadDashboard = useCallback(async () => {
    if (!patientId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    const spec =
      typeof window !== "undefined" ? localStorage.getItem("medassist_specialty") : null;
    setSpecialtyKey(spec);

    const results = await Promise.allSettled([
      apiClient.get(`/symptoms/history/${patientId}`),
      apiClient.get(`/reports/${patientId}`, { params: { limit: 8 } }),
      apiClient.get(`/medications/${patientId}`),
      apiClient.get(`/vitals/${patientId}`, { params: { limit: 1 } }),
      apiClient.get("/appointments", { params: { limit: 30 } }),
    ]);

    const normArray = (data: unknown): unknown[] => {
      if (Array.isArray(data)) return data;
      if (data && typeof data === "object" && "sessions" in (data as object)) {
        const s = (data as { sessions?: unknown }).sessions;
        return Array.isArray(s) ? s : [];
      }
      if (data && typeof data === "object" && "appointments" in (data as object)) {
        const a = (data as { appointments?: unknown }).appointments;
        return Array.isArray(a) ? a : [];
      }
      return [];
    };

    if (results[0].status === "fulfilled") {
      const d = results[0].value.data;
      setSessions(normArray(d) as SymptomSession[]);
    } else {
      setSessions([]);
    }

    if (results[1].status === "fulfilled") {
      const d = results[1].value.data;
      setReports(normArray(d) as ReportRow[]);
    } else {
      setReports([]);
    }

    if (results[2].status === "fulfilled") {
      const d = results[2].value.data;
      const m = (d as { medications?: MedicationRow[] })?.medications ?? d;
      setMedications(Array.isArray(m) ? (m as MedicationRow[]) : []);
    } else {
      setMedications([]);
    }

    if (results[3].status === "fulfilled") {
      const d = results[3].value.data;
      const list = normArray(d) as VitalsReading[];
      setVitalsLatest(list[0] ?? null);
    } else {
      setVitalsLatest(null);
    }

    if (results[4].status === "fulfilled") {
      const d = results[4].value.data;
      setAppointments(normArray(d) as AppointmentRow[]);
    } else {
      setAppointments([]);
    }

    setLoading(false);
  }, [patientId]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const journey = useMemo(
    () => computeJourney(specialtyKey, sessions, reports),
    [specialtyKey, sessions, reports]
  );

  const activeSessions = useMemo(
    () => sessions.filter((s) => s.status === "in_progress"),
    [sessions]
  );

  const nextAppointment = useMemo(() => {
    const now = Date.now();
    const upcoming = appointments
      .filter(
        (a) =>
          a.status !== "cancelled" &&
          a.status !== "completed" &&
          new Date(a.scheduled_at).getTime() > now
      )
      .sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime());
    return upcoming[0] ?? null;
  }, [appointments]);

  const activeMeds = useMemo(
    () => medications.filter((m) => m.status === "active"),
    [medications]
  );
  const dueTodayCount = useMemo(() => countMedsDueToday(medications), [medications]);

  const recentReports = useMemo(() => {
    return [...reports]
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 3);
  }, [reports]);

  const recentMeds = useMemo(() => activeMeds.slice(0, 4), [activeMeds]);

  const handleSpecialtySelect = (id: string) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("medassist_specialty", id);
      localStorage.setItem("medassist_journey_step", "2");
    }
    setSpecialtyKey(id);
    setSpecialtyModalOpen(false);
    router.push(`/patient/symptoms?specialty=${encodeURIComponent(id)}`);
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            Welcome{user ? `, ${user.first_name}` : ""}
          </h1>
          <p className="mt-1 text-muted-foreground">Your personal health dashboard</p>
        </div>
        <button
          type="button"
          onClick={() => setSpecialtyModalOpen(true)}
          className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary/90 sm:w-auto"
        >
          <Stethoscope className="h-5 w-5 shrink-0" aria-hidden />
          Start New Consultation
          <ArrowRight className="h-4 w-4 shrink-0" aria-hidden />
        </button>
      </div>

      {/* Patient Journey Tracker */}
      <section
        className="rounded-xl border border-border bg-card p-4 shadow-sm sm:p-6"
        aria-label="Patient journey progress"
      >
        <div className="mb-4 flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-foreground sm:text-base">
            Patient Journey Tracker
          </h2>
          {journey.allDone && (
            <span className="flex items-center gap-1 text-xs font-medium text-emerald-600">
              <Check className="h-4 w-4" aria-hidden />
              Complete
            </span>
          )}
        </div>
        {loading ? (
          <div className="flex gap-2 overflow-x-auto pb-2">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="min-w-[100px] flex-1 animate-pulse">
                <div className="mx-auto h-8 w-8 rounded-full bg-muted" />
                <div className="mt-2 h-3 w-full rounded bg-muted" />
              </div>
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto pb-2">
            <div className="flex min-w-[600px] items-start sm:min-w-0">
              {JOURNEY_LABELS.map((label, index) => {
                const done = journey.completed[index];
                const isCurrent = !journey.allDone && index === journey.currentIndex;
                const future = !done && !isCurrent;

                return (
                  <Fragment key={label}>
                    {index > 0 && (
                      <div
                        className={`mt-4 h-0.5 min-w-[4px] flex-1 rounded ${
                          journey.completed[index - 1] ? "bg-emerald-500" : "bg-muted"
                        }`}
                        aria-hidden
                      />
                    )}
                    <div className="flex w-[72px] shrink-0 flex-col items-center text-center sm:w-24">
                      <div
                        className={`flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-semibold transition-colors ${
                          done
                            ? "border-emerald-500 bg-emerald-500 text-white"
                            : isCurrent
                            ? "border-primary bg-primary/10 text-primary"
                            : "border-muted bg-muted/60 text-muted-foreground"
                        }`}
                        aria-current={isCurrent ? "step" : undefined}
                      >
                        {done ? (
                          <Check className="h-4 w-4" strokeWidth={3} aria-hidden />
                        ) : isCurrent ? (
                          <Circle className="h-3 w-3 fill-primary text-primary" aria-hidden />
                        ) : (
                          <span className="text-[10px] text-muted-foreground">{index + 1}</span>
                        )}
                      </div>
                      <p
                        className={`mt-2 text-[10px] leading-tight sm:text-xs ${
                          future ? "text-muted-foreground" : "text-foreground"
                        } ${isCurrent ? "font-semibold text-primary" : ""}`}
                      >
                        {label}
                      </p>
                    </div>
                  </Fragment>
                );
              })}
            </div>
          </div>
        )}
      </section>

      {/* Quick stats */}
      <section aria-label="Quick stats">
        {loading ? (
          <div className="grid gap-4 sm:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <div
                key={i}
                className="rounded-lg border border-border bg-card p-4 shadow-sm"
              >
                <div className="animate-pulse space-y-2">
                  <div className="h-4 w-1/3 rounded bg-muted" />
                  <div className="h-6 w-2/3 rounded bg-muted" />
                  <div className="h-3 w-full rounded bg-muted" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-3">
            <Link
              href="/patient/telemedicine"
              className="rounded-lg border border-border bg-card p-4 shadow-sm transition-colors hover:bg-accent"
            >
              <div className="flex items-center gap-2 text-muted-foreground">
                <Calendar className="h-4 w-4 shrink-0" aria-hidden />
                <span className="text-xs font-medium uppercase tracking-wide">
                  Next appointment
                </span>
              </div>
              {nextAppointment ? (
                <>
                  <p className="mt-2 text-lg font-semibold text-foreground">
                    {new Date(nextAppointment.scheduled_at).toLocaleString(undefined, {
                      weekday: "short",
                      month: "short",
                      day: "numeric",
                      hour: "numeric",
                      minute: "2-digit",
                    })}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
                    {nextAppointment.doctor_name ?? "Your care team"} ·{" "}
                    {nextAppointment.appointment_type ?? "Visit"}
                  </p>
                </>
              ) : (
                <p className="mt-2 text-sm text-muted-foreground">No upcoming visits scheduled</p>
              )}
            </Link>

            <Link
              href="/patient/medications"
              className="rounded-lg border border-border bg-card p-4 shadow-sm transition-colors hover:bg-accent"
            >
              <div className="flex items-center gap-2 text-muted-foreground">
                <Pill className="h-4 w-4 shrink-0" aria-hidden />
                <span className="text-xs font-medium uppercase tracking-wide">
                  Medications today
                </span>
              </div>
              <p className="mt-2 text-lg font-semibold text-foreground">
                {dueTodayCount > 0 ? `${dueTodayCount} due` : activeMeds.length > 0 ? "Review" : "—"}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                {activeMeds.length} active · open schedule for doses
              </p>
            </Link>

            <Link
              href="/patient/vitals"
              className="rounded-lg border border-border bg-card p-4 shadow-sm transition-colors hover:bg-accent"
            >
              <div className="flex items-center gap-2 text-muted-foreground">
                <Activity className="h-4 w-4 shrink-0" aria-hidden />
                <span className="text-xs font-medium uppercase tracking-wide">
                  Latest vitals
                </span>
              </div>
              <p className="mt-2 text-sm font-semibold leading-snug text-foreground">
                {formatVitalsSummary(vitalsLatest)}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                {vitalsLatest
                  ? new Date(vitalsLatest.recorded_at).toLocaleString()
                  : "Log a reading to track trends"}
              </p>
            </Link>
          </div>
        )}
      </section>

      {/* Active consultations */}
      <section aria-label="Active consultations">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">Active Consultations</h2>
        </div>
        {loading ? (
          <LoadingSkeleton rows={2} variant="card" />
        ) : activeSessions.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border bg-muted/30 px-4 py-8 text-center text-sm text-muted-foreground">
            No symptom sessions in progress. Start a new consultation to begin.
          </div>
        ) : (
          <ul className="space-y-3">
            {activeSessions.map((s) => {
              const title = s.chief_complaint ?? "Symptom consultation";
              return (
                <li
                  key={s.id}
                  className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-foreground line-clamp-2">{title}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Stage:{" "}
                      <span className="font-medium text-foreground">{sessionStageLabel(s)}</span>
                      {" · "}
                      Started {new Date(s.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Link
                    href={`/patient/symptoms?resume=${encodeURIComponent(s.id)}`}
                    className="inline-flex shrink-0 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
                  >
                    Continue
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {/* Recent results */}
      <section aria-label="Recent results">
        <h2 className="mb-3 text-lg font-semibold text-foreground">Recent Results</h2>
        {loading ? (
          <div className="grid gap-4 lg:grid-cols-2">
            <LoadingSkeleton rows={2} variant="card" />
            <LoadingSkeleton rows={2} variant="card" />
          </div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-lg border border-border bg-card p-5 shadow-sm">
              <div className="mb-3 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-amber-500" aria-hidden />
                <h3 className="text-sm font-semibold text-foreground">Latest AI analysis</h3>
              </div>
              {recentReports.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No reports yet.{" "}
                  <Link href="/patient/reports" className="font-medium text-primary underline">
                    Upload a report
                  </Link>{" "}
                  for AI interpretation.
                </p>
              ) : (
                <ul className="space-y-3">
                  {recentReports.map((r) => (
                    <li key={r.id} className="border-b border-border pb-3 last:border-0 last:pb-0">
                      <Link
                        href="/patient/reports"
                        className="group block font-medium text-foreground hover:text-primary"
                      >
                        <span className="line-clamp-1">{r.title}</span>
                        <span className="ml-2 text-xs font-normal text-muted-foreground">
                          {r.report_type}
                        </span>
                      </Link>
                      <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                        {r.ai_summary ?? "Analysis pending or in progress."}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="rounded-lg border border-border bg-card p-5 shadow-sm">
              <div className="mb-3 flex items-center gap-2">
                <Pill className="h-4 w-4 text-primary" aria-hidden />
                <h3 className="text-sm font-semibold text-foreground">Medications</h3>
              </div>
              {recentMeds.length === 0 ? (
                <p className="text-sm text-muted-foreground">No active medications on file.</p>
              ) : (
                <ul className="space-y-2">
                  {recentMeds.map((m) => (
                    <li
                      key={m.id}
                      className="flex items-start justify-between gap-2 text-sm"
                    >
                      <span className="font-medium text-foreground">
                        {m.drug_name ?? m.name ?? "Medication"}
                      </span>
                      <span className="shrink-0 text-xs text-muted-foreground">
                        {m.dosage} · {m.frequency}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              <Link
                href="/patient/medications"
                className="mt-4 inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
              >
                View all medications
                <ArrowRight className="h-3 w-3" aria-hidden />
              </Link>
            </div>
          </div>
        )}
      </section>

      {/* Quick actions (existing pattern) */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-foreground">Quick Actions</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Link
            href="/patient/symptoms"
            className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 shadow-sm transition-colors hover:bg-accent"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 text-sm font-bold text-primary">
              S
            </span>
            <div>
              <p className="text-sm font-medium text-foreground">Check Symptoms</p>
              <p className="text-xs text-muted-foreground">AI-powered analysis</p>
            </div>
          </Link>
          <Link
            href="/patient/vitals"
            className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 shadow-sm transition-colors hover:bg-accent"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-green-100 text-sm font-bold text-green-600">
              V
            </span>
            <div>
              <p className="text-sm font-medium text-foreground">Log Vitals</p>
              <p className="text-xs text-muted-foreground">Record your readings</p>
            </div>
          </Link>
          <Link
            href="/patient/reports"
            className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 shadow-sm transition-colors hover:bg-accent"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-orange-100 text-sm font-bold text-orange-600">
              R
            </span>
            <div>
              <p className="text-sm font-medium text-foreground">View Reports</p>
              <p className="text-xs text-muted-foreground">Medical reports & labs</p>
            </div>
          </Link>
          <Link
            href="/patient/chat"
            className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 shadow-sm transition-colors hover:bg-accent"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-blue-100 text-sm font-bold text-blue-600">
              C
            </span>
            <div>
              <p className="text-sm font-medium text-foreground">AI Chat</p>
              <p className="text-xs text-muted-foreground">Ask a health question</p>
            </div>
          </Link>
        </div>
      </div>

      <div className="rounded-md border border-border bg-muted/50 px-4 py-3">
        <p className="text-xs text-muted-foreground">
          AI-generated content is for informational purposes only and is not a substitute for
          professional medical advice, diagnosis, or treatment. Always consult your healthcare
          provider.
        </p>
      </div>

      {/* Specialty modal */}
      {specialtyModalOpen && (
        <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
          <button
            type="button"
            className="absolute inset-0 bg-black/50"
            aria-label="Close dialog"
            onClick={() => setSpecialtyModalOpen(false)}
          />
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="specialty-modal-title"
            className="relative z-10 max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-t-2xl border border-border bg-card p-4 shadow-xl sm:rounded-2xl sm:p-6"
          >
            <div className="mb-4 flex items-start justify-between gap-4">
              <div>
                <h2 id="specialty-modal-title" className="text-lg font-semibold text-foreground">
                  Choose a specialty
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  We will open the symptom assistant with this specialty context.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSpecialtyModalOpen(false)}
                className="rounded-md border border-border px-3 py-1.5 text-sm text-foreground hover:bg-muted"
              >
                Close
              </button>
            </div>
            <SpecialtySelector onSelect={handleSpecialtySelect} />
          </div>
        </div>
      )}
    </div>
  );
}
