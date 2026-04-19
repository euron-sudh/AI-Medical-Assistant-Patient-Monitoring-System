"use client";

import { useState, useMemo, useEffect } from "react";
import {
  Calendar,
  Clock,
  User,
  ChevronRight,
  ChevronLeft,
  Check,
  Video,
  MapPin,
  Stethoscope,
  Loader2,
} from "lucide-react";
import apiClient from "@/lib/api-client";

interface Doctor {
  /** users.id — required for POST /appointments doctor_id */
  id: string;
  name: string;
  specialization: string;
  available: boolean;
}

interface TimeSlot {
  time: string;
  label: string;
  available: boolean;
}

type AppointmentType = "in_person" | "telemedicine";

interface BookingFlowProps {
  onBooked: () => void;
  onCancel: () => void;
}

const STEPS = ["Select Doctor", "Choose Date & Time", "Confirm Booking"] as const;

function generateTimeSlots(): TimeSlot[] {
  const slots: TimeSlot[] = [];
  for (let h = 9; h <= 17; h++) {
    for (const m of [0, 30]) {
      if (h === 17 && m === 30) continue;
      const hr = h.toString().padStart(2, "0");
      const mn = m.toString().padStart(2, "0");
      const label = `${h > 12 ? h - 12 : h}:${mn} ${h >= 12 ? "PM" : "AM"}`;
      slots.push({ time: `${hr}:${mn}`, label, available: Math.random() > 0.3 });
    }
  }
  return slots;
}

function getNextSevenDays(): { date: Date; label: string; dayName: string }[] {
  const days = [];
  const today = new Date();
  for (let i = 1; i <= 7; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    days.push({
      date: d,
      label: d.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      dayName: d.toLocaleDateString("en-US", { weekday: "short" }),
    });
  }
  return days;
}

