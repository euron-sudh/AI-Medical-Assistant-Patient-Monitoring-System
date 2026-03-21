"use client";

import { useState, useEffect } from "react";

export default function AIConfigPage() {
  const [hasApiKey, setHasApiKey] = useState(false);
  const [apiKeyPreview, setApiKeyPreview] = useState<string>("");

  useEffect(() => {
    const key = localStorage.getItem("euriApiKey") ?? "";
    const valid = key.startsWith("euri-") && key.length > 20;
    setHasApiKey(valid);
    if (valid) {
      setApiKeyPreview(`${key.substring(0, 10)}...${key.substring(key.length - 4)}`);
    }
  }, []);

  const modelConfig = [
    { label: "Primary LLM", value: "GPT-4o", description: "Medical reasoning, symptom analysis, clinical decisions" },
    { label: "Fast Inference", value: "GPT-4o-mini", description: "Triage, drug interactions, monitoring" },
    { label: "Embedding Model", value: "text-embedding-3-large", description: "Medical knowledge vectorization (3072 dims)" },
    { label: "Speech-to-Text", value: "Whisper API", description: "Voice transcription (50+ languages)" },
    { label: "Text-to-Speech", value: "TTS-1", description: "Audio response generation" },
    { label: "Vision", value: "GPT-4o Vision", description: "Report scanning, medical image analysis" },
  ];

  const agentConfig = [
    { label: "Temperature", value: "0.3", description: "Lower = more deterministic medical responses" },
    { label: "Max Tokens", value: "4,096", description: "Maximum response length per API call" },
    { label: "Confidence Threshold", value: "0.75", description: "Minimum confidence for diagnosis output" },
    { label: "RAG Similarity Cutoff", value: "0.75", description: "Minimum cosine similarity for knowledge retrieval" },
    { label: "Agent Timeout", value: "300 seconds", description: "Maximum execution time per agent run" },
    { label: "Max Retries", value: "3", description: "Retry count on API failures with exponential backoff" },
  ];

  const agents = [
    { name: "Symptom Analyst", model: "GPT-4o", status: "active" },
    { name: "Report Reader", model: "GPT-4o Vision", status: "active" },
    { name: "Triage Agent", model: "GPT-4o-mini", status: "active" },
    { name: "Voice Agent", model: "Whisper + TTS", status: "active" },
    { name: "Drug Interaction", model: "GPT-4o-mini", status: "active" },
    { name: "Monitoring Agent", model: "GPT-4o-mini", status: "active" },
    { name: "Follow-Up Agent", model: "GPT-4o", status: "active" },
    { name: "Agent Orchestrator", model: "GPT-4o (function calling)", status: "active" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">AI Configuration</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Configure AI agent models, thresholds, and system prompts.
        </p>
      </div>

      {/* API Status */}
      <div className={`rounded-lg border p-4 shadow-sm ${
        hasApiKey ? "border-green-200 bg-green-50/50" : "border-amber-200 bg-amber-50/50"
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className={`h-3 w-3 rounded-full ${hasApiKey ? "bg-green-500" : "bg-amber-500 animate-pulse"}`} />
            <div>
              <p className="font-medium text-foreground">
                {hasApiKey ? "EURI API Connected" : "EURI API Key Not Configured"}
              </p>
              <p className="text-xs text-muted-foreground">
                {hasApiKey
                  ? `Key: ${apiKeyPreview}`
                  : "Set your API key in the chat interface to enable AI features"}
              </p>
            </div>
          </div>
          <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
            hasApiKey ? "bg-green-100 text-green-800" : "bg-amber-100 text-amber-800"
          }`}>
            {hasApiKey ? "Connected" : "Not Configured"}
          </span>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Model Settings */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Model Settings</h2>
          <div className="mt-4 space-y-4">
            {modelConfig.map((item) => (
              <div key={item.label} className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-medium text-foreground">{item.label}</p>
                  <p className="text-xs text-muted-foreground">{item.description}</p>
                </div>
                <span className="shrink-0 rounded-md bg-muted px-2.5 py-1 text-xs font-mono font-medium text-foreground">
                  {item.value}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Agent Thresholds */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Agent Thresholds</h2>
          <div className="mt-4 space-y-4">
            {agentConfig.map((item) => (
              <div key={item.label} className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-medium text-foreground">{item.label}</p>
                  <p className="text-xs text-muted-foreground">{item.description}</p>
                </div>
                <span className="shrink-0 rounded-md bg-muted px-2.5 py-1 text-xs font-mono font-medium text-foreground">
                  {item.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Agent Registry */}
      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="border-b border-border px-6 py-4">
          <h2 className="text-lg font-semibold text-foreground">Agent Registry</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            8 specialized AI agents coordinated by the Agent Orchestrator
          </p>
        </div>
        <div className="divide-y divide-border">
          {agents.map((agent) => (
            <div
              key={agent.name}
              className="flex items-center justify-between px-6 py-3"
            >
              <div className="flex items-center gap-3">
                <span className="h-2 w-2 rounded-full bg-green-500" />
                <span className="text-sm font-medium text-foreground">{agent.name}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="rounded-md bg-muted px-2 py-0.5 text-xs font-mono text-muted-foreground">
                  {agent.model}
                </span>
                <span className="inline-flex rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
                  {agent.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Safety & Compliance */}
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">Safety & Compliance</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="flex items-center gap-3">
            <span className="h-2 w-2 rounded-full bg-green-500" />
            <span className="text-sm text-foreground">PII redaction before AI calls</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="h-2 w-2 rounded-full bg-green-500" />
            <span className="text-sm text-foreground">Content moderation enabled</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="h-2 w-2 rounded-full bg-green-500" />
            <span className="text-sm text-foreground">Prompt injection defense active</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="h-2 w-2 rounded-full bg-green-500" />
            <span className="text-sm text-foreground">Source attribution required</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="h-2 w-2 rounded-full bg-green-500" />
            <span className="text-sm text-foreground">HIPAA audit logging on all AI calls</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="h-2 w-2 rounded-full bg-green-500" />
            <span className="text-sm text-foreground">Emergency auto-escalation enabled</span>
          </div>
        </div>
      </div>
    </div>
  );
}
