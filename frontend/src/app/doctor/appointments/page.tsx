export default function DoctorAppointmentsPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Appointments</h1>
        <p className="mt-1 text-muted-foreground">
          Manage your appointment schedule and patient consultations.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Today</p>
          <p className="mt-2 text-3xl font-bold text-foreground">0</p>
          <p className="mt-1 text-xs text-muted-foreground">appointments</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">This Week</p>
          <p className="mt-2 text-3xl font-bold text-foreground">0</p>
          <p className="mt-1 text-xs text-muted-foreground">scheduled</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Pending Review</p>
          <p className="mt-2 text-3xl font-bold text-foreground">0</p>
          <p className="mt-1 text-xs text-muted-foreground">follow-ups</p>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">Schedule</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Your appointment calendar and schedule management will appear here.
          Supports in-person, telemedicine, follow-up, and emergency appointment types.
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
