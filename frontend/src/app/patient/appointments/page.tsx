export default function AppointmentsPage() {
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Appointments</h1>
          <p className="mt-1 text-muted-foreground">
            Schedule and manage your upcoming appointments.
          </p>
        </div>
        <button
          disabled
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground opacity-50"
        >
          Book Appointment
        </button>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Upcoming</h2>
          <p className="mt-4 text-sm text-muted-foreground">
            No upcoming appointments scheduled. Book an appointment with your care team
            for in-person visits or telemedicine consultations.
          </p>
          <div className="mt-4">
            <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Coming Soon
            </span>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Past Appointments</h2>
          <p className="mt-4 text-sm text-muted-foreground">
            Your appointment history will appear here, including visit notes
            and follow-up recommendations.
          </p>
        </div>
      </div>
    </div>
  );
}
