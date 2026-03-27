"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend } from "recharts";

interface BPReading { timestamp: string; systolic: number; diastolic: number; }

function classifyBP(sys: number, dia: number): "normal" | "warning" | "critical" {
  if (sys >= 180 || dia >= 120) return "critical";
  if (sys >= 140 || dia >= 90) return "warning";
  if (sys < 90 || dia < 60) return "warning";
  return "normal";
}

const STATUS_COLORS: Record<string, string> = { normal: "#22c55e", warning: "#eab308", critical: "#ef4444" };

export default function BloodPressureChart({ data, height = 250 }: { data: BPReading[]; height?: number }) {
  const chartData = data.map((d) => ({
    ...d,
    time: new Date(d.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    bpStatus: classifyBP(d.systolic, d.diastolic),
  }));

  return (
    <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">Blood Pressure</h3>
        <span className="text-xs text-muted-foreground">mmHg</span>
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
          <XAxis dataKey="time" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} width={40} domain={[40, 200]} />
          <Tooltip />
          <Legend wrapperStyle={{ fontSize: "12px" }} iconType="line" />
          <ReferenceLine y={140} stroke="#eab308" strokeDasharray="5 5" />
          <ReferenceLine y={90} stroke="#94a3b8" strokeDasharray="5 5" />
          <Line type="monotone" dataKey="systolic" name="systolic" stroke="#ef4444" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} />
          <Line type="monotone" dataKey="diastolic" name="diastolic" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
