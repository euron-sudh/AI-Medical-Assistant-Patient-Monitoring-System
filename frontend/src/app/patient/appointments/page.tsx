"use client";

import { useEffect, useState } from "react";
import { CalendarPlus } from "lucide-react";
import apiClient from "@/lib/api-client";
import BookingFlow from "@/components/appointments/BookingFlow";

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
  in_person: "bg-blue-100 text-blue-700",
  telemedicine: "bg-purple-100 text-purple-700",
  follow_up: "bg-teal-100 text-teal-700",
  emergency: "bg-red-100 text-red-700",
};

const statusBadge: Record<string, string> = {
  scheduled: "bg-blue-100 text-blue-700",
  confirmed: "bg-green-100 text-green-700",
  in_progress: "bg-amber-100 text-amber-700",
  completed: "bg-gray-100 text-gray-700",
  cancelled: "bg-red-100 text-red-700",
  no_show: "bg-red-100 text-red-700",
};

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showBooking, setShowBooking] = useState(false);

  useEffect(() => {
    fetchAppointments();
  }, []);

  const fetchAppointments = async () => {
    try {
      const res = await apiClient.get("/appointments");
      const data = res.data?.appointments ?? res.data;
      setAppointments(Array.isArray(data) ? data : []);
    } catch (err: unknown) {
      const status =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { status?: number } }).response?.status
          : undefined;
      if (status === 404) {
        setAppointments([]);
      } else {
        setError("Failed to load appointments.");
      }
    } finally {
      setLoading(false);
    }
  };

  const now = new Date();
  const upcoming = appointments.filter(
    (a) =>
      new Date(a.scheduled_at) >= now &&
      !["completed", "cancelled", "no_show"].includes(a.status)
  );
  const past = appointments.filter(
    (a) =>
      new Date(a.scheduled_at) < now ||
      ["completed", "cancelled", "no_show"].includes(a.status)
  );

  const getDoctorName = (a: Appointment): string => {
    if (a.doctor_name) return a.doctor_name;
    if (a.doctor) {
      if (a.doctor.name) return a.doctor.name;
      if (a.doctor.first_name)
        return `Dr. ${a.doctor.first_name} ${a.doctor.last_name ?? ""}`.trim();
    }
    return "Doctor";
  };

  const formatDateTime = (dt: string): string => {
    const d = new Date(dt);
    return d.toLocaleDateString("en-US", {
      weekday: "short",
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  };

  const handleBooked = () => {
    setShowBooking(false);
    setLoading(true);
    fetchAppointments();
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Appointments</h1>
          <p className="mt-1 text-muted-foreground">
            View and manage your upcoming and past appointments.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">
            {upcoming.length} upcoming
          </span>
          {!showBooking && (
            <button
              type="button"
              onClick={() => setShowBooking(true)}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary/90"
            >
              <CalendarPlus className="h-4 w-4" />
              Book Appointment
            </button>
          )}
        </div>
      </div>

      {showBooking && (
        <BookingFlow
          onBooked={handleBooked}
          onCancel={() => setShowBooking(false)}
        />
      )}

      {loading ? (
        <div className="rounded-lg border border-border bg-card p-12 text-center">
          <p className="text-sm text-muted-foreground">Loading appointments...</p>
        </div>
      ) : error ? (
        <div className="rounded-lg border border-border bg-card p-12 text-center">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      ) : appointments.length === 0 ? (
        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-foreground">Upcoming</h2>
            <p className="mt-4 text-sm text-muted-foreground">
              No upcoming appointments scheduled. Use the Book Appointment button above to
              schedule an in-person visit or telemedicine consultation.
            </p>
          </div>
          <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-foreground">Past Appointments</h2>
            <p className="mt-4 text-sm text-muted-foreground">
              Your appointment history will appear here.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <div>
            <h2 className="mb-3 text-lg font-semibold text-foreground">
              Upcoming ({upcoming.length})
            </h2>
            {upcoming.length === 0 ? (
              <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
                <p className="text-sm text-muted-foreground">
                  No upcoming appointments scheduled.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {upcoming.map((appt) => (
                  <AppointmentCard
                    key={appt.id}
                    appt={appt}
                    doctorName={getDoctorName(appt)}
                    formatDateTime={formatDateTime}
                  />
                ))}
              </div>
            )}
          </div>
          <div>
            <h2 className="mb-3 text-lg font-semibold text-foreground">
              Past ({past.length})
            </h2>
            {past.length === 0 ? (
              <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
                <p className="text-sm text-muted-foreground">
                  No past appointments found.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {past.map((appt) => (
                  <AppointmentCard
                    key={appt.id}
                    appt={appt}
                    doctorName={getDoctorName(appt)}
                    formatDateTime={formatDateTime}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function AppointmentCard({
  appt,
  doctorName,
  formatDateTime,
}: {
  appt: Appointment;
  doctorName: string;
  formatDateTime: (dt: string) => string;
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-sm font-semibold text-foreground">{doctorName}</h3>
          {appt.doctor?.specialization && (
            <p className="text-xs text-muted-foreground">{appt.doctor.specialization}</p>
          )}
        </div>
        <div className="flex gap-2">
          <span
            className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
              typeBadge[appt.appointment_type] ?? "bg-gray-100 text-gray-700"
            }`}
          >
            {appt.appointment_type.replace("_", " ")}
          </span>
          <span
            className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
              statusBadge[appt.status] ?? "bg-gray-100 text-gray-700"
            }`}
          >
            {appt.status.replace("_", " ")}
          </span>
        </div>
      </div>
      <div className="mt-3 space-y-1 text-sm">
        <div className="flex items-center gap-2 text-muted-foreground">
          <span className="font-medium text-foreground">
            {formatDateTime(appt.scheduled_at)}
          </span>
        </div>
        <p className="text-muted-foreground">
          Duration: {appt.duration_minutes} minutes
        </p>
        {appt.reason && (
          <p className="text-muted-foreground">
            <span className="font-medium text-foreground">Reason:</span> {appt.reason}
          </p>
        )}
        {appt.notes && (
          <p className="text-xs text-muted-foreground mt-2 italic">{appt.notes}</p>
        )}
      </div>
      {appt.appointment_type === "telemedicine" &&
        ["scheduled", "confirmed"].includes(appt.status) && (
          <div className="mt-3">
            <span className="inline-flex items-center rounded-md bg-purple-50 px-3 py-1 text-xs font-medium text-purple-700 border border-purple-200">
              Video call link will be available when the session starts
            </span>
          </div>
        )}
    </div>
  );
}
