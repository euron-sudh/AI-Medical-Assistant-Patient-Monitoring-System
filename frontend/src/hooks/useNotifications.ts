"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import apiClient from "@/lib/api-client";

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string;
  type: "info" | "warning" | "success" | "error";
  is_read: boolean;
  created_at: string;
  read_at: string | null;
  link: string | null;
}

export function useNotifications({ pollingInterval = 0, enabled = true }: { pollingInterval?: number; enabled?: boolean } = {}) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchNotifications = useCallback(async () => {
    if (!enabled) return;
    try {
      setIsLoading(true);
      const res = await apiClient.get("/notifications");
      const data = res.data.notifications ?? res.data ?? [];
      setNotifications(Array.isArray(data) ? data : []);
      setError(null);
    } catch {
      setError("Failed to load notifications.");
    } finally {
      setIsLoading(false);
    }
  }, [enabled]);

  useEffect(() => { if (enabled) fetchNotifications(); }, [fetchNotifications, enabled]);

  useEffect(() => {
    if (pollingInterval > 0 && enabled) intervalRef.current = setInterval(fetchNotifications, pollingInterval);
    return () => { if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; } };
  }, [pollingInterval, fetchNotifications, enabled]);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const markAsRead = useCallback(async (notificationId: string) => {
    try {
      await apiClient.put(`/notifications/${notificationId}/read`);
      setNotifications((prev) => prev.map((n) => n.id === notificationId ? { ...n, is_read: true, read_at: new Date().toISOString() } : n));
    } catch { /* Silently handle */ }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      await apiClient.put("/notifications/read-all");
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true, read_at: n.read_at ?? new Date().toISOString() })));
    } catch { /* Silently handle */ }
  }, []);

  return { notifications, unreadCount, isLoading, error, refetch: fetchNotifications, markAsRead, markAllAsRead };
}
