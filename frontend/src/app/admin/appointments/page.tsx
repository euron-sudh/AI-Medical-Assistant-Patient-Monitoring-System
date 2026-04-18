"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import apiClient from "@/lib/api-client";
import { extractPatientList, normalizeDoctorPatientRow } from "@/lib/patient-list";
import { CalendarPlus, Loader2, Pencil, Trash2, X } from "lucide-react";

interface AppointmentRow {
  id: string;
  patient_id: string;
  doctor_id: string;
  patient_name: string | null;
  doctor_name: string | null;
  appointment_type: string;
  status: string;
  scheduled_at: string;
  duration_minutes: number;
  reason: string | null;
  notes: string | null;
}

interface SelectOption {
  value: string;
  label: string;
}

const APPOINTMENT_TYPES = [
  { value: "in_person", label: "In person" },
  { value: "telemedicine", label: "Telemedicine" },
  { value: "follow_up", label: "Follow up" },
  { value: "emergency", label: "Emergency" },
] as const;

const STATUSES = [
  "scheduled",
  "confirmed",
  "in_progress",
  "completed",
  "cancelled",
  "no_show",
] as const;

const STATUS_STYLES: Record<string, string> = {
  scheduled: "bg-blue-50 text-blue-700",
  confirmed: "bg-green-50 text-green-700",
  in_progress: "bg-amber-50 text-amber-700",
  completed: "bg-gray-100 text-gray-700",
  cancelled: "bg-red-50 text-red-700",
  no_show: "bg-orange-50 text-orange-700",
};

function extractAppointmentList(data: unknown): AppointmentRow[] {
  if (Array.isArray(data)) return data as AppointmentRow[];
  if (data != null && typeof data === "object") {
    const o = data as Record<string, unknown>;
    if (Array.isArray(o.appointments)) return o.appointments as AppointmentRow[];
  }
  return [];
}

