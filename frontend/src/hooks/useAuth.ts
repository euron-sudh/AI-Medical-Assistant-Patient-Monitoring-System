"use client";

import { useState, useEffect, useCallback } from "react";
import apiClient from "@/lib/api-client";
import type { User, LoginRequest, LoginResponse } from "@/types/auth";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null, isAuthenticated: false, isLoading: true, error: null,
  });

  useEffect(() => {
    try {
      const token = localStorage.getItem("accessToken");
      const storedUser = localStorage.getItem("user");
      if (token && storedUser) {
        const user = JSON.parse(storedUser) as User;
        setState({ user, isAuthenticated: true, isLoading: false, error: null });
      } else {
        setState((prev) => ({ ...prev, isLoading: false }));
      }
    } catch {
      setState((prev) => ({ ...prev, isLoading: false }));
    }
  }, []);

  const login = useCallback(async (credentials: LoginRequest) => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const { data } = await apiClient.post<LoginResponse>("/auth/login", credentials);
      localStorage.setItem("accessToken", data.access_token);
      localStorage.setItem("refreshToken", data.refresh_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      setState({ user: data.user, isAuthenticated: true, isLoading: false, error: null });
      return data;
    } catch (err: unknown) {
      const message = (err as { response?: { data?: { message?: string } } })?.response?.data?.message ?? "Login failed.";
      setState((prev) => ({ ...prev, isLoading: false, error: message }));
      throw err;
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("user");
    setState({ user: null, isAuthenticated: false, isLoading: false, error: null });
    if (typeof window !== "undefined") window.location.href = "/login";
  }, []);

  const updateUser = useCallback((updatedUser: User) => {
    localStorage.setItem("user", JSON.stringify(updatedUser));
    setState((prev) => ({ ...prev, user: updatedUser }));
  }, []);

  const getToken = useCallback((): string | null => localStorage.getItem("accessToken"), []);

  return { user: state.user, isAuthenticated: state.isAuthenticated, isLoading: state.isLoading, error: state.error, login, logout, updateUser, getToken };
}
