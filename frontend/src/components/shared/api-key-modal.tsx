"use client";

import { useState, useEffect } from "react";

interface ApiKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (key: string) => void;
}

export function ApiKeyModal({ isOpen, onClose, onSave }: ApiKeyModalProps) {
  const [key, setKey] = useState("");

  useEffect(() => {
    if (isOpen) {
      const saved = localStorage.getItem("euriApiKey") ?? "";
      setKey(saved);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = () => {
    localStorage.setItem("euriApiKey", key);
    onSave(key);
    onClose();
  };

  const handleClear = () => {
    localStorage.removeItem("euriApiKey");
    setKey("");
  };

  const isConfigured = key.startsWith("euri-") && key.length > 20;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg border bg-card p-6 shadow-xl mx-4">
        <h2 className="text-xl font-semibold text-foreground">EURI API Key</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Enter your EURI API key to enable AI features (symptom analysis, chat, report reading).
          Get a key at{" "}
          <a
            href="https://euron.one/euri"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary underline"
          >
            euron.one/euri
          </a>
        </p>

        <div className="mt-4 space-y-3">
          <input
            type="password"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="euri-xxxxxxxxxxxxxxxxxxxx"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />

          {isConfigured && (
            <div className="flex items-center gap-2 text-sm text-green-600">
              <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
              Key looks valid
            </div>
          )}

          {key && !isConfigured && (
            <div className="flex items-center gap-2 text-sm text-amber-600">
              <span className="inline-block h-2 w-2 rounded-full bg-amber-500" />
              Key should start with &quot;euri-&quot;
            </div>
          )}
        </div>

        <div className="mt-6 flex gap-3 justify-end">
          <button
            onClick={handleClear}
            className="rounded-md border border-input px-4 py-2 text-sm text-muted-foreground hover:bg-muted"
          >
            Clear
          </button>
          <button
            onClick={onClose}
            className="rounded-md border border-input px-4 py-2 text-sm hover:bg-muted"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!key}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            Save Key
          </button>
        </div>
      </div>
    </div>
  );
}

export function ApiKeyButton() {
  const [isOpen, setIsOpen] = useState(false);
  const [hasKey, setHasKey] = useState(false);

  useEffect(() => {
    const key = localStorage.getItem("euriApiKey");
    setHasKey(!!key && key.startsWith("euri-"));
  }, []);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 rounded-md border border-input px-3 py-1.5 text-xs font-medium hover:bg-muted"
      >
        <span className={`inline-block h-2 w-2 rounded-full ${hasKey ? "bg-green-500" : "bg-red-500"}`} />
        {hasKey ? "AI Connected" : "Set API Key"}
      </button>
      <ApiKeyModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        onSave={(key) => setHasKey(!!key && key.startsWith("euri-"))}
      />
    </>
  );
}
