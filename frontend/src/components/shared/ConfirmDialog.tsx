"use client";
import { useEffect, useRef } from "react";
interface ConfirmDialogProps { open: boolean; title: string; description: string; confirmLabel?: string; cancelLabel?: string; variant?: "danger" | "default"; onConfirm: () => void; onCancel: () => void; }
export default function ConfirmDialog({ open, title, description, confirmLabel = "Confirm", cancelLabel = "Cancel", variant = "default", onConfirm, onCancel }: ConfirmDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  useEffect(() => { if (!open) return; const h = (e: KeyboardEvent) => { if (e.key === "Escape") onCancel(); }; document.addEventListener("keydown", h); return () => document.removeEventListener("keydown", h); }, [open, onCancel]);
  useEffect(() => { if (open && dialogRef.current) dialogRef.current.focus(); }, [open]);
  if (!open) return null;
  const btn = variant === "danger" ? "bg-red-600 text-white hover:bg-red-700" : "bg-primary text-primary-foreground hover:bg-primary/90";
  return (<div className="fixed inset-0 z-50 flex items-center justify-center"><div className="absolute inset-0 bg-black/50" onClick={onCancel} /><div ref={dialogRef} tabIndex={-1} role="alertdialog" aria-modal="true" className="relative z-10 w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-lg"><h2 className="text-lg font-semibold text-foreground">{title}</h2><p className="mt-2 text-sm text-muted-foreground">{description}</p><div className="mt-6 flex justify-end gap-3"><button onClick={onCancel} className="rounded-md border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted transition-colors">{cancelLabel}</button><button onClick={onConfirm} className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${btn}`}>{confirmLabel}</button></div></div></div>);
}
