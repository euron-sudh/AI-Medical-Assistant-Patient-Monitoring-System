"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import apiClient from "@/lib/api-client";

// Google Client ID — set via env var or use this default for development
const GOOGLE_CLIENT_ID =
  process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ||
  "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com";

interface GoogleSignInProps {
  onError?: (error: string) => void;
  text?: "signin_with" | "signup_with" | "continue_with";
}

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: Record<string, unknown>) => void;
          renderButton: (element: HTMLElement, config: Record<string, unknown>) => void;
          prompt: () => void;
        };
      };
    };
  }
}

export function GoogleSignIn({ onError, text = "signin_with" }: GoogleSignInProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [scriptLoaded, setScriptLoaded] = useState(false);

  const handleCredentialResponse = useCallback(
    async (response: { credential: string }) => {
      setLoading(true);
      try {
        const res = await apiClient.post("/auth/google", {
          credential: response.credential,
        });

        const { access_token, refresh_token, user } = res.data;

        // Store tokens and user data
        localStorage.setItem("accessToken", access_token);
        localStorage.setItem("refreshToken", refresh_token);
        localStorage.setItem("user", JSON.stringify(user));

        // Redirect based on role
        const roleRoutes: Record<string, string> = {
          patient: "/patient/dashboard",
          doctor: "/doctor/dashboard",
          admin: "/admin/dashboard",
          nurse: "/doctor/dashboard",
        };
        router.push(roleRoutes[user.role] || "/patient/dashboard");
      } catch (err: unknown) {
        const message =
          err &&
          typeof err === "object" &&
          "response" in err &&
          err.response &&
          typeof err.response === "object" &&
          "data" in err.response
            ? (err.response as { data: { error?: { message?: string } } }).data
                ?.error?.message || "Google sign-in failed"
            : "Google sign-in failed. Please try again.";
        onError?.(message);
      } finally {
        setLoading(false);
      }
    },
    [router, onError]
  );

  useEffect(() => {
    // Load Google Identity Services script
    if (document.getElementById("google-gsi-script")) {
      setScriptLoaded(true);
      return;
    }

    const script = document.createElement("script");
    script.id = "google-gsi-script";
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => setScriptLoaded(true);
    document.head.appendChild(script);
  }, []);

  useEffect(() => {
    if (!scriptLoaded || !window.google) return;

    // Only render if we have a real client ID
    if (GOOGLE_CLIENT_ID.includes("YOUR_GOOGLE")) return;

    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: handleCredentialResponse,
      auto_select: false,
    });

    const buttonElement = document.getElementById("google-signin-button");
    if (buttonElement) {
      window.google.accounts.id.renderButton(buttonElement, {
        type: "standard",
        theme: "outline",
        size: "large",
        text,
        width: "100%",
        shape: "rectangular",
      });
    }
  }, [scriptLoaded, handleCredentialResponse, text]);

  if (GOOGLE_CLIENT_ID.includes("YOUR_GOOGLE")) {
    // No Google Client ID configured — show a styled placeholder button
    return (
      <button
        type="button"
        disabled
        className="flex w-full items-center justify-center gap-3 rounded-md border border-border bg-background px-4 py-2.5 text-sm font-medium text-muted-foreground opacity-60 cursor-not-allowed"
        title="Google Sign-In not configured. Set NEXT_PUBLIC_GOOGLE_CLIENT_ID environment variable."
      >
        <svg className="h-5 w-5" viewBox="0 0 24 24">
          <path
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
            fill="#4285F4"
          />
          <path
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            fill="#34A853"
          />
          <path
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            fill="#FBBC05"
          />
          <path
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            fill="#EA4335"
          />
        </svg>
        Sign in with Google
      </button>
    );
  }

  return (
    <div className="w-full">
      {loading && (
        <div className="flex items-center justify-center py-2.5">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <span className="ml-2 text-sm text-muted-foreground">Signing in with Google...</span>
        </div>
      )}
      <div
        id="google-signin-button"
        className={`flex justify-center ${loading ? "hidden" : ""}`}
      />
    </div>
  );
}
