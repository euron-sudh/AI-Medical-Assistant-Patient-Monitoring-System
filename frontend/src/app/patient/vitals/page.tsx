export default function VitalsPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">My Vitals</h1>
        <p className="mt-1 text-muted-foreground">
          Track and monitor your vital signs over time.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Heart Rate", value: "--", unit: "bpm", color: "bg-red-100 text-red-600" },
          { label: "Blood Pressure", value: "--/--", unit: "mmHg", color: "bg-blue-100 text-blue-600" },
          { label: "SpO2", value: "--", unit: "%", color: "bg-cyan-100 text-cyan-600" },
          { label: "Temperature", value: "--", unit: "°F", color: "bg-orange-100 text-orange-600" },
        ].map((vital) => (
          <div key={vital.label} className="rounded-lg border border-border bg-card p-6 shadow-sm">
            <p className="text-sm font-medium text-muted-foreground">{vital.label}</p>
            <p className="mt-2 text-3xl font-bold text-foreground">
              {vital.value}
              <span className="ml-1 text-sm font-normal text-muted-foreground">{vital.unit}</span>
            </p>
          </div>
        ))}
      </div>

      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">Vitals History</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          No vitals readings recorded yet. Log your vitals manually or connect a monitoring device
          to start tracking your health trends.
        </p>
        <div className="mt-4">
          <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
            Coming Soon
          </span>
        </div>
      </div>
    </div>
  );
}
