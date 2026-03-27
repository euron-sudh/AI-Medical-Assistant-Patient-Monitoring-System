"use client";

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from "recharts";

interface DataPoint { timestamp: string; value: number; status?: "normal" | "warning" | "critical"; }
interface Threshold { value: number; label: string; color: string; }

interface VitalsLineChartProps {
  data: DataPoint[];
  title: string;
  unit: string;
  color?: string;
  thresholds?: Threshold[];
  height?: number;
  showGrid?: boolean;
}

const STATUS_COLORS: Record<string, string> = { normal: "#22c55e", warning: "#eab308", critical: "#ef4444" };

function formatTime(ts: string): string {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function VitalsLineChart({ data, title, unit, color = "#6366f1", thresholds = [], height = 250, showGrid = true }: VitalsLineChartProps) {
  const chartData = data.map((d) => ({ ...d, time: formatTime(d.timestamp) }));

  return (
    <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        <span className="text-xs text-muted-foreground">{unit}</span>
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" className="opacity-30" />}
          <XAxis dataKey="time" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} width={40} />
          <Tooltip />
          {thresholds.map((t) => (
            <ReferenceLine key={t.label} y={t.value} stroke={t.color} strokeDasharray="5 5" />
          ))}
          <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