function toDatetimeLocalValue(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function emptyForm() {
  return {
    patient_id: "",
    doctor_id: "",
    scheduled_at_local: "",
    duration_minutes: "30",
    status: "scheduled" as (typeof STATUSES)[number],
    appointment_type: "in_person" as (typeof APPOINTMENT_TYPES)[number]["value"],
    reason: "",
    notes: "",
  };
}

export default function AdminAppointmentsPage() {
  const [appointments, setAppointments] = useState<AppointmentRow[]>([]);
  const [patientOptions, setPatientOptions] = useState<SelectOption[]>([]);
  const [doctorOptions, setDoctorOptions] = useState<SelectOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [deleteTarget, setDeleteTarget] = useState<AppointmentRow | null>(null);
  const [deleteSubmitting, setDeleteSubmitting] = useState(false);

  const loadReferenceData = useCallback(async () => {
    const [pRes, dRes] = await Promise.allSettled([
      apiClient.get("/patients"),
      apiClient.get("/doctors"),
    ]);

    if (pRes.status === "fulfilled") {
      const rows = extractPatientList(pRes.value.data).map((r) => normalizeDoctorPatientRow(r));
      setPatientOptions(
        rows.map((p) => ({
          value: p.user_id,
          label: `${p.first_name} ${p.last_name}`.trim() || p.email || p.user_id,
        })),
      );
    } else {
      setPatientOptions([]);
    }

    if (dRes.status === "fulfilled") {
      const raw = dRes.value.data;
      const list = Array.isArray(raw) ? raw : [];
      setDoctorOptions(
        list.map((d: Record<string, unknown>) => {
          const uid = String(d.user_id ?? d.id ?? "");
          const fn = String(d.first_name ?? "");
          const ln = String(d.last_name ?? "");
          const name = d.name ? String(d.name) : `Dr. ${fn} ${ln}`.trim();
          return { value: uid, label: name || uid };
        }),
      );
    } else {
      setDoctorOptions([]);
    }
  }, []);

  const loadAppointments = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.get("/appointments", { params: { limit: 500 } });
      setAppointments(extractAppointmentList(res.data));
    } catch {
      setError("Failed to load appointments.");
      setAppointments([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAppointments();
    loadReferenceData();
  }, [loadAppointments, loadReferenceData]);

  const filtered = useMemo(() => {
    if (!search.trim()) return appointments;
    const q = search.toLowerCase();
    return appointments.filter(
      (a) =>
        (a.patient_name ?? "").toLowerCase().includes(q) ||
        (a.doctor_name ?? "").toLowerCase().includes(q) ||
        a.status.toLowerCase().includes(q) ||
        a.appointment_type.toLowerCase().includes(q),
    );
  }, [appointments, search]);

  const openAdd = () => {
    setEditingId(null);
    setForm(emptyForm());
    setFormError(null);
    setModalOpen(true);
  };

  const openEdit = (a: AppointmentRow) => {
    setEditingId(a.id);
    setForm({
      patient_id: a.patient_id,
      doctor_id: a.doctor_id,
      scheduled_at_local: toDatetimeLocalValue(a.scheduled_at),
      duration_minutes: String(a.duration_minutes ?? 30),
      status: (STATUSES.includes(a.status as (typeof STATUSES)[number])
        ? a.status
        : "scheduled") as (typeof STATUSES)[number],
      appointment_type: (APPOINTMENT_TYPES.map((t) => t.value).includes(
        a.appointment_type as (typeof APPOINTMENT_TYPES)[number]["value"],
      )
        ? a.appointment_type
        : "in_person") as (typeof APPOINTMENT_TYPES)[number]["value"],
      reason: a.reason ?? "",
      notes: a.notes ?? "",
    });
    setFormError(null);
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingId(null);
    setFormError(null);
  };

  const submitForm = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (!form.patient_id || !form.doctor_id || !form.scheduled_at_local) {
      setFormError("Patient, doctor, and date & time are required.");
      return;
    }
    const scheduled = new Date(form.scheduled_at_local);
    if (Number.isNaN(scheduled.getTime())) {
      setFormError("Invalid date and time.");
      return;
    }
    const duration = parseInt(form.duration_minutes, 10);
    if (Number.isNaN(duration) || duration < 5 || duration > 480) {
      setFormError("Duration must be between 5 and 480 minutes.");
      return;
    }

    setFormSubmitting(true);
    try {
      if (editingId) {
        await apiClient.put(`/appointments/${editingId}`, {
          patient_id: form.patient_id,
          doctor_id: form.doctor_id,
          scheduled_at: scheduled.toISOString(),
          duration_minutes: duration,
          status: form.status,
          appointment_type: form.appointment_type,
          reason: form.reason.trim() || null,
          notes: form.notes.trim() || null,
        });
      } else {
        await apiClient.post("/appointments", {
          patient_id: form.patient_id,
          doctor_id: form.doctor_id,
          appointment_type: form.appointment_type,
          scheduled_at: scheduled.toISOString(),
          duration_minutes: duration,
          reason: form.reason.trim() || null,
          notes: form.notes.trim() || null,
        });
      }
      closeModal();
      await loadAppointments();
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? String(
              (err as { response?: { data?: { error?: { message?: string } } } }).response?.data
                ?.error?.message ?? "Request failed",
            )
          : "Failed to save appointment.";
      setFormError(msg);
    } finally {
      setFormSubmitting(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleteSubmitting(true);
    try {
      await apiClient.delete(`/appointments/${deleteTarget.id}`);
      setDeleteTarget(null);
      await loadAppointments();
    } catch {
      setError("Failed to delete appointment.");
    } finally {
      setDeleteSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Appointment Management</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            View and manage all patient appointments across the platform.
          </p>
        </div>
        <button
          type="button"
          onClick={openAdd}
          className="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <CalendarPlus className="h-4 w-4" />
          Add Appointment
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-4">
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by patient, doctor, status, or type…"
          className="w-full max-w-md rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring sm:w-80"
        />
        <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
          {filtered.length} appointment{filtered.length !== 1 ? "s" : ""}
        </span>
      </div>

      {loading && (
        <div className="flex items-center justify-center rounded-lg border border-border bg-card py-16">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-3 text-sm text-muted-foreground">Loading appointments…</span>
        </div>
      )}

      {error && !loading && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
          <p className="text-sm text-destructive">{error}</p>
          <button
            type="button"
            onClick={() => {
              loadAppointments();
            }}
            className="mt-2 text-sm font-medium text-primary hover:underline"
          >
            Retry
          </button>
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-border bg-card py-16 text-center">
          <p className="text-lg font-medium text-foreground">No appointments available</p>
          <p className="mt-1 max-w-md text-sm text-muted-foreground">
            There are no appointments to show. Create one to get started.
          </p>
          <button
            type="button"
            onClick={openAdd}
            className="mt-6 inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <CalendarPlus className="h-4 w-4" />
            Add Appointment
          </button>
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] text-left text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/40">
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Patient
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Doctor
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Date
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Time
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Status
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Type
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Notes / Reason
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map((a) => {
                  const dt = new Date(a.scheduled_at);
                  const dateStr = Number.isNaN(dt.getTime())
                    ? "—"
                    : dt.toLocaleDateString(undefined, {
                        weekday: "short",
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      });
                  const timeStr = Number.isNaN(dt.getTime())
                    ? "—"
                    : dt.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
                  return (
                    <tr key={a.id} className="transition-colors hover:bg-muted/40">
                      <td className="px-4 py-3 font-medium text-foreground">
                        {a.patient_name ?? "—"}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{a.doctor_name ?? "—"}</td>
                      <td className="px-4 py-3 text-muted-foreground">{dateStr}</td>
                      <td className="px-4 py-3 text-muted-foreground">{timeStr}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[a.status] ?? "bg-gray-100 text-gray-700"}`}
                        >
                          {a.status.replace("_", " ")}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {a.appointment_type.replace("_", " ")}
                      </td>
                      <td className="max-w-[200px] truncate px-4 py-3 text-muted-foreground" title={a.reason ?? a.notes ?? ""}>
                        {a.reason || a.notes || "—"}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          type="button"
                          onClick={() => openEdit(a)}
                          className="mr-2 inline-flex items-center gap-1 rounded-md border border-input px-2 py-1 text-xs font-medium hover:bg-muted"
                        >
                          <Pencil className="h-3 w-3" />
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => setDeleteTarget(a)}
                          className="inline-flex items-center gap-1 rounded-md border border-destructive/30 bg-destructive/5 px-2 py-1 text-xs font-medium text-destructive hover:bg-destructive/10"
                        >
                          <Trash2 className="h-3 w-3" />
                          Delete
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div
            role="dialog"
            aria-modal="true"
            className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-lg border border-border bg-card p-6 shadow-lg"
          >
            <div className="flex items-center justify-between gap-4">
              <h2 className="text-lg font-semibold text-foreground">
                {editingId ? "Edit appointment" : "Add appointment"}
              </h2>
              <button
                type="button"
                onClick={closeModal}
                className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                aria-label="Close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={submitForm} className="mt-4 space-y-4">
              <label className="block">
                <span className="text-xs font-medium text-muted-foreground">Patient *</span>
                <select
                  required
                  value={form.patient_id}
                  onChange={(e) => setForm((f) => ({ ...f, patient_id: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="">Select patient…</option>
                  {patientOptions.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="text-xs font-medium text-muted-foreground">Doctor *</span>
                <select
                  required
                  value={form.doctor_id}
                  onChange={(e) => setForm((f) => ({ ...f, doctor_id: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="">Select doctor…</option>
                  {doctorOptions.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="text-xs font-medium text-muted-foreground">Date & time *</span>
                <input
                  type="datetime-local"
                  required
                  value={form.scheduled_at_local}
                  onChange={(e) => setForm((f) => ({ ...f, scheduled_at_local: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-muted-foreground">Duration (minutes) *</span>
                <input
                  type="number"
                  required
                  min={5}
                  max={480}
                  value={form.duration_minutes}
                  onChange={(e) => setForm((f) => ({ ...f, duration_minutes: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </label>
              {editingId && (
                <label className="block">
                  <span className="text-xs font-medium text-muted-foreground">Status</span>
                  <select
                    value={form.status}
                    onChange={(e) =>
                      setForm((f) => ({
                        ...f,
                        status: e.target.value as (typeof STATUSES)[number],
                      }))
                    }
                    className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {s.replace("_", " ")}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              <label className="block">
                <span className="text-xs font-medium text-muted-foreground">Appointment type</span>
                <select
                  value={form.appointment_type}
                  onChange={(e) =>
                    setForm((f) => ({
                      ...f,
                      appointment_type: e.target.value as (typeof APPOINTMENT_TYPES)[number]["value"],
                    }))
                  }
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {APPOINTMENT_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="text-xs font-medium text-muted-foreground">Reason</span>
                <input
                  type="text"
                  value={form.reason}
                  onChange={(e) => setForm((f) => ({ ...f, reason: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-muted-foreground">Notes</span>
                <textarea
                  rows={3}
                  value={form.notes}
                  onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </label>
              {formError && (
                <p className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {formError}
                </p>
              )}
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={closeModal}
                  className="rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-muted"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={formSubmitting}
                  className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
                >
                  {formSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Saving…
                    </>
                  ) : editingId ? (
                    "Save changes"
                  ) : (
                    "Create"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {deleteTarget && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">Delete appointment?</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              This will permanently remove the appointment for{" "}
              <span className="font-medium text-foreground">
                {deleteTarget.patient_name ?? "patient"}
              </span>{" "}
              on{" "}
              {new Date(deleteTarget.scheduled_at).toLocaleString(undefined, {
                dateStyle: "medium",
                timeStyle: "short",
              })}
              . This cannot be undone.
            </p>
            <div className="mt-6 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setDeleteTarget(null)}
                className="rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-muted"
                disabled={deleteSubmitting}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmDelete}
                disabled={deleteSubmitting}
                className="inline-flex items-center gap-2 rounded-md bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground hover:bg-destructive/90 disabled:opacity-60"
              >
                {deleteSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
