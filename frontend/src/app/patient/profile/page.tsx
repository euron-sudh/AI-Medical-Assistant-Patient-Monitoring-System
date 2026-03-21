"use client";

import { useEffect, useState } from "react";
import { ApiKeyButton } from "@/components/shared/api-key-modal";
import apiClient from "@/lib/api-client";

interface UserProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  phone: string | null;
  is_active: boolean;
  email_verified: boolean;
  last_login_at: string | null;
  created_at: string;
  patient_profile?: {
    date_of_birth: string | null;
    gender: string | null;
    blood_type: string | null;
    height_cm: number | null;
    weight_kg: number | null;
    emergency_contact: Record<string, string> | null;
    insurance_info: Record<string, string> | null;
  };
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [apiKeyStatus, setApiKeyStatus] = useState<string>("Not configured");

  useEffect(() => {
    fetchProfile();
    checkApiKey();
  }, []);

  const fetchProfile = async () => {
    try {
      const res = await apiClient.get("/auth/me");
      setProfile(res.data?.user ?? res.data);
    } catch {
      // Fall back to localStorage
      try {
        const userStr = localStorage.getItem("user");
        if (userStr) {
          setProfile(JSON.parse(userStr));
        } else {
          setError("Unable to load profile. Please log in again.");
        }
      } catch {
        setError("Unable to load profile.");
      }
    } finally {
      setLoading(false);
    }
  };

  const checkApiKey = () => {
    const key = localStorage.getItem("euriApiKey");
    if (key && key.startsWith("euri-") && key.length > 20) {
      setApiKeyStatus("Configured (key set)");
    } else if (key) {
      setApiKeyStatus("Set but may be invalid");
    } else {
      setApiKeyStatus("Not configured");
    }
  };

  if (loading) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Profile</h1>
          <p className="mt-1 text-muted-foreground">Loading your profile...</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-12 text-center">
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Profile</h1>
        </div>
        <div className="rounded-lg border border-border bg-card p-12 text-center">
          <p className="text-sm text-destructive">{error ?? "Profile not available."}</p>
        </div>
      </div>
    );
  }

  const pp = profile.patient_profile;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Profile</h1>
        <p className="mt-1 text-muted-foreground">
          Manage your personal information and account settings.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Personal Information */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Personal Information</h2>
          <div className="mt-4 space-y-3">
            <InfoRow label="Name" value={`${profile.first_name} ${profile.last_name}`} />
            <InfoRow label="Email" value={profile.email} />
            <InfoRow label="Phone" value={profile.phone ?? "Not set"} />
            <InfoRow label="Role" value={profile.role} />
            {pp?.gender && <InfoRow label="Gender" value={pp.gender} />}
            {pp?.date_of_birth && (
              <InfoRow
                label="Date of Birth"
                value={new Date(pp.date_of_birth).toLocaleDateString()}
              />
            )}
            {pp?.blood_type && <InfoRow label="Blood Type" value={pp.blood_type} />}
          </div>
        </div>

        {/* Account Status */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Account Status</h2>
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Account Active</span>
              <span
                className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                  profile.is_active
                    ? "bg-green-100 text-green-700"
                    : "bg-red-100 text-red-700"
                }`}
              >
                <span
                  className={`inline-block h-1.5 w-1.5 rounded-full ${
                    profile.is_active ? "bg-green-500" : "bg-red-500"
                  }`}
                />
                {profile.is_active ? "Active" : "Inactive"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Email Verified</span>
              <span
                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                  profile.email_verified
                    ? "bg-green-100 text-green-700"
                    : "bg-amber-100 text-amber-700"
                }`}
              >
                {profile.email_verified ? "Verified" : "Pending"}
              </span>
            </div>
            <InfoRow
              label="Member Since"
              value={new Date(profile.created_at).toLocaleDateString()}
            />
            {profile.last_login_at && (
              <InfoRow
                label="Last Login"
                value={new Date(profile.last_login_at).toLocaleString()}
              />
            )}
          </div>
        </div>

        {/* Medical Details */}
        {pp && (
          <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-foreground">Medical Details</h2>
            <div className="mt-4 space-y-3">
              {pp.height_cm && (
                <InfoRow label="Height" value={`${pp.height_cm} cm`} />
              )}
              {pp.weight_kg && (
                <InfoRow label="Weight" value={`${pp.weight_kg} kg`} />
              )}
              {pp.emergency_contact && (
                <div>
                  <p className="text-sm text-muted-foreground">Emergency Contact</p>
                  <div className="mt-1 rounded-md bg-muted/50 p-2 text-sm text-foreground">
                    {Object.entries(pp.emergency_contact).map(([key, val]) => (
                      <p key={key}>
                        <span className="font-medium capitalize">
                          {key.replace("_", " ")}:
                        </span>{" "}
                        {val}
                      </p>
                    ))}
                  </div>
                </div>
              )}
              {pp.insurance_info && (
                <div>
                  <p className="text-sm text-muted-foreground">Insurance Info</p>
                  <div className="mt-1 rounded-md bg-muted/50 p-2 text-sm text-foreground">
                    {Object.entries(pp.insurance_info).map(([key, val]) => (
                      <p key={key}>
                        <span className="font-medium capitalize">
                          {key.replace("_", " ")}:
                        </span>{" "}
                        {val}
                      </p>
                    ))}
                  </div>
                </div>
              )}
              {!pp.height_cm &&
                !pp.weight_kg &&
                !pp.emergency_contact &&
                !pp.insurance_info && (
                  <p className="text-sm text-muted-foreground italic">
                    No additional medical details on file.
                  </p>
                )}
            </div>
          </div>
        )}

        {/* AI API Key Status */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">AI Features</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Configure your EURI API key to enable AI-powered features like symptom analysis,
            medical chat, and report reading.
          </p>
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">API Key Status</span>
              <span
                className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                  apiKeyStatus.includes("Configured")
                    ? "bg-green-100 text-green-700"
                    : "bg-amber-100 text-amber-700"
                }`}
              >
                <span
                  className={`inline-block h-1.5 w-1.5 rounded-full ${
                    apiKeyStatus.includes("Configured") ? "bg-green-500" : "bg-amber-500"
                  }`}
                />
                {apiKeyStatus}
              </span>
            </div>
            <div className="pt-1">
              <ApiKeyButton />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium text-foreground">{value}</span>
    </div>
  );
}
