"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  Calendar,
  Check,
  ChevronLeft,
  ChevronRight,
  Clock,
  MapPin,
  Star,
  Stethoscope,
  User,
  Video,
  X,
} from "lucide-react";
import apiClient from "@/lib/api-client";
import SpecialtySelector from "@/components/shared/SpecialtySelector";

/** Maps SpecialtySelector ids to API specialization search terms. */
const SPECIALTY_SEARCH: Record<string, string> = {
  "general-physician": "General",
  cardiology: "Cardiology",
  orthopedics: "Orthopedics",
  dermatology: "Dermatology",
  gynecology: "Gynecology",
  pediatrics: "Pediatrics",
  neurology: "Neurology",
  psychiatry: "Psychiatry",
};

export interface DoctorProfile {
  id: string;
  user_id: string;
  specialization: string;
  years_of_experience?: number | null;
  consultation_fee?: number | null;
}

interface AvailabilitySlot {
  start: string;
  end: string;
}

interface BookingFlowProps {
  open: boolean;
  onClose: () => void;
  onBooked: () => void;
}

const STEPS = ["Specialty", "Doctor", "Date & time", "Confirm"] as const;

function getPatientId(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const u = JSON.parse(localStorage.getItem("user") || "{}") as {
      id?: string;
      patient_id?: string;
    };
    return u.id ?? u.patient_id ?? null;
  } catch {
    return null;
  }
}

