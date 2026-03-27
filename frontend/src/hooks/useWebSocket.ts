"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { connectSocket, disconnectSocket, getSocket } from "@/lib/socket";
import type { Socket } from "@/lib/socket";

interface UseWebSocketOptions {
  token?: string;
  autoConnect?: boolean;
  events?: Record<string, (...args: unknown[]) => void>;
}

export function useWebSocket({ token, autoConnect = true, events }: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    const s = getSocket();
    socketRef.current = s;
    const handleConnect = () => setIsConnected(true);
    const handleDisconnect = () => setIsConnected(false);
    s.on("connect", handleConnect);
    s.on("disconnect", handleDisconnect);
    if (events) {
      for (const [event, handler] of Object.entries(events)) { s.on(event, handler); }
    }
    if (autoConnect) { connectSocket(token); }
    return () => {
      s.off("connect", handleConnect);
      s.off("disconnect", handleDisconnect);
      if (events) {
        for (const [event, handler] of Object.entries(events)) { s.off(event, handler); }
      }
      disconnectSocket();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, autoConnect]);

  const connect = useCallback(() => connectSocket(token), [token]);
  const disconnect = useCallback(() => disconnectSocket(), []);
  const emit = useCallback((event: string, ...args: unknown[]) => socketRef.current?.emit(event, ...args), []);
  const on = useCallback((event: string, handler: (...args: unknown[]) => void) => socketRef.current?.on(event, handler), []);
  const off = useCallback((event: string, handler: (...args: unknown[]) => void) => socketRef.current?.off(event, handler), []);

  return { socket: socketRef.current, isConnected, connect, disconnect, emit, on, off };
}
