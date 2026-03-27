"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarPlus, ChevronDown, ChevronRight } from "lucide-react";
import apiClient from "@/lib/api-client";
import BookingFlow from "@/components/appointments/BookingFlow";
import ConfirmDialog from "@/components/shared/ConfirmDialog";

interface Appointment {
  id: string;
  patient_id: string;
  doctor_id: string;
  doctor_name?: string;
  doctor?: {
    first_name?: string;
    last_name?: string;
    name?: string;
    specialization?: string;
  };
  appointment_type: string;
  status: string;
  scheduled_at: string;
  duration_minutes: number;
  reason: string | null;
  notes: string | null;
  created_at: string;
}

const typeBadge: Record<string, string> = {
  in_person: "bg-blue-100 text-blue-800 dark:bg-blue-950/50 dark:text-blue-200",
  telemedicine: "bg-purple-100 text-purple-800 dark:bg-purple-950/50 dark:text-purple-200",
  follow_up: "bg-teal-100 text-teal-800 dark:bg-teal-950/50 dark:text-teal-200",
  emergency: "bg-red-100 text-red-800 dark:bg-red-950/50 dark:text-red-200",
};

const statusBadge: Record<string, string> = {
  scheduled: "bg-blue-100 text-blue-800",
  confirmed: "bg-green-100 text-green-800",
  in_progress: "bg-amber-100 text-amber-800",
  completed: "bg-gray-100 text-gray-800",
  cancelled: "bg-red-100 text-red-800",
  no_show: "bg-red-100 text-red-800",
};

function normalizeAppointments(data: unknown): Appointment[] {
  if (Array.isArray(data)) return data as Appointment[];
  if (data && typeof data === "object" && "appointments" in data) {
    const a = (data as { appointments?: unknown }).appointments;
    return Array.isArray(a) ? (a as Appointment[]) : [];
  }
  return [];
}

function getDoctorName(a: Appointment): string {
  if (a.doctor_name) return a.doctor_name;
  if (a.doctor) {
    if (a.doctor.name) return a.doctor.name;
    if (a.doctor.first_name) {
      return `Dr. ${a.doctor.first_name} ${a.doctor.last_name ?? ""}`.trim();
    }
    if (a.doctor.specialization) return `Dr. ${a.doctor.specialization}`;
  }
  return "Your provider";
}

