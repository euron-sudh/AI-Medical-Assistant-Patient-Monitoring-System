export default function PatientsPage() {
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Patient List</h1>
          <p className="mt-1 text-muted-foreground">
            View and manage your assigned patients.
          </p>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            disabled
            placeholder="Search patients..."
            className="rounded-md border border-border bg-muted/50 px-4 py-2 text-sm"
          />
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="border-b border-border px-6 py-3">
          <div className="grid grid-cols-5 text-sm font-medium text-muted-foreground">
            <span>Patient Name</span>
            <span>Age / Gender</span>
            <span>Last Visit</span>
            <span>Status</span>
            <span>Actions</span>
          </div>
        </div>
        <div className="flex flex-col items-center justify-center py-12">
          <p className="text-sm text-muted-foreground">
            Patient data will appear here once the system is fully connected.
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
