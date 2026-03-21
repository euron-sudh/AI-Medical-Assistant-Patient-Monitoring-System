export default function AuditLogsPage() {
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Audit Logs</h1>
          <p className="mt-1 text-muted-foreground">
            HIPAA compliance audit trail - immutable record of all PHI access.
          </p>
        </div>
        <button
          disabled
          className="rounded-md border border-border bg-card px-4 py-2 text-sm font-medium text-foreground opacity-50"
        >
          Export CSV
        </button>
      </div>

      <div className="grid gap-6 md:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Total Events</p>
          <p className="mt-2 text-3xl font-bold text-foreground">0</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Today</p>
          <p className="mt-2 text-3xl font-bold text-foreground">0</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">PHI Access Events</p>
          <p className="mt-2 text-3xl font-bold text-foreground">0</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Denied Access</p>
          <p className="mt-2 text-3xl font-bold text-red-600">0</p>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="border-b border-border px-6 py-3">
          <div className="grid grid-cols-6 text-sm font-medium text-muted-foreground">
            <span>Timestamp</span>
            <span>User</span>
            <span>Action</span>
            <span>Resource</span>
            <span>IP Address</span>
            <span>Status</span>
          </div>
        </div>
        <div className="flex flex-col items-center justify-center py-12">
          <p className="text-sm text-muted-foreground">
            Audit log entries will appear here. Logs are immutable and retained for 6+ years per HIPAA.
          </p>
          <div className="mt-4">
            <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Coming Soon
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
