export default function ProfilePage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Profile</h1>
        <p className="mt-1 text-muted-foreground">
          Manage your personal information, medical history, and notification preferences.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Personal Information</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Update your name, contact details, emergency contacts, and insurance information.
          </p>
          <div className="mt-4">
            <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Coming Soon
            </span>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Medical History</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            View and update your medical history, allergies, and pre-existing conditions.
          </p>
          <div className="mt-4">
            <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Coming Soon
            </span>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Notification Preferences</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Configure how and when you receive notifications for appointments, medications,
            and health updates.
          </p>
          <div className="mt-4">
            <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Coming Soon
            </span>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Connected Devices</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Manage your connected health monitoring devices and wearables.
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
