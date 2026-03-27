"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import apiClient from "@/lib/api-client";

export interface VitalReading {
  id: string;
  patient_id: string;
  vital_type: string;
  value: number;
  unit: string;
  recorded_at: string;
  status: "normal" | "warning" | "critical";
}

export interface VitalsData {
  heart_rate: VitalReading[];
  blood_pressure_systolic: VitalReading[];
  blood_pressure_diastolic: VitalReading[];
  spo2: VitalReading[];
  temperature: VitalReading[];
  respiratory_rate: VitalReading[];
}

interface UseVitalsOptions {
  patientId: string;
  pollingInterval?: number;
  enabled?: boolean;
}

const EMPTY_VITALS: VitalsData = {
  heart_rate: [], blood_pressure_systolic: [], blood_pressure_diastolic: [],
  spo2: [], temperature: [], respiratory_rate: [],
};

export function useVitals({ patientId, pollingInterval = 0, enabled = true }: UseVitalsOptions) {
  const [vitals, setVitals] = useState<VitalsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchVitals = useCallback(async () => {
    if (!patientId || !enabled) return;
    try {
      setIsLoading(true);
      const { data } = await apiClient.get(`/vitals/${patientId}`);
      if (data && typeof data === "object") {
        setVitals({
          heart_rate: data.heart_rate ?? data.heartRate ?? [],
          blood_pressure_systolic: data.blood_pressure_systolic ?? data.bloodPressureSystolic ?? [],
          blood_pressure_diastolic: data.blood_pressure_diastolic ?? data.bloodPressureDiastolic ?? [],
          spo2: data.spo2 ?? data.spO2 ?? [],
          temperature: data.temperature ?? [],
          respiratory_rate: data.respiratory_rate ?? data.respiratoryRate ?? [],
        });
      } else {
        setVitals(EMPTY_VITALS);
      }
      setError(null);
    } catch {
      setError("Failed to fetch vitals data.");
    } finally {
      setIsLoading(false);
    }
  }, [patientId, enabled]);

  useEffect(() => {
    if (enabled && patientId) fetchVitals();
  }, [fetchVitals, enabled, patientId]);

  useEffect(() => {
    if (pollingInterval > 0 && enabled && patientId) {
      intervalRef.current = setInterval(fetchVitals, pollingInterval);
    }
    return () => {
      if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
    };
  }, [pollingInterval, fetchVitals, enabled, patientId]);

  const latestVitals: Record<string, VitalReading | null> = {};
  if (vitals) {
    for (const [key, readings] of Object.entries(vitals)) {
      if (Array.isArray(readings) && readings.length > 0) {
        const sorted = [...readings].sort((a, b) => new Date(b.recorded_at).getTime() - new Date(a.recorded_at).getTime());
        latestVitals[key] = sorted[0];
      } else {
        latestVitals[key] = null;
      }
    }
  }

  return { vitals, latestVitals, isLoading, error, refetch: fetchVitals };
}