export default function BookingFlow({ onBooked, onCancel }: BookingFlowProps) {
  const [step, setStep] = useState(0);
  const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [selectedTime, setSelectedTime] = useState<string | null>(null);
  const [appointmentType, setAppointmentType] = useState<AppointmentType>("in_person");
  const [reason, setReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [doctorsLoading, setDoctorsLoading] = useState(true);
  const [doctorsError, setDoctorsError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setDoctorsLoading(true);
    setDoctorsError(null);
    apiClient
      .get("/doctors")
      .then((res) => {
        if (cancelled) return;
        const raw = res.data?.doctors ?? res.data;
        const list = Array.isArray(raw) ? raw : [];
        if (list.length === 0) {
          setDoctors([]);
          setDoctorsError("No doctors are registered yet. Ask an administrator to add doctor accounts.");
          return;
        }
        setDoctors(
          list.map((d: Record<string, unknown>) => {
            const userId = d.user_id != null ? String(d.user_id) : "";
            const profileId = d.id != null ? String(d.id) : "";
            const bookingId = userId || profileId;
            const fn = d.first_name != null ? String(d.first_name) : "";
            const ln = d.last_name != null ? String(d.last_name) : "";
            const nameFromParts = `Dr. ${fn} ${ln}`.trim();
            return {
              id: bookingId,
              name: d.name ? String(d.name) : nameFromParts || "Doctor",
              specialization: String(d.specialization ?? "General Medicine"),
              available: d.available !== false && !!bookingId,
            };
          }),
        );
      })
      .catch(() => {
        if (!cancelled) {
          setDoctors([]);
          setDoctorsError("Could not load doctors. Check your connection and try again.");
        }
      })
      .finally(() => {
        if (!cancelled) setDoctorsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const dates = useMemo(() => getNextSevenDays(), []);
  const timeSlots = useMemo(() => generateTimeSlots(), []);

  const filteredDoctors = useMemo(() => {
    if (!searchQuery.trim()) return doctors;
    const q = searchQuery.toLowerCase();
    return doctors.filter(
      (d) => d.name.toLowerCase().includes(q) || d.specialization.toLowerCase().includes(q),
    );
  }, [searchQuery, doctors]);

  const canProceed = () => {
    if (step === 0) return !!selectedDoctor;
    if (step === 1) return !!selectedDate && !!selectedTime;
    return true;
  };

  const handleBook = async () => {
    if (!selectedDoctor || !selectedDate || !selectedTime) return;
    setIsSubmitting(true);
    setError(null);
    const scheduledAt = new Date(selectedDate);
    const [h, m] = selectedTime.split(":").map(Number);
    scheduledAt.setHours(h, m, 0, 0);
    try {
      const userStr = localStorage.getItem("user");
      const patientId = userStr ? JSON.parse(userStr).id : null;
      if (!patientId) {
        setError("Please log in again.");
        setIsSubmitting(false);
        return;
      }
      if (!selectedDoctor.id || !/^[0-9a-f-]{36}$/i.test(selectedDoctor.id)) {
        setError("Invalid doctor selection. Reload the page and pick a doctor from the list.");
        setIsSubmitting(false);
        return;
      }
      await apiClient.post("/appointments", {
        patient_id: patientId,
        doctor_id: selectedDoctor.id,
        scheduled_at: scheduledAt.toISOString(),
        appointment_type: appointmentType,
        duration_minutes: 30,
        reason: reason.trim() || null,
      });
      onBooked();
    } catch (err: unknown) {
      const ax = err as {
        code?: string;
        message?: string;
        response?: { data?: { error?: { message?: string } }; status?: number };
      };
      const serverMsg = ax.response?.data?.error?.message;
      const isNetwork =
        ax.code === "ERR_NETWORK" ||
        ax.message === "Network Error" ||
        (!ax.response && ax.message?.toLowerCase().includes("network"));
      const msg =
        serverMsg ??
        (isNetwork
          ? "Cannot reach the server, or the request failed before a response. Check that the API is running; if you use Docker, restart the backend after pulling the latest code."
          : ax.message) ??
        "Failed to book appointment. Please try again.";
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="rounded-xl border border-border bg-card shadow-sm">
      <div className="border-b border-border px-5 py-4">
        <div className="flex items-center gap-2">
          {STEPS.map((label, i) => (
            <div key={label} className="flex items-center gap-2">
              {i > 0 && <ChevronRight className="h-4 w-4 text-muted-foreground" />}
              <div className="flex items-center gap-1.5">
                <div
                  className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold ${
                    i < step
                      ? "bg-emerald-500 text-white"
                      : i === step
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground"
                  }`}
                >
                  {i < step ? <Check className="h-3.5 w-3.5" /> : i + 1}
                </div>
                <span
                  className={`hidden text-sm font-medium sm:inline ${i === step ? "text-foreground" : "text-muted-foreground"}`}
                >
                  {label}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="p-5">
        {step === 0 && (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-foreground">Select a Doctor</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Choose a healthcare provider for your appointment.
              </p>
            </div>
            {doctorsLoading && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading doctors…
              </div>
            )}
            {!doctorsLoading && doctorsError && (
              <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
                {doctorsError}
              </div>
            )}
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name or specialty..."
              disabled={doctors.length === 0}
              className="w-full rounded-md border border-input bg-background px-4 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
            />
            <div className="grid gap-3 sm:grid-cols-2">
              {filteredDoctors.map((doc) => (
                <button
                  key={doc.id}
                  type="button"
                  disabled={!doc.available}
                  onClick={() => setSelectedDoctor(doc)}
                  className={`flex items-start gap-3 rounded-lg border p-4 text-left transition-colors ${
                    selectedDoctor?.id === doc.id
                      ? "border-primary bg-primary/5 ring-1 ring-primary"
                      : doc.available
                        ? "border-border hover:bg-accent"
                        : "cursor-not-allowed border-border opacity-50"
                  }`}
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
                    <User className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-foreground">{doc.name}</p>
                    <p className="text-xs text-muted-foreground">{doc.specialization}</p>
                    {!doc.available && <p className="mt-1 text-xs text-red-500">Not available</p>}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-foreground">Choose Date and Time</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Select a convenient date and time for your visit with {selectedDoctor?.name}.
              </p>
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-foreground">Appointment Type</p>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setAppointmentType("in_person")}
                  className={`flex items-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-medium transition-colors ${
                    appointmentType === "in_person"
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-border text-muted-foreground hover:bg-accent"
                  }`}
                >
                  <MapPin className="h-4 w-4" />
                  In Person
                </button>
                <button
                  type="button"
                  onClick={() => setAppointmentType("telemedicine")}
                  className={`flex items-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-medium transition-colors ${
                    appointmentType === "telemedicine"
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-border text-muted-foreground hover:bg-accent"
                  }`}
                >
                  <Video className="h-4 w-4" />
                  Telemedicine
                </button>
              </div>
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-foreground">
                <Calendar className="mr-1 inline h-4 w-4" />
                Select Date
              </p>
              <div className="flex gap-2 overflow-x-auto pb-2">
                {dates.map((d) => (
                  <button
                    key={d.date.toISOString()}
                    type="button"
                    onClick={() => setSelectedDate(d.date)}
                    className={`flex shrink-0 flex-col items-center rounded-lg border px-4 py-3 transition-colors ${
                      selectedDate?.toDateString() === d.date.toDateString()
                        ? "border-primary bg-primary/5 text-primary"
                        : "border-border text-foreground hover:bg-accent"
                    }`}
                  >
                    <span className="text-xs font-medium">{d.dayName}</span>
                    <span className="text-sm font-bold">{d.label}</span>
                  </button>
                ))}
              </div>
            </div>
            {selectedDate && (
              <div>
                <p className="mb-2 text-sm font-medium text-foreground">
                  <Clock className="mr-1 inline h-4 w-4" />
                  Select Time
                </p>
                <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-6">
                  {timeSlots.map((slot) => (
                    <button
                      key={slot.time}
                      type="button"
                      disabled={!slot.available}
                      onClick={() => setSelectedTime(slot.time)}
                      className={`rounded-md border px-3 py-2 text-sm font-medium transition-colors ${
                        selectedTime === slot.time
                          ? "border-primary bg-primary text-primary-foreground"
                          : slot.available
                            ? "border-border text-foreground hover:bg-accent"
                            : "cursor-not-allowed border-border text-muted-foreground/50 line-through"
                      }`}
                    >
                      {slot.label}
                    </button>
                  ))}
                </div>
              </div>
            )}
            <div>
              <label htmlFor="booking-reason" className="mb-1 block text-sm font-medium text-foreground">
                Reason for visit (optional)
              </label>
              <textarea
                id="booking-reason"
                rows={2}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Brief description of your concern..."
                className="w-full rounded-md border border-input bg-background px-4 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
          </div>
        )}
        {step === 2 && selectedDoctor && selectedDate && selectedTime && (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-foreground">Confirm Your Appointment</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Review the details below and confirm your booking.
              </p>
            </div>
            <div className="space-y-3 rounded-lg border border-border bg-muted/30 p-5">
              <div className="flex items-center gap-3">
                <Stethoscope className="h-5 w-5 text-primary" />
                <div>
                  <p className="text-sm font-semibold text-foreground">{selectedDoctor.name}</p>
                  <p className="text-xs text-muted-foreground">{selectedDoctor.specialization}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Calendar className="h-5 w-5 text-primary" />
                <p className="text-sm text-foreground">
                  {selectedDate.toLocaleDateString("en-US", {
                    weekday: "long",
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Clock className="h-5 w-5 text-primary" />
                <p className="text-sm text-foreground">
                  {timeSlots.find((s) => s.time === selectedTime)?.label} (30 minutes)
                </p>
              </div>
              <div className="flex items-center gap-3">
                {appointmentType === "telemedicine" ? (
                  <Video className="h-5 w-5 text-purple-600" />
                ) : (
                  <MapPin className="h-5 w-5 text-blue-600" />
                )}
                <p className="text-sm text-foreground capitalize">{appointmentType.replace("_", " ")}</p>
              </div>
              {reason.trim() && (
                <div className="border-t border-border pt-3">
                  <p className="text-xs text-muted-foreground">Reason</p>
                  <p className="text-sm text-foreground">{reason}</p>
                </div>
              )}
            </div>
            {error && (
              <div className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center justify-between border-t border-border px-5 py-4">
        <button
          type="button"
          onClick={step === 0 ? onCancel : () => setStep((s) => s - 1)}
          className="flex items-center gap-1 rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-muted"
        >
          <ChevronLeft className="h-4 w-4" />
          {step === 0 ? "Cancel" : "Back"}
        </button>
        {step < 2 ? (
          <button
            type="button"
            disabled={!canProceed()}
            onClick={() => setStep((s) => s + 1)}
            className="flex items-center gap-1 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </button>
        ) : (
          <button
            type="button"
            disabled={isSubmitting}
            onClick={() => void handleBook()}
            className="flex items-center gap-1 rounded-md bg-emerald-600 px-5 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {isSubmitting ? "Booking..." : "Confirm Booking"}
            <Check className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}
