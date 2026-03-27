"use client";

interface SpO2GaugeProps { value: number; size?: number; showLabel?: boolean; }

function getSpO2Status(value: number) {
  if (value >= 95) return { color: "#22c55e", bgColor: "bg-green-50", label: "Normal" };
  if (value >= 90) return { color: "#eab308", bgColor: "bg-yellow-50", label: "Low" };
  return { color: "#ef4444", bgColor: "bg-red-50", label: "Critical" };
}

export default function SpO2Gauge({ value, size = 160, showLabel = true }: SpO2GaugeProps) {
  const { color, bgColor, label } = getSpO2Status(value);
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const center = size / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, value));
  const offset = circumference - (clamped / 100) * circumference;

  return (
    <div className={`flex flex-col items-center rounded-lg border border-border ${bgColor} p-4 shadow-sm`}>
      {showLabel && <h3 className="mb-2 text-sm font-semibold text-foreground">SpO2 Level</h3>}
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle cx={center} cy={center} r={radius} fill="none" stroke="#e2e8f0" strokeWidth={strokeWidth} />
          <circle cx={center} cy={center} r={radius} fill="none" stroke={color} strokeWidth={strokeWidth}
            strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round"
            className="transition-all duration-700 ease-in-out" />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold" style={{ color }}>{value}%</span>
          <span className="text-xs font-medium" style={{ color }}>{label}</span>
        </div>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">Oxygen Saturation</p>
    </div>
  );
}