function formatSlotLabel(isoStart: string): string {
  const d = new Date(isoStart);
  return d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

function doctorDisplayName(d: DoctorProfile): string {
  return `Dr. ${d.specialization.split(/[;,]/)[0]?.trim() ?? "Provider"}`;
}

function placeholderRating(userId: string): string {
  let n = 0;
  for (let i = 0; i < userId.length; i += 1) n += userId.charCodeAt(i);
  return (4 + (n % 10) / 10).toFixed(1);
}

export default function BookingFlow({ open, onClose, onBooked }: BookingFlowProps) {
  const queryClient = useQueryClient();
  const [step, setStep] = useState(0);
  const [specialtyId, setSpecialtyId] = useState<string | null>(null);
  const [selectedDoctor, setSelectedDoctor] = useState<DoctorProfile | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [selectedSlotStart, setSelectedSlotStart] = useState<string | null>(null);
  const [appointmentType, setAppointmentType] = useState<
    "in_person" | "telemedicine" | "follow_up" | "emergency"
  >("in_person");
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  const specSearch = specialtyId ? SPECIALTY_SEARCH[specialtyId] ?? specialtyId : "";

  const doctorsQuery = useQuery({
    queryKey: ["doctors", specSearch],
    queryFn: async () => {
      const res = await apiClient.get<DoctorProfile[]>("/doctors", {
        params: { specialization: specSearch, limit: 50 },
      });
      const raw = res.data;
      return Array.isArray(raw) ? raw : [];
    },
    enabled: open && step >= 1 && !!specSearch,
  });

  const dateIso = selectedDate
    ? `${selectedDate.getFullYear()}-${String(selectedDate.getMonth() + 1).padStart(2, "0")}-${String(selectedDate.getDate()).padStart(2, "0")}`
    : null;

  const availabilityQuery = useQuery({
    queryKey: ["appointments", "availability", selectedDoctor?.user_id, dateIso],
    queryFn: async () => {
      if (!selectedDoctor?.user_id || !dateIso) return { available_slots: [] as AvailabilitySlot[] };
      const res = await apiClient.get<{
        available_slots?: AvailabilitySlot[];
      }>(`/appointments/availability/${selectedDoctor.user_id}`, {
        params: { date: dateIso },
      });
      return res.data;
    },
    enabled: open && step >= 2 && !!selectedDoctor?.user_id && !!dateIso,
  });

  const bookMutation = useMutation({
    mutationFn: async () => {
      const patientId = getPatientId();
      if (!patientId || !selectedDoctor || !selectedSlotStart) {
        throw new Error("Missing booking details.");
      }
      await apiClient.post("/appointments", {
        patient_id: patientId,
        doctor_id: selectedDoctor.user_id,
        appointment_type: appointmentType,
        scheduled_at: selectedSlotStart,
        duration_minutes: 30,
        reason: reason.trim() || null,
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["appointments"] });
      setStep(0);
      setSpecialtyId(null);
      setSelectedDoctor(null);
      setSelectedDate(null);
      setSelectedSlotStart(null);
      setReason("");
      setError(null);
      onBooked();
      onClose();
    },
    onError: () => {
      setError("Could not book this slot. It may have been taken. Try another time.");
    },
  });

  const dates = useMemo(() => {
    const out: Date[] = [];
    const today = new Date();
    for (let i = 1; i <= 14; i += 1) {
      const d = new Date(today);
      d.setDate(today.getDate() + i);
      d.setHours(0, 0, 0, 0);
      out.push(d);
    }
    return out;
  }, []);

  const resetAndClose = () => {
    setStep(0);
    setSpecialtyId(null);
    setSelectedDoctor(null);
    setSelectedDate(null);
    setSelectedSlotStart(null);
    setReason("");
    setError(null);
    onClose();
  };

  const canNext = (): boolean => {
    if (step === 0) return !!specialtyId;
    if (step === 1) return !!selectedDoctor;
    if (step === 2) return !!selectedDate && !!selectedSlotStart;
    return true;
  };

  const handleNext = () => {
    setError(null);
    if (step < STEPS.length - 1) setStep((s) => s + 1);
  };

  const handleBack = () => {
    setError(null);
    if (step === 0) resetAndClose();
    else setStep((s) => s - 1);
  };

  if (!open) return null;

  const slots = availabilityQuery.data?.available_slots ?? [];

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
      <button
        type="button"
        className="absolute inset-0 bg-black/50"
        aria-label="Close booking"
        onClick={resetAndClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="booking-flow-title"
        className="relative z-10 flex max-h-[92vh] w-full max-w-3xl flex-col overflow-hidden rounded-t-2xl border border-border bg-card shadow-xl sm:rounded-2xl"
      >
        <div className="flex items-center justify-between border-b border-border px-4 py-3 sm:px-6">
          <h2 id="booking-flow-title" className="text-lg font-semibold text-foreground">
            Book appointment
          </h2>
          <button
            type="button"
            onClick={resetAndClose}
            className="rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="border-b border-border px-4 py-3 sm:px-6">
          <div className="flex flex-wrap items-center gap-2">
            {STEPS.map((label, i) => (
              <div key={label} className="flex items-center gap-2">
                {i > 0 && <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />}
                <div className="flex items-center gap-1.5">
                  <div
                    className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold ${
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
                    className={`hidden text-xs font-medium sm:inline sm:text-sm ${
                      i === step ? "text-foreground" : "text-muted-foreground"
                    }`}
                  >
                    {label}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4 sm:px-6">
          {step === 0 && (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Choose the type of care you need. You can change this later before confirming.
              </p>
              <SpecialtySelector
                variant="modal"
                onSelect={(id) => {
                  setSpecialtyId(id);
                  setError(null);
                }}
              />
              {!specialtyId && (
                <p className="text-xs text-muted-foreground">Select a specialty to continue.</p>
              )}
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-base font-semibold text-foreground">Select a doctor</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  Providers matching &quot;{specSearch}&quot;
                </p>
              </div>
              {doctorsQuery.isLoading && (
                <p className="text-sm text-muted-foreground">Loading doctors...</p>
              )}
              {doctorsQuery.isError && (
                <p className="text-sm text-destructive">Could not load doctors. Try again.</p>
              )}
              {!doctorsQuery.isLoading && doctorsQuery.data?.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  No doctors found for this specialty. Go back and try another.
                </p>
              )}
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {doctorsQuery.data?.map((doc) => {
                  const selected = selectedDoctor?.user_id === doc.user_id;
                  const rating = placeholderRating(doc.user_id);
                  return (
                    <button
                      key={doc.user_id}
                      type="button"
                      onClick={() => setSelectedDoctor(doc)}
                      className={`flex gap-3 rounded-xl border p-4 text-left transition-all ${
                        selected
                          ? "border-primary ring-2 ring-primary/25 shadow-md"
                          : "border-border hover:border-primary/40 hover:bg-accent"
                      }`}
                    >
                      <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-muted">
                        <User className="h-7 w-7 text-muted-foreground" aria-hidden />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="font-semibold text-foreground">{doctorDisplayName(doc)}</p>
                        <p className="text-xs text-muted-foreground">{doc.specialization}</p>
                        <div className="mt-1 flex items-center gap-1 text-xs text-amber-600">
                          <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-500" />
                          <span>{rating}</span>
                          <span className="text-muted-foreground">·</span>
                          <span className="text-muted-foreground">
                            {doc.years_of_experience != null
                              ? `${doc.years_of_experience} yrs exp`
                              : "Licensed physician"}
                          </span>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {step === 2 && selectedDoctor && (
            <div className="space-y-6">
              <div>
                <h3 className="text-base font-semibold text-foreground">Date and time</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  With {doctorDisplayName(selectedDoctor)}
                </p>
              </div>
              <div>
                <p className="mb-2 text-sm font-medium text-foreground">Visit type</p>
                <div className="flex flex-wrap gap-2">
                  {(
                    [
                      ["in_person", "In person", MapPin],
                      ["telemedicine", "Telemedicine", Video],
                      ["follow_up", "Follow-up", Stethoscope],
                      ["emergency", "Emergency", AlertCircle],
                    ] as const
                  ).map(([value, label, Icon]) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() =>
                        setAppointmentType(
                          value as "in_person" | "telemedicine" | "follow_up" | "emergency"
                        )
                      }
                      className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium ${
                        appointmentType === value
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border text-muted-foreground hover:bg-accent"
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      {label}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <p className="mb-2 text-sm font-medium text-foreground">
                  <Calendar className="mr-1 inline h-4 w-4" />
                  Date
                </p>
                <div className="flex gap-2 overflow-x-auto pb-2">
                  {dates.map((d) => {
                    const active =
                      selectedDate?.toDateString() === d.toDateString();
                    return (
                      <button
                        key={d.toISOString()}
                        type="button"
                        onClick={() => {
                          setSelectedDate(d);
                          setSelectedSlotStart(null);
                        }}
                        className={`flex shrink-0 flex-col items-center rounded-lg border px-3 py-2 transition-colors ${
                          active
                            ? "border-primary bg-primary/10 text-primary"
                            : "border-border hover:bg-accent"
                        }`}
                      >
                        <span className="text-xs">
                          {d.toLocaleDateString(undefined, { weekday: "short" })}
                        </span>
                        <span className="text-sm font-semibold">
                          {d.toLocaleDateString(undefined, {
                            month: "short",
                            day: "numeric",
                          })}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
              {selectedDate && (
                <div>
                  <p className="mb-2 text-sm font-medium text-foreground">
                    <Clock className="mr-1 inline h-4 w-4" />
                    Available times
                  </p>
                  {availabilityQuery.isLoading && (
                    <p className="text-sm text-muted-foreground">Loading slots...</p>
                  )}
                  {availabilityQuery.isError && (
                    <p className="text-sm text-destructive">Could not load availability.</p>
                  )}
                  {!availabilityQuery.isLoading && slots.length === 0 && (
                    <p className="text-sm text-muted-foreground">
                      No open slots this day. Pick another date.
                    </p>
                  )}
                  <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-5">
                    {slots.map((slot) => (
                      <button
                        key={slot.start}
                        type="button"
                        onClick={() => setSelectedSlotStart(slot.start)}
                        className={`rounded-md border px-2 py-2 text-sm font-medium ${
                          selectedSlotStart === slot.start
                            ? "border-primary bg-primary text-primary-foreground"
                            : "border-border hover:bg-accent"
                        }`}
                      >
                        {formatSlotLabel(slot.start)}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              <div>
                <label htmlFor="book-reason" className="mb-1 block text-sm font-medium">
                  Reason (optional)
                </label>
                <textarea
                  id="book-reason"
                  rows={2}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  placeholder="Brief reason for visit"
                />
              </div>
            </div>
          )}

          {step === 3 && selectedDoctor && selectedDate && selectedSlotStart && (
            <div className="space-y-4">
              <h3 className="text-base font-semibold text-foreground">Review</h3>
              <div className="space-y-2 rounded-lg border border-border bg-muted/30 p-4 text-sm">
                <p>
                  <span className="text-muted-foreground">Doctor:</span>{" "}
                  <span className="font-medium text-foreground">
                    {doctorDisplayName(selectedDoctor)}
                  </span>
                </p>
                <p>
                  <span className="text-muted-foreground">Specialty:</span>{" "}
                  {selectedDoctor.specialization}
                </p>
                <p>
                  <span className="text-muted-foreground">When:</span>{" "}
                  {selectedDate.toLocaleDateString(undefined, {
                    weekday: "long",
                    month: "long",
                    day: "numeric",
                    year: "numeric",
                  })}{" "}
                  at {formatSlotLabel(selectedSlotStart)}
                </p>
                <p>
                  <span className="text-muted-foreground">Type:</span>{" "}
                  {appointmentType.replace("_", " ")}
                </p>
                {reason.trim() && (
                  <p>
                    <span className="text-muted-foreground">Reason:</span> {reason}
                  </p>
                )}
              </div>
              {error && (
                <div className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {error}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between gap-3 border-t border-border px-4 py-3 sm:px-6">
          <button
            type="button"
            onClick={handleBack}
            className="inline-flex items-center gap-1 rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-muted"
          >
            <ChevronLeft className="h-4 w-4" />
            {step === 0 ? "Cancel" : "Back"}
          </button>
          {step < STEPS.length - 1 ? (
            <button
              type="button"
              disabled={!canNext()}
              onClick={handleNext}
              className="inline-flex items-center gap-1 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </button>
          ) : (
            <button
              type="button"
              disabled={bookMutation.isPending}
              onClick={() => {
                setError(null);
                bookMutation.mutate();
              }}
              className="inline-flex items-center gap-1 rounded-md bg-emerald-600 px-5 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              {bookMutation.isPending ? "Booking..." : "Confirm"}
              <Check className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
