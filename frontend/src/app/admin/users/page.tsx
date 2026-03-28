"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import apiClient from "@/lib/api-client";
// lucide-react icons available if needed

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

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("all");

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);

      // Try admin endpoint first, then fall back to combining patients + doctors
      let allUsers: User[] = [];
      try {
        const res = await apiClient.get("/admin/users");
        const data = res.data.users ?? res.data ?? [];
        allUsers = Array.isArray(data) ? data : [];
      } catch {
        // Fall back to combining patient and doctor lists
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
              }))
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
              }))
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
          <button onClick={fetchUsers} className="mt-2 text-sm font-medium text-primary hover:underline">
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
            <div className="grid grid-cols-6 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <span>Name</span>
              <span>Email</span>
              <span>Role</span>
              <span>Status</span>
              <span>Last Login</span>
              <span>Joined</span>
            </div>
          </div>
          <div className="divide-y divide-border">
            {filtered.map((u) => (
              <Link
                key={u.id}
                href={`/admin/users/${u.id}`}
                className="grid grid-cols-6 items-center px-6 py-3 text-sm transition-colors hover:bg-muted/50 cursor-pointer"
              >
                <span className="font-medium text-foreground">
                  {u.first_name} {u.last_name}
                </span>
                <span className="text-muted-foreground">{u.email ?? "N/A"}</span>
                <span>
                  <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${ROLE_STYLES[u.role] ?? "bg-gray-100 text-gray-700"}`}>
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
                  {u.last_login_at
                    ? new Date(u.last_login_at).toLocaleDateString()
                    : "Never"}
                </span>
                <span className="text-xs text-muted-foreground">
                  {u.created_at
                    ? new Date(u.created_at).toLocaleDateString()
                    : "N/A"}
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
