export default function PrescriptionsPage() {
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Prescriptions</h1>
          <p className="mt-1 text-muted-foreground">
            Manage patient prescriptions with AI-powered drug interaction checking.
          </p>
        </div>
        <button
          disabled
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground opacity-50"
        >
          New Prescription
        </button>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Recent Prescriptions</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            View and manage recently issued prescriptions. Each prescription is automatically
            checked for drug-drug interactions and allergy cross-references.
          </p>
          <div className="mt-4">
            <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Coming Soon
            </span>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Drug Interaction Checker</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            AI-powered drug interaction analysis checks all active medications for conflicts,
            contraindications, and dosage verification before prescribing.
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
