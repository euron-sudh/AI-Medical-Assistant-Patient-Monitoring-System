"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import apiClient from "@/lib/api-client";
import { UserPlus, Loader2 } from "lucide-react";

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
  phone: string | null;
}

const ROLE_STYLES: Record<string, string> = {
  patient: "bg-blue-100 text-blue-800",
  doctor: "bg-green-100 text-green-800",
  nurse: "bg-purple-100 text-purple-800",
  admin: "bg-red-100 text-red-800",
};

const emptyDoctorForm = {
  email: "",
  password: "",
  first_name: "",
  last_name: "",
  phone: "",
  specialization: "",
  license_number: "",
  license_state: "",
  department: "",
  years_of_experience: "",
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("all");

  const [addDoctorOpen, setAddDoctorOpen] = useState(false);
  const [doctorForm, setDoctorForm] = useState(emptyDoctorForm);
  const [addDoctorLoading, setAddDoctorLoading] = useState(false);
  const [addDoctorError, setAddDoctorError] = useState<string | null>(null);
  const [addDoctorSuccess, setAddDoctorSuccess] = useState<string | null>(null);
  const [doctorToggleId, setDoctorToggleId] = useState<string | null>(null);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);

      let allUsers: User[] = [];
      try {
        const res = await apiClient.get("/admin/users");
        const data = res.data.users ?? res.data ?? [];
        allUsers = Array.isArray(data) ? data : [];
      } catch {
        const [pRes, dRes] = await Promise.allSettled([
          apiClient.get("/patients"),
          apiClient.get("/doctors"),
        ]);

        if (pRes.status === "fulfilled") {
          const patients = pRes.value.data.patients ?? pRes.value.data ?? [];
          if (Array.isArray(patients)) {
            allUsers.push(
              ...patients.map((p: User & { user_id?: string }) => ({
                ...p,
                id: p.user_id ?? p.id,
                role: p.role ?? "patient",
              })),
            );
          }
        }

        if (dRes.status === "fulfilled") {
          const doctors = dRes.value.data.doctors ?? dRes.value.data ?? [];
          if (Array.isArray(doctors)) {
            allUsers.push(
              ...doctors.map((d: User & { user_id?: string }) => ({
                ...d,
                id: d.user_id ?? d.id,
                role: d.role ?? "doctor",
              })),
            );
          }
        }
      }

      setUsers(allUsers);
    } catch {
      setError("Failed to load users.");
    } finally {
      setLoading(false);
    }
  };

  const submitAddDoctor = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddDoctorError(null);
    setAddDoctorSuccess(null);

    const {
      email,
      password,
      first_name,
      last_name,
      phone,
      specialization,
      license_number,
      license_state,
      department,
      years_of_experience,
    } = doctorForm;

    if (!email.trim() || !password || !first_name.trim() || !last_name.trim()) {
      setAddDoctorError("Email, password, first name, and last name are required.");
      return;
    }
    if (!specialization.trim() || !license_number.trim()) {
      setAddDoctorError("Specialization and license number are required for doctors.");
      return;
    }

    setAddDoctorLoading(true);
    try {
      const payload: Record<string, unknown> = {
        email: email.trim(),
        password,
        first_name: first_name.trim(),
        last_name: last_name.trim(),
        role: "doctor",
        specialization: specialization.trim(),
        license_number: license_number.trim(),
      };
      if (phone.trim()) payload.phone = phone.trim();
      if (license_state.trim()) payload.license_state = license_state.trim();
      if (department.trim()) payload.department = department.trim();
      if (years_of_experience.trim()) {
        const y = parseInt(years_of_experience, 10);
        if (!Number.isNaN(y)) payload.years_of_experience = y;
      }

      await apiClient.post("/admin/users", payload);
      setAddDoctorSuccess("Doctor account created. They can sign in with the email and password you set.");
      setDoctorForm(emptyDoctorForm);
      await fetchUsers();
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: { message?: string } } } };
      setAddDoctorError(
        ax.response?.data?.error?.message ?? (err as Error)?.message ?? "Failed to create doctor.",
      );
    } finally {
      setAddDoctorLoading(false);
    }
  };

  const toggleDoctorActive = async (u: User) => {
    if (u.role !== "doctor") return;
    const next = u.is_active !== false ? false : true;
    setDoctorToggleId(u.id);
    try {
      await apiClient.patch(`/admin/users/${u.id}`, { is_active: next });
      setUsers((prev) => prev.map((x) => (x.id === u.id ? { ...x, is_active: next } : x)));
    } catch {
      // keep UI unchanged on failure
    } finally {
      setDoctorToggleId(null);
    }
  };

  const filtered = users
    .filter((u) => {
      if (roleFilter !== "all" && u.role !== roleFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        const name = `${u.first_name ?? ""} ${u.last_name ?? ""}`.toLowerCase();
        return name.includes(q) || (u.email ?? "").toLowerCase().includes(q);
      }
      return true;
    })
    .sort((a, b) => (a.first_name ?? "").localeCompare(b.first_name ?? ""));

  const roleCounts = {
    patient: users.filter((u) => u.role === "patient").length,
    doctor: users.filter((u) => u.role === "doctor").length,
    nurse: users.filter((u) => u.role === "nurse").length,
    admin: users.filter((u) => u.role === "admin").length,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">User Management</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage platform users, roles, and access permissions.
          </p>
        </div>
        <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
          {users.length} total users
        </span>
      </div>

      {/* Add doctor — admin-only workflow */}
      <div className="rounded-lg border border-border bg-card shadow-sm">
        <button
          type="button"
          onClick={() => {
            setAddDoctorOpen((v) => !v);
            setAddDoctorError(null);
            setAddDoctorSuccess(null);
          }}
          className="flex w-full items-center justify-between px-6 py-4 text-left transition-colors hover:bg-muted/40"
        >
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-md bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-200">
              <UserPlus className="h-5 w-5" />
            </span>
            <div>
              <h2 className="text-base font-semibold text-foreground">Add doctor</h2>
              <p className="text-sm text-muted-foreground">
                Create a doctor login, clinical profile, and optional contact details.
              </p>
            </div>
          </div>
          <span className="text-sm font-medium text-primary">{addDoctorOpen ? "Hide" : "Show"}</span>
        </button>

        {addDoctorOpen && (
          <div className="border-t border-border px-6 py-5">
            {addDoctorSuccess && (
              <p className="mb-4 rounded-md border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-900 dark:border-green-900 dark:bg-green-950/40 dark:text-green-100">
                {addDoctorSuccess}
              </p>
            )}
            {addDoctorError && (
              <p className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {addDoctorError}
              </p>
            )}
            <form onSubmit={submitAddDoctor} className="grid gap-4 sm:grid-cols-2">
              <label className="block sm:col-span-2">
                <span className="text-xs font-medium text-muted-foreground">Email *</span>
                <input
                  type="email"
                  required
                  value={doctorForm.email}
                  onChange={(e) => setDoctorForm((f) => ({ ...f, email: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  autoComplete="off"
                />
              </label>
              <label className="block sm:col-span-2">
                <span className="text-xs font-medium text-muted-foreground">Temporary password *</span>
                <input
                  type="password"
                  required
                  value={doctorForm.password}
                  onChange={(e) => setDoctorForm((f) => ({ ...f, password: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  autoComplete="new-password"
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-muted-foreground">First name *</span>
                <input
                  type="text"
                  required
                  value={doctorForm.first_name}
                  onChange={(e) => setDoctorForm((f) => ({ ...f, first_name: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-muted-foreground">Last name *</span>
                <input
                  type="text"
                  required
                  value={doctorForm.last_name}
                  onChange={(e) => setDoctorForm((f) => ({ ...f, last_name: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </label>
              <label className="block sm:col-span-2">
                <span className="text-xs font-medium text-muted-foreground">Phone</span>
                <input
                  type="text"
                  value={doctorForm.phone}
                  onChange={(e) => setDoctorForm((f) => ({ ...f, phone: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </label>
              <label className="block sm:col-span-2">
                <span className="text-xs font-medium text-muted-foreground">Specialization *</span>
                <input
                  type="text"
                  required
                  placeholder="e.g. Internal Medicine"
                  value={doctorForm.specialization}
                  onChange={(e) => setDoctorForm((f) => ({ ...f, specialization: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-muted-foreground">License number *</span>
                <input
                  type="text"
                  required
                  value={doctorForm.license_number}
                  onChange={(e) => setDoctorForm((f) => ({ ...f, license_number: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-muted-foreground">License state / region</span>
                <input
                  type="text"
                  placeholder="e.g. CA"
                  value={doctorForm.license_state}
                  onChange={(e) => setDoctorForm((f) => ({ ...f, license_state: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-muted-foreground">Department</span>
                <input
                  type="text"
                  value={doctorForm.department}
                  onChange={(e) => setDoctorForm((f) => ({ ...f, department: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-muted-foreground">Years of experience</span>
                <input
                  type="number"
                  min={0}
                  value={doctorForm.years_of_experience}
                  onChange={(e) => setDoctorForm((f) => ({ ...f, years_of_experience: e.target.value }))}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </label>
              <div className="flex items-end gap-2 sm:col-span-2">
                <button
                  type="submit"
                  disabled={addDoctorLoading}
                  className="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
                >
                  {addDoctorLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Creating…
                    </>
                  ) : (
                    "Create doctor account"
                  )}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>

      {/* Role summary cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-lg border border-blue-200 bg-blue-50/50 p-4 shadow-sm">
          <p className="text-sm font-medium text-blue-700">Patients</p>
          <p className="mt-1 text-3xl font-bold text-blue-800">{roleCounts.patient}</p>
        </div>
        <div className="rounded-lg border border-green-200 bg-green-50/50 p-4 shadow-sm">
          <p className="text-sm font-medium text-green-700">Doctors</p>
          <p className="mt-1 text-3xl font-bold text-green-800">{roleCounts.doctor}</p>
        </div>
        <div className="rounded-lg border border-purple-200 bg-purple-50/50 p-4 shadow-sm">
          <p className="text-sm font-medium text-purple-700">Nurses</p>
          <p className="mt-1 text-3xl font-bold text-purple-800">{roleCounts.nurse}</p>
        </div>
        <div className="rounded-lg border border-red-200 bg-red-50/50 p-4 shadow-sm">
          <p className="text-sm font-medium text-red-700">Admins</p>
          <p className="mt-1 text-3xl font-bold text-red-800">{roleCounts.admin}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name or email..."
          className="w-64 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="all">All roles</option>
          <option value="patient">Patients</option>
          <option value="doctor">Doctors</option>
          <option value="nurse">Nurses</option>
          <option value="admin">Admins</option>
        </select>
        <button
          type="button"
          onClick={fetchUsers}
          className="ml-auto rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-muted"
        >
          Refresh
        </button>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <span className="ml-3 text-sm text-muted-foreground">Loading users...</span>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
          <p className="text-sm text-destructive">{error}</p>
          <button type="button" onClick={fetchUsers} className="mt-2 text-sm font-medium text-primary hover:underline">
            Retry
          </button>
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-border bg-card py-16">
          <p className="text-lg font-medium text-foreground">No users found</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {search || roleFilter !== "all"
              ? "Try adjusting your search or filter."
              : "No user data available."}
          </p>
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="rounded-lg border border-border bg-card shadow-sm">
          <div className="border-b border-border px-6 py-2">
            <div className="grid grid-cols-[1.2fr_1.2fr_minmax(0,0.7fr)_minmax(0,0.7fr)_minmax(0,0.9fr)_minmax(0,0.7fr)_minmax(0,1fr)] gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <span>Name</span>
              <span>Email</span>
              <span>Role</span>
              <span>Status</span>
              <span>Last Login</span>
              <span>Joined</span>
              <span className="text-right">Actions</span>
            </div>
          </div>
          <div className="divide-y divide-border">
            {filtered.map((u) => (
              <div
                key={u.id}
                className="grid grid-cols-[1.2fr_1.2fr_minmax(0,0.7fr)_minmax(0,0.7fr)_minmax(0,0.9fr)_minmax(0,0.7fr)_minmax(0,1fr)] items-center gap-2 px-6 py-3 text-sm transition-colors hover:bg-muted/50"
              >
                <Link href={`/admin/users/${u.id}`} className="font-medium text-primary hover:underline">
                  {u.first_name} {u.last_name}
                </Link>
                <span className="truncate text-muted-foreground">{u.email ?? "N/A"}</span>
                <span>
                  <span
                    className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${ROLE_STYLES[u.role] ?? "bg-gray-100 text-gray-700"}`}
                  >
                    {u.role}
                  </span>
                </span>
                <span>
                  {u.is_active !== false ? (
                    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-green-700">
                      <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
                      Active
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-gray-500">
                      <span className="h-1.5 w-1.5 rounded-full bg-gray-400" />
                      Inactive
                    </span>
                  )}
                </span>
                <span className="text-xs text-muted-foreground">
                  {u.last_login_at ? new Date(u.last_login_at).toLocaleDateString() : "Never"}
                </span>
                <span className="text-xs text-muted-foreground">
                  {u.created_at ? new Date(u.created_at).toLocaleDateString() : "N/A"}
                </span>
                <div className="flex justify-end">
                  {u.role === "doctor" ? (
                    <button
                      type="button"
                      disabled={doctorToggleId === u.id}
                      onClick={() => void toggleDoctorActive(u)}
                      className={
                        u.is_active !== false
                          ? "rounded-md border border-red-200 px-2.5 py-1 text-xs font-medium text-red-700 hover:bg-red-50 disabled:opacity-50 dark:border-red-900 dark:hover:bg-red-950/40"
                          : "rounded-md border border-green-200 px-2.5 py-1 text-xs font-medium text-green-700 hover:bg-green-50 disabled:opacity-50 dark:border-green-900 dark:hover:bg-green-950/40"
                      }
                    >
                      {doctorToggleId === u.id
                        ? "…"
                        : u.is_active !== false
                          ? "Deactivate"
                          : "Activate"}
                    </button>
                  ) : (
                    <Link
                      href={`/admin/users/${u.id}`}
                      className="text-xs font-medium text-muted-foreground hover:text-foreground hover:underline"
                    >
                      View
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
