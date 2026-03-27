"use client";

import VitalsLineChart from "./VitalsLineChart";

interface HeartRateReading { timestamp: string; value: number; status?: "normal" | "warning" | "critical"; }

function classifyHeartRate(value: number): "normal" | "warning" | "critical" {
  if (value < 40 || value > 150) return "critical";
  if (value < 60 || value > 100) return "warning";
  return "normal";
}

export default function HeartRateChart({ data, height = 250 }: { data: HeartRateReading[]; height?: number }) {
  const enriched = data.map((d) => ({ ...d, status: d.status ?? classifyHeartRate(d.value) }));
  return (
    <VitalsLineChart data={enriched} title="Heart Rate" unit="bpm" color="#ef4444" height={height}
      thresholds={[
        { value: 100, label: "High", color: "#eab308" },
        { value: 60, label: "Low", color: "#eab308" },
        { value: 150, label: "Critical High", color: "#ef4444" },
        { value: 40, label: "Critical Low", color: "#ef4444" },
      ]} />
  );
}
