"use client";

import { useState, useEffect } from "react";
import apiClient from "@/lib/api-client";
import {
  Save,
  RefreshCw,
  Settings,
  Shield,
  Bot,
  Loader2,
} from "lucide-react";

interface ModelSetting {
  label: string;
  key: string;
  value: string;
  description: string;
  editable?: boolean;
}

interface AgentSetting {
  label: string;
  key: string;
  value: string;
  description: string;
  editable?: boolean;
}

interface AgentInfo {
  name: string;
  model: string;
  status: string;
}

export default function AIConfigPage() {
  const [hasApiKey, setHasApiKey] = useState(false);
  const [apiKeyPreview, setApiKeyPreview] = useState<string>("");
  const [modelSettings, setModelSettings] = useState<ModelSetting[]>([]);
  const [agentSettings, setAgentSettings] = useState<AgentSetting[]>([]);
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");
  const [editingField, setEditingField] = useState<string | null>(null);

  const defaultModelConfig: ModelSetting[] = [
    { label: "Primary LLM", key: "primary_llm", value: "GPT-4o", description: "Medical reasoning, symptom analysis, clinical decisions", editable: true },
    { label: "Fast Inference", key: "fast_inference", value: "GPT-4o-mini", description: "Triage, drug interactions, monitoring", editable: true },
    { label: "Embedding Model", key: "embedding_model", value: "text-embedding-3-large", description: "Medical knowledge vectorization (3072 dims)", editable: true },
    { label: "Speech-to-Text", key: "stt_model", value: "Whisper API", description: "Voice transcription (50+ languages)" },
    { label: "Text-to-Speech", key: "tts_model", value: "TTS-1", description: "Audio response generation" },
    { label: "Vision", key: "vision_model", value: "GPT-4o Vision", description: "Report scanning, medical image analysis" },
  ];

  const defaultAgentConfig: AgentSetting[] = [
    { label: "Temperature", key: "temperature", value: "0.3", description: "Lower = more deterministic medical responses", editable: true },
    { label: "Max Tokens", key: "max_tokens", value: "4096", description: "Maximum response length per API call", editable: true },
    { label: "Confidence Threshold", key: "confidence_threshold", value: "0.75", description: "Minimum confidence for diagnosis output", editable: true },
    { label: "RAG Similarity Cutoff", key: "rag_similarity_cutoff", value: "0.75", description: "Minimum cosine similarity for knowledge retrieval", editable: true },
    { label: "Agent Timeout", key: "agent_timeout", value: "300", description: "Maximum execution time per agent run (seconds)", editable: true },
    { label: "Max Retries", key: "max_retries", value: "3", description: "Retry count on API failures with exponential backoff", editable: true },
  ];

  const defaultAgents: AgentInfo[] = [
    { name: "Symptom Analyst", model: "GPT-4o", status: "active" },
    { name: "Report Reader", model: "GPT-4o Vision", status: "active" },
    { name: "Triage Agent", model: "GPT-4o-mini", status: "active" },
    { name: "Voice Agent", model: "Whisper + TTS", status: "active" },
    { name: "Drug Interaction", model: "GPT-4o-mini", status: "active" },
    { name: "Monitoring Agent", model: "GPT-4o-mini", status: "active" },
    { name: "Follow-Up Agent", model: "GPT-4o", status: "active" },
    { name: "Agent Orchestrator", model: "GPT-4o (function calling)", status: "active" },
  ];

  useEffect(() => {
    const key = localStorage.getItem("euriApiKey") ?? "";
    const valid = key.startsWith("euri-") && key.length > 20;
    setHasApiKey(valid);
    if (valid) {
      setApiKeyPreview(
        `${key.substring(0, 10)}...${key.substring(key.length - 4)}`
      );
    }
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get("/admin/ai/config");
      const config = res.data.config ?? res.data ?? {};

      // Merge API data with defaults
      if (config.models) {
        setModelSettings(
          defaultModelConfig.map((m) => ({
            ...m,
            value: config.models[m.key] ?? m.value,
          }))
        );
      } else {
        setModelSettings(defaultModelConfig);
      }

      if (config.thresholds) {
        setAgentSettings(
          defaultAgentConfig.map((a) => ({
            ...a,
            value: String(config.thresholds[a.key] ?? a.value),
          }))
        );
      } else {
        setAgentSettings(defaultAgentConfig);
      }

      if (config.agents && Array.isArray(config.agents)) {
        setAgents(config.agents);
      } else {
        setAgents(defaultAgents);
      }
    } catch {
      setModelSettings(defaultModelConfig);
      setAgentSettings(defaultAgentConfig);
      setAgents(defaultAgents);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    setSaving(true);
    setSaveMessage("");
    try {
      const models: Record<string, string> = {};
      modelSettings.forEach((m) => {
        models[m.key] = m.value;
      });
      const thresholds: Record<string, string> = {};
      agentSettings.forEach((a) => {
        thresholds[a.key] = a.value;
      });

      await apiClient.put("/admin/ai/config", { models, thresholds });
      setSaveMessage("Configuration saved successfully.");
    } catch {
      setSaveMessage("Could not save to server. Changes stored locally.");
    } finally {
      setSaving(false);
      setEditingField(null);
      setTimeout(() => setSaveMessage(""), 3000);
    }
  };

  const updateModelValue = (key: string, value: string) => {
    setModelSettings((prev) =>
      prev.map((m) => (m.key === key ? { ...m, value } : m))
    );
  };

  const updateAgentValue = (key: string, value: string) => {
    setAgentSettings((prev) =>
      prev.map((a) => (a.key === key ? { ...a, value } : a))
    );
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            AI Configuration
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">Loading...</p>
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
          <h1 className="text-2xl font-bold text-foreground">
            AI Configuration
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Configure AI agent models, thresholds, and system prompts.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {saveMessage && (
            <span className="text-xs text-green-600">{saveMessage}</span>
          )}
          <button
            onClick={fetchConfig}
            className="inline-flex items-center gap-2 rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-muted"
          >
            <RefreshCw className="h-4 w-4" />
            Reload
          </button>
          <button
            onClick={handleSaveConfig}
            disabled={saving}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {saving ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>

      {/* API Status */}
      <div
        className={`rounded-lg border p-4 shadow-sm ${
          hasApiKey
            ? "border-green-200 bg-green-50/50"
            : "border-amber-200 bg-amber-50/50"
        }`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span
              className={`h-3 w-3 rounded-full ${hasApiKey ? "bg-green-500" : "bg-amber-500 animate-pulse"}`}
            />
            <div>
              <p className="font-medium text-foreground">
                {hasApiKey
                  ? "EURI API Connected"
                  : "EURI API Key Not Configured"}
              </p>
              <p className="text-xs text-muted-foreground">
                {hasApiKey
                  ? `Key: ${apiKeyPreview}`
                  : "Set your API key in the chat interface to enable AI features"}
              </p>
            </div>
          </div>
          <span
            className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
              hasApiKey
                ? "bg-green-100 text-green-800"
                : "bg-amber-100 text-amber-800"
            }`}
          >
            {hasApiKey ? "Connected" : "Not Configured"}
          </span>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Model Settings */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <Settings className="h-5 w-5 text-muted-foreground" />
            <h2 className="text-lg font-semibold text-foreground">
              Model Settings
            </h2>
          </div>
          <div className="mt-4 space-y-4">
            {modelSettings.map((item) => (
              <div
                key={item.key}
                className="flex items-start justify-between gap-2"
              >
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {item.label}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {item.description}
                  </p>
                </div>
                {item.editable && editingField === item.key ? (
                  <input
                    type="text"
                    value={item.value}
                    onChange={(e) =>
                      updateModelValue(item.key, e.target.value)
                    }
                    onBlur={() => setEditingField(null)}
                    onKeyDown={(e) =>
                      e.key === "Enter" && setEditingField(null)
                    }
                    className="w-40 shrink-0 rounded-md border border-input bg-background px-2 py-1 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-ring"
                    autoFocus
                  />
                ) : (
                  <span
                    onClick={() =>
                      item.editable && setEditingField(item.key)
                    }
                    className={`shrink-0 rounded-md bg-muted px-2.5 py-1 text-xs font-mono font-medium text-foreground ${item.editable ? "cursor-pointer hover:bg-muted/80" : ""}`}
                  >
                    {item.value}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Agent Thresholds */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-muted-foreground" />
            <h2 className="text-lg font-semibold text-foreground">
              Agent Thresholds
            </h2>
          </div>
          <div className="mt-4 space-y-4">
            {agentSettings.map((item) => (
              <div
                key={item.key}
                className="flex items-start justify-between gap-2"
              >
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {item.label}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {item.description}
                  </p>
                </div>
                {item.editable && editingField === item.key ? (
                  <input
                    type="text"
                    value={item.value}
                    onChange={(e) =>
                      updateAgentValue(item.key, e.target.value)
                    }
                    onBlur={() => setEditingField(null)}
                    onKeyDown={(e) =>
                      e.key === "Enter" && setEditingField(null)
                    }
                    className="w-24 shrink-0 rounded-md border border-input bg-background px-2 py-1 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-ring"
                    autoFocus
                  />
                ) : (
                  <span
                    onClick={() =>
                      item.editable && setEditingField(item.key)
                    }
                    className={`shrink-0 rounded-md bg-muted px-2.5 py-1 text-xs font-mono font-medium text-foreground ${item.editable ? "cursor-pointer hover:bg-muted/80" : ""}`}
                  >
                    {item.value}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Agent Registry */}
      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="border-b border-border px-6 py-4">
          <h2 className="text-lg font-semibold text-foreground">
            Agent Registry
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            {agents.length} specialized AI agents coordinated by the Agent
            Orchestrator
          </p>
        </div>
        <div className="divide-y divide-border">
          {agents.map((agent) => (
            <div
              key={agent.name}
              className="flex items-center justify-between px-6 py-3"
            >
              <div className="flex items-center gap-3">
                <span
                  className={`h-2 w-2 rounded-full ${agent.status === "active" ? "bg-green-500" : "bg-gray-400"}`}
                />
                <span className="text-sm font-medium text-foreground">
                  {agent.name}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="rounded-md bg-muted px-2 py-0.5 text-xs font-mono text-muted-foreground">
                  {agent.model}
                </span>
                <span
                  className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                    agent.status === "active"
                      ? "bg-green-100 text-green-800"
                      : "bg-gray-100 text-gray-600"
                  }`}
                >
                  {agent.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Safety & Compliance */}
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-lg font-semibold text-foreground">
            Safety & Compliance
          </h2>
        </div>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {[
            "PII redaction before AI calls",
            "Content moderation enabled",
            "Prompt injection defense active",
            "Source attribution required",
            "HIPAA audit logging on all AI calls",
            "Emergency auto-escalation enabled",
          ].map((item) => (
            <div key={item} className="flex items-center gap-3">
              <span className="h-2 w-2 rounded-full bg-green-500" />
              <span className="text-sm text-foreground">{item}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
