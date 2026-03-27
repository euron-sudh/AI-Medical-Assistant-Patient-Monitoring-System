"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  ArrowRight,
  Calendar,
  Check,
  ChevronRight,
  ClipboardList,
  FileText,
  Pill,
  Sparkles,
  Stethoscope,
} from "lucide-react";
import apiClient from "@/lib/api-client";
import type { User } from "@/types/auth";
import JourneyTracker from "@/components/shared/JourneyTracker";

const JOURNEY_STORAGE_STEP = "medassist_journey_step";
const JOURNEY_STORAGE_SPECIALTY = "medassist_specialty";

const JOURNEY_STEPS = [
  "Select Specialty",
  "Describe Symptoms",
  "Tests Recommended",
  "Upload Reports",
  "AI Analysis",
  "Advice/Referral",
] as const;

const MEDICAL_SPECIALTIES: { value: string; label: string }[] = [
  { value: "primary_care", label: "Primary Care" },
  { value: "cardiology", label: "Cardiology" },
  { value: "dermatology", label: "Dermatology" },
  { value: "neurology", label: "Neurology" },
  { value: "orthopedics", label: "Orthopedics" },
  { value: "pediatrics", label: "Pediatrics" },
  { value: "psychiatry", label: "Psychiatry" },
  { value: "gastroenterology", label: "Gastroenterology" },
  { value: "endocrinology", label: "Endocrinology" },
  { value: "pulmonology", label: "Pulmonology" },
  { value: "emergency", label: "Urgent / Emergency" },
];

interface SymptomSessionRow {
  id: string;
  status: string;
  chief_complaint?: string | null;
  ai_analysis?: Record<string, unknown> | null;
  recommended_action?: string | null;
  conversation_log?: unknown;
  created_at?: string;
  updated_at?: string;
}

interface MedicationRow {
  id: string;
  drug_name?: string;
  name?: string;
  dosage: string;
  frequency: string;
  status: string;
}

interface AppointmentRow {
  id: string;
  scheduled_at: string;
  status: string;
  doctor_name?: string;
  doctor?: { first_name?: string; last_name?: string; name?: string };
  appointment_type?: string;
}

interface VitalsRow {
  heart_rate?: number | null;
  blood_pressure_systolic?: number | null;
  blood_pressure_diastolic?: number | null;
  oxygen_saturation?: number | null;
  spo2?: number | null;
  temperature?: number | null;
  recorded_at?: string;
}

interface ReportRow {
  id: string;
  title: string;
  ai_summary?: string | null;
  status?: string;
  created_at?: string;
}

function getPatientId(user: User | null): string | null {
  if (!user) return null;
  return user.id;
}

function conversationLogLength(log: unknown): number {
  if (Array.isArray(log)) return log.length;
  if (log && typeof log === "object" && "messages" in log) {
    const m = (log as { messages?: unknown }).messages;
    if (Array.isArray(m)) return m.length;
  }
  return 0;
}

/** Maps an in-progress session to a journey index (0–5) for display labels. */
function sessionStageIndex(s: SymptomSessionRow): number {
  if (s.status === "completed") return 5;
  const hasAnalysis =
    s.ai_analysis != null && Object.keys(s.ai_analysis as object).length > 0;
  if (hasAnalysis) return 4;
  if (s.recommended_action) return 2;
  if (conversationLogLength(s.conversation_log) > 2) return 2;
  return 1;
}

function sessionStageLabel(s: SymptomSessionRow): string {
  const idx = sessionStageIndex(s);
  return JOURNEY_STEPS[idx] ?? "In progress";
}

function readStoredJourneyStep(): number {
  if (typeof window === "undefined") return 0;
  const raw = localStorage.getItem(JOURNEY_STORAGE_STEP);
  const n = raw ? parseInt(raw, 10) : 0;
  if (Number.isNaN(n) || n < 0) return 0;
  return Math.min(n, 5);
}

