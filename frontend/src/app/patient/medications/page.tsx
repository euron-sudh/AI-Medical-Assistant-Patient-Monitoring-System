export default function MedicationsPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Medications</h1>
        <p className="mt-1 text-muted-foreground">
          View your active medications, dosage schedules, and interaction alerts.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Active Medications</p>
          <p className="mt-2 text-3xl font-bold text-foreground">0</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Refills Needed</p>
          <p className="mt-2 text-3xl font-bold text-foreground">0</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Interaction Alerts</p>
          <p className="mt-2 text-3xl font-bold text-green-600">None</p>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">Medication List</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          No active medications on file. Your prescribed medications and dosage schedules will appear here.
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
