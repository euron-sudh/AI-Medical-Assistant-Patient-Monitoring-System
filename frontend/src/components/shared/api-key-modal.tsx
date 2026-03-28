"use client";

import { useState, useEffect } from "react";

/**
 * The default EURI API key — used by the backend. Users can override
 * this with their own key via the settings modal if desired.
 */
const DEFAULT_EURI_KEY = "euri-1359066cf23e5b59f64abda2da199c73046b7ba3910a018cdbdcb5ae3a13396d";

/** Get the EURI API key — returns user's custom key or the default */
export function getEuriApiKey(): string {
  if (typeof window === "undefined") return DEFAULT_EURI_KEY;
  return localStorage.getItem("euriApiKey") || DEFAULT_EURI_KEY;
}

/** Check if any key is available (always true now since we have a default) */
export function hasEuriApiKey(): boolean {
  return true;
}

interface ApiKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (key: string) => void;
}

export function ApiKeyModal({ isOpen, onClose, onSave }: ApiKeyModalProps) {
  const [key, setKey] = useState("");
  const [isCustom, setIsCustom] = useState(false);

  useEffect(() => {
    if (isOpen) {
      const saved = localStorage.getItem("euriApiKey") ?? "";
      setKey(saved);
      setIsCustom(!!saved);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = () => {
    if (key.trim()) {
      localStorage.setItem("euriApiKey", key.trim());
    } else {
      localStorage.removeItem("euriApiKey");
    }
    onSave(key.trim() || DEFAULT_EURI_KEY);
    onClose();
  };

  const handleReset = () => {
    localStorage.removeItem("euriApiKey");
    setKey("");
    setIsCustom(false);
    onSave(DEFAULT_EURI_KEY);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg border bg-card p-6 shadow-xl mx-4">
        <h2 className="text-xl font-semibold text-foreground">AI API Key Settings</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          A default EURI API key is pre-configured. You can optionally use your own key for higher rate limits.
        </p>

        <div className="mt-4 space-y-3">
          <div className="flex items-center gap-2 text-sm text-green-600">
            <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
            Default key active — AI features are working
          </div>

          <label className="block text-sm font-medium text-foreground mt-4">
            Custom key (optional):
          </label>
          <input
            type="password"
            value={key}
            onChange={(e) => { setKey(e.target.value); setIsCustom(true); }}
            placeholder="Leave empty to use default key"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />

          {isCustom && key && (
            <p className="text-xs text-muted-foreground">Using your custom key instead of the default.</p>
          )}
        </div>

        <div className="mt-6 flex gap-3 justify-end">
          {isCustom && (
            <button
              onClick={handleReset}
              className="rounded-md border border-input px-4 py-2 text-sm text-muted-foreground hover:bg-muted"
            >
              Reset to Default
            </button>
          )}
          <button
            onClick={onClose}
            className="rounded-md border border-input px-4 py-2 text-sm hover:bg-muted"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}

export function ApiKeyButton() {
  const [isOpen, setIsOpen] = useState(false);
  const isCustom = typeof window !== "undefined" && !!localStorage.getItem("euriApiKey");

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 rounded-md border border-input px-3 py-1.5 text-xs font-medium hover:bg-muted"
      >
        <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
        {isCustom ? "Custom Key" : "AI Connected"}
      </button>
      <ApiKeyModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        onSave={() => {}}
      />
    </>
  );
}