export default function PatientDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [specialtyModalOpen, setSpecialtyModalOpen] = useState(false);
  const [journeyStep, setJourneyStep] = useState(0);

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (stored) {
      try {
        setUser(JSON.parse(stored) as User);
      } catch {
        setUser(null);
      }
    }
  }, []);

  const patientId = getPatientId(user);

  useEffect(() => {
    setJourneyStep(readStoredJourneyStep());
  }, []);

  const syncJourneyFromSessions = useCallback((sessions: SymptomSessionRow[]) => {
    const active = sessions.filter((s) => s.status === "in_progress");
    let maxInf = 0;
    for (const s of active) {
      maxInf = Math.max(maxInf, sessionStageIndex(s));
    }
    const stored = readStoredJourneyStep();
    const merged = Math.max(stored, maxInf, localStorage.getItem(JOURNEY_STORAGE_SPECIALTY) ? 1 : 0);
    setJourneyStep(merged);
  }, []);

  const {
    data: symptomSessions = [],
    isLoading: loadingSessions,
  } = useQuery({
    queryKey: ["patient-dashboard-symptoms", patientId],
    queryFn: async (): Promise<SymptomSessionRow[]> => {
      const res = await apiClient.get(`/symptoms/history/${patientId}`);
      const raw = res.data;
      return Array.isArray(raw) ? raw : [];
    },
    enabled: !!patientId,
  });

  useEffect(() => {
    if (symptomSessions.length) syncJourneyFromSessions(symptomSessions);
  }, [symptomSessions, syncJourneyFromSessions]);

  const activeConsultations = useMemo(
    () => symptomSessions.filter((s) => s.status === "in_progress"),
    [symptomSessions]
  );

  const {
    data: medications = [],
    isLoading: loadingMeds,
  } = useQuery({
    queryKey: ["patient-dashboard-meds", patientId],
    queryFn: async (): Promise<MedicationRow[]> => {
      const res = await apiClient.get(`/medications/${patientId}`);
      const data = res.data?.medications ?? res.data;
      return Array.isArray(data) ? data : [];
    },
    enabled: !!patientId,
  });

  const { data: appointments = [], isLoading: loadingAppts } = useQuery({
    queryKey: ["patient-dashboard-appointments"],
    queryFn: async (): Promise<AppointmentRow[]> => {
      const res = await apiClient.get("/appointments");
      const data = res.data?.appointments ?? res.data;
      return Array.isArray(data) ? data : [];
    },
  });

  const { data: vitalsList = [], isLoading: loadingVitals } = useQuery({
    queryKey: ["patient-dashboard-vitals", patientId],
    queryFn: async (): Promise<VitalsRow[]> => {
      const res = await apiClient.get(`/vitals/${patientId}`);
      const data = res.data?.vitals ?? res.data?.readings ?? res.data;
      return Array.isArray(data) ? data : [];
    },
    enabled: !!patientId,
  });

  const { data: reports = [], isLoading: loadingReports } = useQuery({
    queryKey: ["patient-dashboard-reports", patientId],
    queryFn: async (): Promise<ReportRow[]> => {
      const res = await apiClient.get(`/reports/${patientId}`);
      const data = res.data?.reports ?? res.data;
      return Array.isArray(data) ? data : [];
    },
    enabled: !!patientId,
  });

  const loadingMain =
    !!patientId &&
    (loadingSessions || loadingMeds || loadingAppts || loadingVitals || loadingReports);

  const nextAppointment = useMemo(() => {
    const now = new Date();
    const upcoming = appointments.filter(
      (a) =>
        new Date(a.scheduled_at) >= now &&
        !["completed", "cancelled", "no_show"].includes(a.status)
    );
    upcoming.sort(
      (a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime()
    );
    return upcoming[0] ?? null;
  }, [appointments]);

  const latestVitals = vitalsList[0] ?? null;

  const activeMeds = useMemo(
    () => medications.filter((m) => m.status === "active"),
    [medications]
  );

  const medsDueTodayCount = useMemo(() => {
    return activeMeds.filter((m) => {
      const f = (m.frequency ?? "").toLowerCase();
      return (
        f.includes("daily") ||
        f.includes("once a day") ||
        f.includes("twice") ||
        f.includes("every day") ||
        f.includes("qd")
      );
    }).length;
  }, [activeMeds]);

  const recentSymptomResults = useMemo(() => {
    return symptomSessions
      .filter(
        (s) =>
          s.status === "completed" &&
          s.ai_analysis != null &&
          Object.keys(s.ai_analysis).length > 0
      )
      .slice(0, 3);
  }, [symptomSessions]);

  const recentReports = useMemo(() => {
    return [...reports]
      .sort(
        (a, b) =>
          new Date(b.created_at ?? 0).getTime() - new Date(a.created_at ?? 0).getTime()
      )
      .slice(0, 2);
  }, [reports]);

  const handleSelectSpecialty = (value: string) => {
    localStorage.setItem(JOURNEY_STORAGE_SPECIALTY, value);
    localStorage.setItem(JOURNEY_STORAGE_STEP, "1");
    setJourneyStep(1);
    setSpecialtyModalOpen(false);
    const q = new URLSearchParams({ specialty: value });
    router.push(`/patient/symptoms?${q.toString()}`);
  };

  const currentStepIndex = Math.min(Math.max(journeyStep, 0), 5);

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            Welcome{user ? `, ${user.first_name}` : ""}
          </h1>
          <p className="mt-1 text-muted-foreground">Your personal health dashboard</p>
        </div>
        <button
          type="button"
          onClick={() => setSpecialtyModalOpen(true)}
          className="inline-flex w-full shrink-0 items-center justify-center gap-2 rounded-lg bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary/90 sm:w-auto"
        >
          <Stethoscope className="h-5 w-5" aria-hidden />
          Start New Consultation
          <ChevronRight className="h-4 w-4 opacity-80" aria-hidden />
        </button>
      </div>

      {/* Patient Journey Tracker - Enhanced */}
      <JourneyTracker currentStep={currentStepIndex} loading={loadingMain} />

      {/* Quick stats */}
      <section aria-label="Quick stats">
        <h2 className="sr-only">Quick stats</h2>
        {loadingMain ? (
          <div className="grid gap-3 sm:grid-cols-3">
            <StatSkeleton />
            <StatSkeleton />
            <StatSkeleton />
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="flex items-start gap-3 rounded-lg border border-border bg-card p-4 shadow-sm">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300">
                <Calendar className="h-5 w-5" aria-hidden />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-muted-foreground">Next appointment</p>
                {nextAppointment ? (
                  <>
                    <p className="mt-0.5 truncate text-sm font-semibold text-foreground">
                      {new Date(nextAppointment.scheduled_at).toLocaleString(undefined, {
                        weekday: "short",
                        month: "short",
                        day: "numeric",
                        hour: "numeric",
                        minute: "2-digit",
                      })}
                    </p>
                    <Link
                      href="/patient/appointments"
                      className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                    >
                      View <ArrowRight className="h-3 w-3" />
                    </Link>
                  </>
                ) : (
                  <p className="mt-0.5 text-sm text-muted-foreground">None scheduled</p>
                )}
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-lg border border-border bg-card p-4 shadow-sm">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-200">
                <Pill className="h-5 w-5" aria-hidden />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-muted-foreground">Medications due today</p>
                <p className="mt-0.5 text-lg font-bold tabular-nums text-foreground">
                  {medsDueTodayCount > 0 ? medsDueTodayCount : activeMeds.length}
                </p>
                <p className="text-xs text-muted-foreground">
                  {activeMeds.length} active total
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-lg border border-border bg-card p-4 shadow-sm">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-200">
                <Activity className="h-5 w-5" aria-hidden />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-muted-foreground">Latest vitals</p>
                {latestVitals ? (
                  <>
                    <p className="mt-0.5 text-sm font-semibold text-foreground">
                      {[
                        latestVitals.heart_rate != null
                          ? `HR ${latestVitals.heart_rate}`
                          : null,
                        latestVitals.blood_pressure_systolic != null
                          ? `BP ${latestVitals.blood_pressure_systolic}/${latestVitals.blood_pressure_diastolic ?? "—"}`
                          : null,
                        latestVitals.oxygen_saturation != null || latestVitals.spo2 != null
                          ? `SpO₂ ${latestVitals.oxygen_saturation ?? latestVitals.spo2}%`
                          : null,
                      ]
                        .filter(Boolean)
                        .join(" · ") || "Recorded"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {latestVitals.recorded_at
                        ? new Date(latestVitals.recorded_at).toLocaleString()
                        : ""}
                    </p>
                  </>
                ) : (
                  <p className="mt-0.5 text-sm text-muted-foreground">No readings yet</p>
                )}
                <Link
                  href="/patient/vitals"
                  className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                >
                  Log vitals <ArrowRight className="h-3 w-3" />
                </Link>
              </div>
            </div>
          </div>
        )}
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Active Consultations */}
        <section className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-2">
            <ClipboardList className="h-5 w-5 text-primary" aria-hidden />
            <h2 className="text-lg font-semibold text-foreground">Active Consultations</h2>
          </div>
          {loadingSessions ? (
            <div className="space-y-3">
              <div className="h-16 animate-pulse rounded-lg bg-muted" />
              <div className="h-16 animate-pulse rounded-lg bg-muted" />
            </div>
          ) : activeConsultations.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No consultations in progress. Start a new consultation to begin your journey.
            </p>
          ) : (
            <ul className="space-y-3">
              {activeConsultations.map((s) => (
                <li
                  key={s.id}
                  className="flex flex-col gap-2 rounded-lg border border-border p-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    <p className="font-medium text-foreground">
                      {s.chief_complaint?.trim() || "Symptom consultation"}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Stage:{" "}
                      <span className="font-medium text-foreground">{sessionStageLabel(s)}</span>
                    </p>
                  </div>
                  <Link
                    href={`/patient/symptoms?resume=${encodeURIComponent(s.id)}`}
                    className="inline-flex shrink-0 items-center justify-center gap-1 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
                  >
                    Continue
                    <ArrowRight className="h-4 w-4" aria-hidden />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* Recent Results */}
        <section className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" aria-hidden />
            <h2 className="text-lg font-semibold text-foreground">Recent Results</h2>
          </div>
          {loadingMain ? (
            <div className="space-y-3">
              <div className="h-14 animate-pulse rounded-lg bg-muted" />
              <div className="h-14 animate-pulse rounded-lg bg-muted" />
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  AI symptom analysis
                </p>
                {recentSymptomResults.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No completed analyses yet.</p>
                ) : (
                  <ul className="space-y-2">
                    {recentSymptomResults.map((s) => (
                      <li
                        key={s.id}
                        className="rounded-md border border-border bg-muted/40 px-3 py-2 text-sm"
                      >
                        <p className="font-medium text-foreground line-clamp-2">
                          {s.chief_complaint ?? "Consultation"}
                        </p>
                        {s.recommended_action && (
                          <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
                            {s.recommended_action}
                          </p>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div>
                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Medications
                </p>
                {activeMeds.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No active medications on file.</p>
                ) : (
                  <ul className="space-y-2">
                    {activeMeds.slice(0, 4).map((m) => (
                      <li
                        key={m.id}
                        className="flex items-center justify-between gap-2 rounded-md border border-border px-3 py-2 text-sm"
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
              </div>
              {recentReports.length > 0 && (
                <div>
                  <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Reports
                  </p>
                  <ul className="space-y-2">
                    {recentReports.map((r) => (
                      <li key={r.id}>
                        <Link
                          href="/patient/reports"
                          className="block rounded-md border border-border px-3 py-2 text-sm transition-colors hover:bg-muted/60"
                        >
                          <span className="font-medium text-foreground">{r.title}</span>
                          {r.ai_summary && (
                            <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                              {r.ai_summary}
                            </p>
                          )}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </section>
      </div>

      {/* Quick Actions — existing shortcuts retained */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-foreground">Quick Actions</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <a
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
          </a>
          <a
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
          </a>
          <a
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
          </a>
          <a
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
          </a>
        </div>
      </div>

      <div className="rounded-md border border-border bg-muted/50 px-4 py-3">
        <p className="text-xs text-muted-foreground">
          AI-generated content is for informational purposes only and is not a substitute for
          professional medical advice, diagnosis, or treatment. Always consult your healthcare
          provider.
        </p>
      </div>

      {specialtyModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-4 sm:items-center"
          role="dialog"
          aria-modal="true"
          aria-labelledby="specialty-modal-title"
        >
          <div className="max-h-[85vh] w-full max-w-lg overflow-hidden rounded-xl border border-border bg-card shadow-lg">
            <div className="border-b border-border px-5 py-4">
              <h3 id="specialty-modal-title" className="text-lg font-semibold text-foreground">
                Choose a specialty
              </h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Select a focus area for your consultation. You can describe symptoms next.
              </p>
            </div>
            <div className="max-h-[55vh] overflow-y-auto p-3 sm:p-4">
              <ul className="grid gap-2 sm:grid-cols-2">
                {MEDICAL_SPECIALTIES.map((sp) => (
                  <li key={sp.value}>
                    <button
                      type="button"
                      onClick={() => handleSelectSpecialty(sp.value)}
                      className="flex w-full items-center justify-between rounded-lg border border-border px-4 py-3 text-left text-sm font-medium text-foreground transition-colors hover:bg-accent"
                    >
                      {sp.label}
                      <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
                    </button>
                  </li>
                ))}
              </ul>
            </div>
            <div className="border-t border-border px-5 py-3">
              <button
                type="button"
                onClick={() => setSpecialtyModalOpen(false)}
                className="w-full rounded-md border border-input py-2 text-sm font-medium hover:bg-muted"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function JourneySkeleton() {
  return (
    <div className="flex animate-pulse gap-2">
      {JOURNEY_STEPS.map((s) => (
        <div key={s} className="flex flex-1 flex-col items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-muted" />
          <div className="h-3 w-full max-w-[72px] rounded bg-muted" />
        </div>
      ))}
    </div>
  );
}

function StatSkeleton() {
  return <div className="h-[88px] animate-pulse rounded-lg bg-muted" />;
}
