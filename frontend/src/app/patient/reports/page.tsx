export default function ReportsPage() {
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Medical Reports</h1>
          <p className="mt-1 text-muted-foreground">
            View your medical reports and AI-generated analysis summaries.
          </p>
        </div>
        <button
          disabled
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground opacity-50"
        >
          Upload Report
        </button>
      </div>

      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <div className="flex flex-col items-center justify-center py-12">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
            <span className="text-2xl font-bold text-muted-foreground">R</span>
          </div>
          <h3 className="mt-4 text-lg font-semibold text-foreground">No Reports Yet</h3>
          <p className="mt-2 max-w-sm text-center text-sm text-muted-foreground">
            Your medical reports and lab results will appear here once uploaded.
            AI-powered analysis will provide plain-language summaries of your results.
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
