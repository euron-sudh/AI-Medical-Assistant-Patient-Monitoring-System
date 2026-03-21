export default function AlertsPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Alert Summary</h1>
        <p className="mt-1 text-muted-foreground">
          Overview of all patient monitoring alerts and escalation metrics.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Active Alerts</p>
          <p className="mt-2 text-3xl font-bold text-foreground">0</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Critical</p>
          <p className="mt-2 text-3xl font-bold text-red-600">0</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Escalated</p>
          <p className="mt-2 text-3xl font-bold text-amber-600">0</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Resolved (Today)</p>
          <p className="mt-2 text-3xl font-bold text-green-600">0</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Alert Feed</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Real-time alert feed showing active, acknowledged, and escalated alerts
            across all monitored patients.
          </p>
          <div className="mt-4">
            <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Coming Soon
            </span>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Response Metrics</h2>
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Mean Time to Acknowledge</span>
              <span className="text-sm font-medium text-muted-foreground">N/A</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Mean Time to Resolve</span>
              <span className="text-sm font-medium text-muted-foreground">N/A</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Escalation Rate</span>
              <span className="text-sm font-medium text-muted-foreground">N/A</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">SLA Compliance</span>
              <span className="text-sm font-medium text-muted-foreground">N/A</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
