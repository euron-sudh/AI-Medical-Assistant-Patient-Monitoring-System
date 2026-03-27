"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { loginSchema, type LoginFormData } from "@/lib/validators";
import apiClient from "@/lib/api-client";
import type { LoginResponse, AuthError } from "@/types/auth";

export function LoginForm() {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const fillTestCredentials = (email: string, password: string) => {
    setValue("email", email);
    setValue("password", password);
    setServerError(null);
  };

  const onSubmit = async (data: LoginFormData) => {
    setServerError(null);

    try {
      const response = await apiClient.post<LoginResponse>("/auth/login", {
        email: data.email,
        password: data.password,
      });

      const { access_token, refresh_token, user } = response.data;
      localStorage.setItem("accessToken", access_token);
      localStorage.setItem("refreshToken", refresh_token);
      localStorage.setItem("user", JSON.stringify(user));

      const role = user.role;
      const redirectMap: Record<string, string> = {
        patient: "/patient/dashboard",
        doctor: "/doctor/dashboard",
        nurse: "/doctor/dashboard",
        admin: "/admin/dashboard",
      };
      router.push(redirectMap[role] ?? "/");
    } catch (error: unknown) {
      if (
        error &&
        typeof error === "object" &&
        "response" in error &&
        error.response &&
        typeof error.response === "object" &&
        "data" in error.response
      ) {
        const authError = (error.response as { data: AuthError }).data;
        setServerError(authError.message ?? "Login failed. Please try again.");
      } else {
        setServerError("An unexpected error occurred. Please try again.");
      }
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {serverError && (
        <div className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {serverError}
        </div>
      )}

      <div className="space-y-2">
        <label
          htmlFor="email"
          className="block text-sm font-medium text-foreground"
        >
          Email
        </label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          {...register("email")}
        />
        {errors.email && (
          <p className="text-sm text-destructive">{errors.email.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <label
          htmlFor="password"
          className="block text-sm font-medium text-foreground"
        >
          Password
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          placeholder="Enter your password"
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          {...register("password")}
        />
        {errors.password && (
          <p className="text-sm text-destructive">{errors.password.message}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isSubmitting ? "Signing in..." : "Sign in"}
      </button>

      <Link
        href="/demo"
        className="flex w-full items-center justify-center gap-2 rounded-md border border-primary/30 bg-primary/5 px-4 py-2.5 text-sm font-medium text-primary transition-colors hover:bg-primary/10 hover:border-primary/50"
      >
        <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8 5v14l11-7z" />
        </svg>
        Watch Product Demo
      </Link>

      {process.env.NODE_ENV !== 'production' && (
        <div className="mt-6 rounded-md border border-border bg-muted/50 p-4">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Test Accounts (click to fill)
          </p>
          <div className="space-y-2">
            <button
              type="button"
              onClick={() => fillTestCredentials("patient@demo.dev", "Demo1234!")}
              className="flex w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-left text-sm hover:bg-accent"
            >
              <div>
                <span className="font-medium text-foreground">Patient</span>
                <span className="ml-2 text-muted-foreground">patient@demo.dev</span>
              </div>
              <span className="text-xs text-muted-foreground">Demo1234!</span>
            </button>
            <button
              type="button"
              onClick={() => fillTestCredentials("doctor@demo.dev", "Demo1234!")}
              className="flex w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-left text-sm hover:bg-accent"
            >
              <div>
                <span className="font-medium text-foreground">Doctor</span>
                <span className="ml-2 text-muted-foreground">doctor@demo.dev</span>
              </div>
              <span className="text-xs text-muted-foreground">Demo1234!</span>
            </button>
            <button
              type="button"
              onClick={() => fillTestCredentials("admin@demo.dev", "Demo1234!")}
              className="flex w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-left text-sm hover:bg-accent"
            >
              <div>
                <span className="font-medium text-foreground">Admin</span>
                <span className="ml-2 text-muted-foreground">admin@demo.dev</span>
              </div>
              <span className="text-xs text-muted-foreground">Demo1234!</span>
            </button>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            Register new accounts at <a href="/register" className="underline hover:text-foreground">/register</a>
          </p>
        </div>
      )}
    </form>
  );
}
