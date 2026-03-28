"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { loginSchema, type LoginFormData } from "@/lib/validators";
import apiClient from "@/lib/api-client";
import type { LoginResponse } from "@/types/auth";
import { GoogleSignIn } from "./google-sign-in";

export function LoginForm() {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

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
        const responseData = (error.response as { data: Record<string, unknown> }).data;
        const msg = (responseData?.error as Record<string, unknown>)?.message ?? responseData?.message ?? "Login failed. Please try again.";
        setServerError(String(msg));
      } else {
        setServerError("An unexpected error occurred. Please try again.");
      }
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      {/* Server error */}
      {serverError && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          {serverError}
        </div>
      )}

      {/* Email */}
      <div className="space-y-1.5">
        <label htmlFor="email" className="block text-sm font-medium text-gray-700">
          Email address
        </label>
        <div className="relative">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5">
            <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
            </svg>
          </div>
          <input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            className="w-full rounded-lg border border-gray-300 bg-white py-2.5 pl-10 pr-3 text-sm text-gray-900 placeholder:text-gray-400 transition-all duration-200 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            {...register("email")}
          />
        </div>
        {errors.email && (
          <p className="text-xs text-red-600">{errors.email.message}</p>
        )}
      </div>

      {/* Password */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label htmlFor="password" className="block text-sm font-medium text-gray-700">
            Password
          </label>
          <Link
            href="/forgot-password"
            className="text-xs font-medium text-blue-600 transition-colors hover:text-teal-600"
          >
            Forgot password?
          </Link>
        </div>
        <div className="relative">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5">
            <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
            </svg>
          </div>
          <input
            id="password"
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
            placeholder="Enter your password"
            className="w-full rounded-lg border border-gray-300 bg-white py-2.5 pl-10 pr-10 text-sm text-gray-900 placeholder:text-gray-400 transition-all duration-200 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            {...register("password")}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute inset-y-0 right-0 flex items-center pr-3.5 text-gray-400 transition-colors hover:text-gray-600"
            tabIndex={-1}
          >
            {showPassword ? (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
              </svg>
            ) : (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            )}
          </button>
        </div>
        {errors.password && (
          <p className="text-xs text-red-600">{errors.password.message}</p>
        )}
      </div>

      {/* Sign in button */}
      <button
        type="submit"
        disabled={isSubmitting}
        className="relative w-full overflow-hidden rounded-lg bg-gradient-to-r from-blue-600 to-teal-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-blue-500/20 transition-all duration-300 hover:from-blue-700 hover:to-teal-700 hover:shadow-lg hover:shadow-blue-500/30 disabled:cursor-not-allowed disabled:opacity-50 active:scale-[0.98]"
      >
        {isSubmitting ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Signing in...
          </span>
        ) : (
          "Sign in"
        )}
      </button>

      {/* Divider */}
      <div className="relative my-1">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t border-gray-200" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-white px-3 text-gray-400">Or continue with</span>
        </div>
      </div>

      {/* Google Sign-In */}
      <GoogleSignIn
        text="signin_with"
        onError={(msg) => setServerError(msg)}
      />

      {/* Watch Product Demo */}
      <Link
        href="/demo"
        className="group flex w-full items-center justify-center gap-2.5 rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 shadow-sm transition-all duration-200 hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700"
      >
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-r from-blue-500 to-teal-500 transition-transform duration-300 group-hover:scale-110">
          <svg className="ml-0.5 h-3 w-3 text-white" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8 5v14l11-7z" />
          </svg>
        </span>
        Watch Product Demo
      </Link>

      {/* Demo accounts */}
      <div className="rounded-xl border border-gray-100 bg-gray-50/50 p-4">
        <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-400">
          Demo Accounts
        </p>
        <div className="space-y-2">
          <button
            type="button"
            onClick={() => fillTestCredentials("sarah.johnson@medassist.ai", "Demo1234!")}
            className="group flex w-full items-center gap-3 rounded-lg border border-gray-100 bg-white px-3 py-2.5 text-left transition-all duration-200 hover:border-blue-200 hover:shadow-sm"
          >
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-blue-100 text-xs font-bold text-blue-600">
              P
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-900">Patient</span>
                <span className="rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-600">
                  PATIENT
                </span>
              </div>
              <p className="truncate text-xs text-gray-400">sarah.johnson@medassist.ai</p>
            </div>
            <svg className="h-4 w-4 shrink-0 text-gray-300 transition-colors group-hover:text-blue-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
          </button>

          <button
            type="button"
            onClick={() => fillTestCredentials("priya.sharma@medassist.ai", "Demo1234!")}
            className="group flex w-full items-center gap-3 rounded-lg border border-gray-100 bg-white px-3 py-2.5 text-left transition-all duration-200 hover:border-emerald-200 hover:shadow-sm"
          >
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-emerald-100 text-xs font-bold text-emerald-600">
              D
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-900">Doctor</span>
                <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-600">
                  DOCTOR
                </span>
              </div>
              <p className="truncate text-xs text-gray-400">priya.sharma@medassist.ai</p>
            </div>
            <svg className="h-4 w-4 shrink-0 text-gray-300 transition-colors group-hover:text-emerald-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
          </button>

          <button
            type="button"
            onClick={() => fillTestCredentials("admin@medassist.ai", "Demo1234!")}
            className="group flex w-full items-center gap-3 rounded-lg border border-gray-100 bg-white px-3 py-2.5 text-left transition-all duration-200 hover:border-purple-200 hover:shadow-sm"
          >
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-purple-100 text-xs font-bold text-purple-600">
              A
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-900">Admin</span>
                <span className="rounded-full bg-purple-50 px-2 py-0.5 text-[10px] font-semibold text-purple-600">
                  ADMIN
                </span>
              </div>
              <p className="truncate text-xs text-gray-400">admin@medassist.ai</p>
            </div>
            <svg className="h-4 w-4 shrink-0 text-gray-300 transition-colors group-hover:text-purple-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
          </button>
        </div>
        <p className="mt-3 text-center text-[11px] text-gray-400">
          Click any card to auto-fill credentials
        </p>
      </div>
    </form>
  );
}
