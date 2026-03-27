"use client";

import { useState, useEffect } from "react";
import apiClient from "@/lib/api-client";
import { RefreshCw, TrendingUp, DollarSign, MessageSquare, Timer } from "lucide-react";

interface AIStats {
  totalChatMessages: number;
  totalTokensUsed: number;
  estimatedCost: number;
  avgResponseTime: number;
  modelBreakdown: { model: string; tokens: number; calls: number; cost: number }[];
  agentBreakdown: { agent: string; runs: number; avgLatency: number }[];
}

export default function AIAnalyticsPage() {
  const [stats, setStats] = useState<AIStats>({
    totalChatMessages: 0,
    totalTokensUsed: 0,
    estimatedCost: 0,
    avgResponseTime: 0,
    modelBreakdown: [],
    agentBreakdown: [],
  });
  const [loading, setLoading] = useState(true);
  const [usingSample, setUsingSample] = useState(false);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get("/admin/analytics/ai-usage");
      if (res.data) {
        setStats(res.data);
        setUsingSample(false);
        setLoading(false);
        return;
      }
    } catch {
      /* fall through to defaults */
    }

    const computed: AIStats = {
      totalChatMessages: 247,
      totalTokensUsed: 1_842_350,
      estimatedCost: 8.72,
      avgResponseTime: 2.3,
      modelBreakdown: [
        { model: "gpt-4o-mini", tokens: 1_245_000, calls: 189, cost: 1.87 },
        { model: "gpt-4o", tokens: 485_000, calls: 42, cost: 5.95 },
        { model: "text-embedding-3-large", tokens: 112_350, calls: 16, cost: 0.90 },
      ],
      agentBreakdown: [
        { agent: "Symptom Analyst", runs: 68, avgLatency: 3200 },
        { agent: "Report Reader", runs: 42, avgLatency: 4500 },
        { agent: "Triage Agent", runs: 35, avgLatency: 1800 },
        { agent: "Drug Interaction", runs: 28, avgLatency: 2100 },
        { agent: "Monitoring Agent", runs: 156, avgLatency: 1200 },
        { agent: "Follow-Up Agent", runs: 22, avgLatency: 2800 },
        { agent: "Voice Agent", runs: 12, avgLatency: 3500 },
      ],
    };

    try {
      const chatRes = await apiClient.get("/chat/conversations");
      const convos = chatRes.data.conversations ?? chatRes.data ?? [];
      if (Array.isArray(convos) && convos.length > 0) {
        computed.totalChatMessages = convos.length;
      }
    } catch {
      /* use default */
    }

    setStats(computed);
    setUsingSample(true);
    setLoading(false);
  };

  const formatNumber = (n: number): string => {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
    return n.toString();
  };

  const maxTokens = Math.max(
    ...stats.modelBreakdown.map((m) => m.tokens),
    1
  );
  const maxRuns = Math.max(
    ...stats.agentBreakdown.map((a) => a.runs),
    1
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">AI Analytics</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Loading AI usage analytics...
          </p>
        </div>
        <div className="flex items-center justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">AI Analytics</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Monitor AI agent usage, token consumption, and cost tracking.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {usingSample && (
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Sample data
            </span>
          )}
          <button
            onClick={fetchStats}
            className="inline-flex items-center gap-2 rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-muted"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted-foreground">
              Total Tokens (Month)
            </p>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </div>
          <p className="mt-2 text-3xl font-bold text-foreground">
            {formatNumber(stats.totalTokensUsed)}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            input + output tokens
          </p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted-foreground">
              Estimated Cost
            </p>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </div>
          <p className="mt-2 text-3xl font-bold text-foreground">
            ${stats.estimatedCost.toFixed(2)}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">this month</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted-foreground">
              Chat Messages
            </p>
            <MessageSquare className="h-4 w-4 text-primary" />
          </div>
          <p className="mt-2 text-3xl font-bold text-primary">
            {stats.totalChatMessages}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">conversations</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted-foreground">
              Avg Response Time
            </p>
            <Timer className="h-4 w-4 text-muted-foreground" />
          </div>
          <p className="mt-2 text-3xl font-bold text-foreground">
            {stats.avgResponseTime}s
          </p>
          <p className="mt-1 text-xs text-muted-foreground">p50 latency</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Token Usage by Model */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">
            Token Usage by Model
          </h2>
          <div className="mt-4 space-y-4">
            {stats.modelBreakdown.map((m) => (
              <div key={m.model}>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-foreground">
                    {m.model}
                  </span>
                  <span className="text-muted-foreground">
                    {formatNumber(m.tokens)} tokens / ${m.cost.toFixed(2)}
                  </span>
                </div>
                <div className="mt-1.5 h-2.5 w-full rounded-full bg-muted">
                  <div
                    className="h-2.5 rounded-full bg-primary"
                    style={{
                      width: `${(m.tokens / maxTokens) * 100}%`,
                    }}
                  />
                </div>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {m.calls} API calls
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Usage by Agent */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">
            Usage by Agent
          </h2>
          <div className="mt-4 space-y-4">
            {stats.agentBreakdown.map((a) => (
              <div key={a.agent}>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-foreground">
                    {a.agent}
                  </span>
                  <span className="text-muted-foreground">
                    {a.runs} runs / {a.avgLatency}ms avg
                  </span>
                </div>
                <div className="mt-1.5 h-2.5 w-full rounded-full bg-muted">
                  <div
                    className="h-2.5 rounded-full bg-emerald-500"
                    style={{
                      width: `${(a.runs / maxRuns) * 100}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Cost Breakdown Table */}
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">
          Cost Breakdown
        </h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                <th className="pb-2 pr-4">Model</th>
                <th className="pb-2 pr-4">API Calls</th>
                <th className="pb-2 pr-4">Tokens Used</th>
                <th className="pb-2 pr-4">Cost/Call</th>
                <th className="pb-2">Total Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {stats.modelBreakdown.map((m) => (
                <tr key={m.model} className="hover:bg-muted/50">
                  <td className="py-2.5 pr-4 font-medium text-foreground">
                    {m.model}
                  </td>
                  <td className="py-2.5 pr-4 text-muted-foreground">
                    {m.calls}
                  </td>
                  <td className="py-2.5 pr-4 text-muted-foreground">
                    {formatNumber(m.tokens)}
                  </td>
                  <td className="py-2.5 pr-4 text-muted-foreground">
                    ${m.calls > 0 ? (m.cost / m.calls).toFixed(4) : "0.00"}
                  </td>
                  <td className="py-2.5 font-medium text-foreground">
                    ${m.cost.toFixed(2)}
                  </td>
                </tr>
              ))}
              <tr className="bg-muted/30 font-semibold">
                <td className="py-2.5 pr-4 text-foreground">Total</td>
                <td className="py-2.5 pr-4 text-foreground">
                  {stats.modelBreakdown.reduce(
                    (s, m) => s + m.calls,
                    0
                  )}
                </td>
                <td className="py-2.5 pr-4 text-foreground">
                  {formatNumber(
                    stats.modelBreakdown.reduce(
                      (s, m) => s + m.tokens,
                      0
                    )
                  )}
                </td>
                <td className="py-2.5 pr-4" />
                <td className="py-2.5 text-foreground">
                  ${stats.estimatedCost.toFixed(2)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
