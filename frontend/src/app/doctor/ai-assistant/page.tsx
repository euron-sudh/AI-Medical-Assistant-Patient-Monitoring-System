export default function AIAssistantPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">AI Assistant</h1>
        <p className="mt-1 text-muted-foreground">
          AI-powered clinical decision support for diagnosis, treatment, and patient care.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary">
              <span className="text-lg font-bold">Dx</span>
            </div>
            <div>
              <p className="font-medium text-foreground">Differential Diagnosis</p>
              <p className="text-sm text-muted-foreground">AI-assisted diagnostic reasoning</p>
            </div>
          </div>
          <div className="mt-4">
            <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Coming Soon
            </span>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
              <span className="text-lg font-bold">Rx</span>
            </div>
            <div>
              <p className="font-medium text-foreground">Treatment Recommendations</p>
              <p className="text-sm text-muted-foreground">Evidence-based treatment suggestions</p>
            </div>
          </div>
          <div className="mt-4">
            <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Coming Soon
            </span>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-blue-600">
              <span className="text-lg font-bold">Lit</span>
            </div>
            <div>
              <p className="font-medium text-foreground">Medical Literature Search</p>
              <p className="text-sm text-muted-foreground">RAG-powered knowledge base queries</p>
            </div>
          </div>
          <div className="mt-4">
            <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Coming Soon
            </span>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-orange-100 text-orange-600">
              <span className="text-lg font-bold">N</span>
            </div>
            <div>
              <p className="font-medium text-foreground">Clinical Note Generation</p>
              <p className="text-sm text-muted-foreground">AI-generated SOAP notes</p>
            </div>
          </div>
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
