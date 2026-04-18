/**
 * Helpers for GET /patients responses (array or wrapped payloads, snake_case or camelCase).
 */

export function extractPatientList(payload: unknown): Record<string, unknown>[] {
  if (Array.isArray(payload)) return payload as Record<string, unknown>[];
  if (payload != null && typeof payload === "object") {
    const o = payload as Record<string, unknown>;
    for (const key of ["patients", "data", "results", "items"] as const) {
      const v = o[key];
      if (Array.isArray(v)) return v as Record<string, unknown>[];
    }
  }
  return [];
}

export interface DoctorPatientListRow {
  id: string;
  user_id: string;
  first_name: string;
  last_name: string;
  email: string;
  gender: string;
  blood_type: string;
  date_of_birth: string;
  height_cm: number | null;
  weight_kg: number | null;
  assigned_doctor_name: string | null;
  phone: string | null;
}

/** Map API patient object to doctor patient table row with display fallbacks. */
export function normalizeDoctorPatientRow(raw: Record<string, unknown>): DoctorPatientListRow {
  const userId = String(raw.user_id ?? raw.userId ?? "").trim();
  const profileId = String(raw.id ?? "").trim();
  const id = profileId || userId;
  const uid = userId || profileId;

  let first = String(raw.first_name ?? raw.firstName ?? "").trim();
  let last = String(raw.last_name ?? raw.lastName ?? "").trim();
  const combined = String(raw.name ?? "").trim();
  if (!first && !last && combined) {
    const parts = combined.split(/\s+/).filter(Boolean);
    first = parts[0] ?? "";
    last = parts.slice(1).join(" ");
  }
  if (!first && !last) {
    first = combined || "Patient";
  }

  const dobRaw = raw.date_of_birth ?? raw.dateOfBirth;
  let date_of_birth = "";
  if (dobRaw != null && dobRaw !== "") {
    if (typeof dobRaw === "string") date_of_birth = dobRaw;
    else if (dobRaw instanceof Date) date_of_birth = dobRaw.toISOString().split("T")[0];
    else date_of_birth = String(dobRaw);
  }

  const hc = raw.height_cm ?? raw.heightCm;
  const wk = raw.weight_kg ?? raw.weightKg;

  return {
    id,
    user_id: uid,
    first_name: first,
    last_name: last,
    email: String(raw.email ?? "").trim(),
    gender: String(raw.gender ?? "").trim(),
    blood_type: String(raw.blood_type ?? raw.bloodType ?? "").trim(),
    date_of_birth,
    height_cm: hc != null && hc !== "" ? Number(hc) : null,
    weight_kg: wk != null && wk !== "" ? Number(wk) : null,
    assigned_doctor_name: (raw.assigned_doctor_name ?? raw.assignedDoctorName ?? null) as string | null,
    phone: raw.phone != null && raw.phone !== "" ? String(raw.phone) : null,
  };
}
