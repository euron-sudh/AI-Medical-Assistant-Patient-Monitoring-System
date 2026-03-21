export default function SymptomsPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Symptom Checker</h1>
        <p className="mt-1 text-muted-foreground">
          Describe your symptoms and get AI-powered analysis and recommendations.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary">
              <span className="text-lg font-bold">S</span>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Start New Check</p>
              <p className="text-xl font-bold text-foreground">AI Symptom Analysis</p>
            </div>
          </div>
          <p className="mt-4 text-sm text-muted-foreground">
            Start a new symptom check session. Our AI assistant will guide you through
            a series of questions to help identify possible conditions.
          </p>
          <div className="mt-4">
            <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Coming Soon
            </span>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-blue-600">
              <span className="text-lg font-bold">H</span>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Session History</p>
              <p className="text-xl font-bold text-foreground">Past Checks</p>
            </div>
          </div>
          <p className="mt-4 text-sm text-muted-foreground">
            Review your previous symptom check sessions and their AI-generated
            differential diagnoses and recommendations.
          </p>
          <p className="mt-4 text-sm text-muted-foreground italic">No past sessions found.</p>
        </div>
      </div>

      <div className="rounded-md border border-border bg-muted/50 px-4 py-3">
        <p className="text-xs text-muted-foreground">
          AI-generated symptom analysis is for informational purposes only and is not a substitute
          for professional medical advice. If you are experiencing a medical emergency, call 911 immediately.
        </p>
      </div>
    </div>
  );
}
