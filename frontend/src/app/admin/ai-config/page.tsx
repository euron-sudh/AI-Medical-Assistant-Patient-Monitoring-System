export default function AIConfigPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">AI Configuration</h1>
        <p className="mt-1 text-muted-foreground">
          Configure AI agent models, thresholds, and system prompts.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Model Settings</h2>
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Primary Model</span>
              <span className="text-sm font-medium text-foreground">GPT-4o</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Fast Inference Model</span>
              <span className="text-sm font-medium text-foreground">GPT-4o-mini</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Embedding Model</span>
              <span className="text-sm font-medium text-foreground">text-embedding-3-large</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Temperature</span>
              <span className="text-sm font-medium text-foreground">0.3</span>
            </div>
          </div>
          <div className="mt-4">
            <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Editing Coming Soon
            </span>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Agent Thresholds</h2>
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Confidence Threshold</span>
              <span className="text-sm font-medium text-foreground">0.75</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">RAG Similarity Cutoff</span>
              <span className="text-sm font-medium text-foreground">0.75</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Max Tokens per Request</span>
              <span className="text-sm font-medium text-foreground">4096</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Agent Timeout</span>
              <span className="text-sm font-medium text-foreground">300s</span>
            </div>
          </div>
          <div className="mt-4">
            <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Editing Coming Soon
            </span>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">Prompt Template Management</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          View and edit system prompts for each AI agent. Changes require confirmation
          and are audit-logged.
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