function formatDateTime(dt: string): string {
  return new Date(dt).toLocaleString(undefined, {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function AppointmentsPage() {
  const queryClient = useQueryClient();
  const [bookingOpen, setBookingOpen] = useState(false);
  const [pastOpen, setPastOpen] = useState(false);
  const [cancelId, setCancelId] = useState<string | null>(null);

  const appointmentsQuery = useQuery({
    queryKey: ["appointments"],
    queryFn: async () => {
      const res = await apiClient.get("/appointments");
      return normalizeAppointments(res.data);
    },
  });

  const cancelMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.put(`/appointments/${id}/cancel`, {
        reason: "Cancelled by patient",
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["appointments"] });
      setCancelId(null);
    },
  });

  const appointments = appointmentsQuery.data ?? [];
  const now = useMemo(() => new Date(), []);

  const { upcoming, past } = useMemo(() => {
    const up: Appointment[] = [];
    const pa: Appointment[] = [];
    for (const a of appointments) {
      const t = new Date(a.scheduled_at).getTime();
      const ended =
        ["completed", "cancelled", "no_show"].includes(a.status) || t < now.getTime();
      if (ended) pa.push(a);
      else up.push(a);
    }
    up.sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime());
    pa.sort((a, b) => new Date(b.scheduled_at).getTime() - new Date(a.scheduled_at).getTime());
    return { upcoming: up, past: pa };
  }, [appointments, now]);

  const loading = appointmentsQuery.isLoading;
  const error = appointmentsQuery.error
    ? "Failed to load appointments."
    : null;

  const canCancel = (a: Appointment) =>
    ["scheduled", "confirmed"].includes(a.status) &&
    new Date(a.scheduled_at) >= now;

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Appointments</h1>
          <p className="mt-1 text-muted-foreground">
            View upcoming visits, history, and book with your care team.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setBookingOpen(true)}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary/90"
        >
          <CalendarPlus className="h-4 w-4" />
          Book Appointment
        </button>
      </div>

      <BookingFlow
        open={bookingOpen}
        onClose={() => setBookingOpen(false)}
        onBooked={() => {
          setBookingOpen(false);
        }}
      />

      {loading ? (
        <div className="rounded-lg border border-border bg-card p-12 text-center">
          <p className="text-sm text-muted-foreground">Loading appointments...</p>
        </div>
      ) : error ? (
        <div className="rounded-lg border border-border bg-card p-12 text-center">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      ) : (
        <>
          <section aria-label="Upcoming appointments">
            <h2 className="mb-3 text-lg font-semibold text-foreground">
              Upcoming ({upcoming.length})
            </h2>
            {upcoming.length === 0 ? (
              <div className="rounded-xl border border-dashed border-border bg-muted/20 px-6 py-12 text-center">
                <p className="text-sm font-medium text-foreground">
                  No upcoming appointments. Book one now!
                </p>
                <button
                  type="button"
                  onClick={() => setBookingOpen(true)}
                  className="mt-4 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
                >
                  <CalendarPlus className="h-4 w-4" />
                  Book Appointment
                </button>
              </div>
            ) : (
              <ul className="space-y-3">
                {upcoming.map((appt) => (
                  <li key={appt.id}>
                    <AppointmentCard
                      appt={appt}
                      doctorName={getDoctorName(appt)}
                      formatDateTime={formatDateTime}
                      onCancel={
                        canCancel(appt) ? () => setCancelId(appt.id) : undefined
                      }
                    />
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section aria-label="Past appointments">
            <button
              type="button"
              onClick={() => setPastOpen((o) => !o)}
              className="flex w-full items-center justify-between rounded-lg border border-border bg-card px-4 py-3 text-left shadow-sm transition-colors hover:bg-accent"
            >
              <span className="text-lg font-semibold text-foreground">
                Past appointments ({past.length})
              </span>
              {pastOpen ? (
                <ChevronDown className="h-5 w-5 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-5 w-5 text-muted-foreground" />
              )}
            </button>
            {pastOpen && (
              <div className="mt-3 space-y-3">
                {past.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No past appointments yet.</p>
                ) : (
                  past.map((appt) => (
                    <AppointmentCard
                      key={appt.id}
                      appt={appt}
                      doctorName={getDoctorName(appt)}
                      formatDateTime={formatDateTime}
                    />
                  ))
                )}
              </div>
            )}
          </section>
        </>
      )}

      <ConfirmDialog
        open={cancelId !== null}
        title="Cancel appointment?"
        description="This will cancel your scheduled visit. You can book a new appointment anytime."
        confirmLabel={cancelMutation.isPending ? "Cancelling..." : "Cancel appointment"}
        cancelLabel="Keep it"
        variant="danger"
        onCancel={() => setCancelId(null)}
        onConfirm={() => {
          if (cancelId) cancelMutation.mutate(cancelId);
        }}
      />
    </div>
  );
}

function AppointmentCard({
  appt,
  doctorName,
  formatDateTime,
  onCancel,
}: {
  appt: Appointment;
  doctorName: string;
  formatDateTime: (dt: string) => string;
  onCancel?: () => void;
}) {
  const typeLabel = appt.appointment_type.replace(/_/g, " ");
  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-foreground">{doctorName}</h3>
          {appt.doctor?.specialization && (
            <p className="text-xs text-muted-foreground">{appt.doctor.specialization}</p>
          )}
          <p className="mt-2 text-sm font-medium text-foreground">
            {formatDateTime(appt.scheduled_at)}
          </p>
          <p className="text-xs text-muted-foreground">
            Duration: {appt.duration_minutes} min
          </p>
          {appt.reason && (
            <p className="mt-2 text-sm text-muted-foreground">
              <span className="font-medium text-foreground">Reason:</span> {appt.reason}
            </p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2 sm:flex-col sm:items-end">
          <span
            className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${
              typeBadge[appt.appointment_type] ?? "bg-gray-100 text-gray-800"
            }`}
          >
            {typeLabel}
          </span>
          <span
            className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${
              statusBadge[appt.status] ?? "bg-gray-100 text-gray-800"
            }`}
          >
            {appt.status.replace("_", " ")}
          </span>
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="rounded-md border border-destructive/40 px-3 py-1.5 text-xs font-medium text-destructive hover:bg-destructive/10"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
