export default function MonitoringPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Patient Monitoring</h1>
        <p className="mt-1 text-muted-foreground">
          Real-time vital sign monitoring wall for all assigned patients.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-green-500" />
            <span className="text-sm font-medium text-foreground">Normal</span>
          </div>
          <p className="mt-1 text-2xl font-bold text-foreground">0</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-amber-500" />
            <span className="text-sm font-medium text-foreground">Warning</span>
          </div>
          <p className="mt-1 text-2xl font-bold text-foreground">0</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-red-500" />
            <span className="text-sm font-medium text-foreground">Critical</span>
          </div>
          <p className="mt-1 text-2xl font-bold text-foreground">0</p>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">Monitoring Wall</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Real-time patient monitoring cards will display here with live vitals,
          color-coded status indicators, and alert notifications via WebSocket connections.
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
