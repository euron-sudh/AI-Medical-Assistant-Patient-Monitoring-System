export default function AIAnalyticsPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">AI Analytics</h1>
        <p className="mt-1 text-muted-foreground">
          Monitor AI agent usage, token consumption, and cost tracking.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Total Tokens (Month)</p>
          <p className="mt-2 text-3xl font-bold text-foreground">0</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Estimated Cost</p>
          <p className="mt-2 text-3xl font-bold text-foreground">$0.00</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Agent Runs</p>
          <p className="mt-2 text-3xl font-bold text-foreground">0</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Avg Latency</p>
          <p className="mt-2 text-3xl font-bold text-muted-foreground">N/A</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Token Usage by Model</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Breakdown of token consumption across GPT-4o, GPT-4o-mini, Whisper, and TTS models.
          </p>
          <div className="mt-4">
            <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Coming Soon
            </span>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Usage by Agent</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Which AI agents consume the most resources: Symptom Analyst, Report Reader,
            Triage, Drug Interaction, Monitoring, and Follow-Up agents.
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
