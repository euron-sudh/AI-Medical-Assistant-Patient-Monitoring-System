export default function TelemedicinePage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Telemedicine</h1>
        <p className="mt-1 text-muted-foreground">
          Join video consultations with your healthcare providers.
        </p>
      </div>

      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="flex flex-col items-center justify-center py-16 px-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
            <svg
              className="h-8 w-8 text-primary"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z"
              />
            </svg>
          </div>
          <h3 className="mt-4 text-lg font-semibold text-foreground">
            Video Consultations
          </h3>
          <p className="mt-2 max-w-md text-center text-sm text-muted-foreground">
            Connect with your doctor through secure, HD video calls. Share your
            screen to review reports and get real-time AI-assisted consultations.
          </p>
          <div className="mt-6">
            <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Coming Soon
            </span>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-4">
          <h4 className="text-sm font-semibold text-foreground">Upcoming Sessions</h4>
          <p className="mt-1 text-2xl font-bold text-primary">0</p>
          <p className="mt-1 text-xs text-muted-foreground">No sessions scheduled</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <h4 className="text-sm font-semibold text-foreground">Past Sessions</h4>
          <p className="mt-1 text-2xl font-bold text-foreground">0</p>
          <p className="mt-1 text-xs text-muted-foreground">No previous sessions</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <h4 className="text-sm font-semibold text-foreground">Session Quality</h4>
          <p className="mt-1 text-2xl font-bold text-green-600">--</p>
          <p className="mt-1 text-xs text-muted-foreground">No data available</p>
        </div>
      </div>
    </div>
  );
}
