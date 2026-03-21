export default function TelemedicinePage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Telemedicine</h1>
        <p className="mt-1 text-muted-foreground">
          Conduct video consultations with patients via secure WebRTC connections.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Upcoming Sessions</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            No telemedicine sessions scheduled. Sessions will appear here when
            patients book telemedicine appointments.
          </p>
          <div className="mt-4">
            <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Coming Soon
            </span>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Features</h2>
          <ul className="mt-2 space-y-2 text-sm text-muted-foreground">
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              HD video calls via Daily.co WebRTC
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              Screen sharing for report review
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              Real-time AI transcription
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              Post-call AI-generated SOAP notes
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              In-call AI assistant sidebar
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
