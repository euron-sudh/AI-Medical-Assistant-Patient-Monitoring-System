"use client";

import { useCallback, useState } from "react";
import Link from "next/link";
import apiClient from "@/lib/api-client";
import {
  AlertTriangle,
  Camera,
  CheckCircle2,
  FileDown,
  FileUp,
  Loader2,
  Stethoscope,
  XCircle,
} from "lucide-react";

type Phase = "idle" | "processing" | "success" | "error";

type PatientAnalysis = {
  report_summary?: string;
  key_abnormal_findings?: string[];
  what_this_may_indicate?: string;
  precautions?: string[];
  general_advice?: string;
  recommended_next_steps?: string;
  urgency?: string;
  doctor_consultation?: string;
  emergency_guidance?: string | null;
  extraction_confidence_note?: string | null;
  medical_disclaimer?: string;
};

type StructuredItem = {
  test_name: string;
  value?: number | null;
  unit?: string | null;
  abnormal_flag?: string;
  category?: string | null;
  confidence?: number;
};

type ImageAnalysis = {
  summary?: string;
  findings?: string[];
  what_this_may_indicate?: string;
  precautions?: string[];
  next_steps?: string[];
  urgency?: string;
  consultation_recommendation?: string;
  confidence_note?: string;
  safety_disclaimer?: string;
};

const URGENCY_STYLES: Record<string, string> = {
  normal: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200",
  mild: "bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-200",
  moderate: "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200",
  urgent: "bg-orange-200 text-orange-950 dark:bg-orange-950 dark:text-orange-200",
  emergency: "bg-red-600 text-white dark:bg-red-700",
};

export default function LabReportUploadPage() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [reportId, setReportId] = useState<string | null>(null);
  const [extraction, setExtraction] = useState<Record<string, unknown> | null>(null);
  const [structured, setStructured] = useState<StructuredItem[]>([]);
  const [analysis, setAnalysis] = useState<PatientAnalysis | null>(null);
  const [aiSummary, setAiSummary] = useState<string | null>(null);
  const [analysisPdfLoading, setAnalysisPdfLoading] = useState(false);

  const [scanFile, setScanFile] = useState<File | null>(null);
  const [scanPreviewUrl, setScanPreviewUrl] = useState<string | null>(null);
  const [scanPhase, setScanPhase] = useState<Phase>("idle");
  const [scanProgress, setScanProgress] = useState(0);
  const [scanError, setScanError] = useState<string | null>(null);
  const [scanReportId, setScanReportId] = useState<string | null>(null);
  const [scanAnalysis, setScanAnalysis] = useState<ImageAnalysis | null>(null);
  const [scanPdfLoading, setScanPdfLoading] = useState(false);

  const reset = useCallback(() => {
    setPhase("idle");
    setProgress(0);
    setError(null);
    setFile(null);
    setReportId(null);
    setExtraction(null);
    setStructured([]);
    setAnalysis(null);
    setAiSummary(null);
    setAnalysisPdfLoading(false);

    setScanPhase("idle");
    setScanProgress(0);
    setScanError(null);
    setScanFile(null);
    if (scanPreviewUrl) URL.revokeObjectURL(scanPreviewUrl);
    setScanPreviewUrl(null);
    setScanReportId(null);
    setScanAnalysis(null);
    setScanPdfLoading(false);
  }, [scanPreviewUrl]);

  const downloadAnalysisPdf = useCallback(async () => {
    if (!reportId) return;
    setAnalysisPdfLoading(true);
    setError(null);
    try {
      const res = await apiClient.get<Blob>(`/reports/${reportId}/analysis-pdf`, {
        responseType: "blob",
      });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `medassist-lab-report-analysis-${new Date().toISOString().slice(0, 10)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: { message?: string } } } };
      const msg =
        ax.response?.data?.error?.message ??
        (err as Error)?.message ??
        "Failed to download analysis PDF.";
      setError(msg);
    } finally {
      setAnalysisPdfLoading(false);
    }
  }, [reportId]);

  const downloadScanPdf = useCallback(async () => {
    if (!scanReportId) return;
    setScanPdfLoading(true);
    setScanError(null);
    try {
      const res = await apiClient.get<Blob>(`/reports/${scanReportId}/image-analysis-pdf`, {
        responseType: "blob",
      });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `medassist-image-analysis-${new Date().toISOString().slice(0, 10)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: { message?: string } } } };
      const msg =
        ax.response?.data?.error?.message ??
        (err as Error)?.message ??
        "Failed to download image analysis PDF.";
      setScanError(msg);
    } finally {
      setScanPdfLoading(false);
    }
  }, [scanReportId]);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    setError(null);
    setFile(f ?? null);
  };

  const onScanFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setScanError(null);
    setScanFile(f);
    setScanPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return f ? URL.createObjectURL(f) : null;
    });
  };

  const runAnalyze = async () => {
    if (!file) {
      setError("Choose a PDF or image file first.");
      return;
    }

    const userStr = localStorage.getItem("user");
    if (!userStr) {
      setError("Please log in again.");
      return;
    }
    const user = JSON.parse(userStr);
    const patientId = user.id ?? user.patient_id;
    if (!patientId) {
      setError("Patient profile not found.");
      return;
    }

    const ext = file.name.split(".").pop()?.toLowerCase();
    if (!ext || !["pdf", "png", "jpg", "jpeg"].includes(ext)) {
      setError("Use a PDF, PNG, or JPEG file (max 15 MB).");
      return;
    }
    if (file.size > 15 * 1024 * 1024) {
      setError("File is too large (max 15 MB).");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("patient_id", patientId);
    formData.append("title", file.name.replace(/\.[^.]+$/, "") || "Lab report");

    setPhase("processing");
    setProgress(0);
    setError(null);

    try {
      const res = await apiClient.post("/reports/lab/analyze", formData, {
        timeout: 180000,
        onUploadProgress: (evt) => {
          if (evt.total) {
            setProgress(Math.min(99, Math.round((evt.loaded * 100) / evt.total)));
          }
        },
      });

      setProgress(100);

      setReportId(res.data.report_id ?? null);
      setExtraction(res.data.extraction ?? null);
      setStructured(res.data.structured_lab_values ?? []);
      setAnalysis(res.data.patient_analysis ?? null);
      setAiSummary(res.data.ai_summary ?? null);
      setPhase("success");
    } catch (err: unknown) {
      setPhase("error");
      setProgress(0);
      const ax = err as { response?: { data?: { error?: { message?: string } } } };
      const msg =
        ax.response?.data?.error?.message ??
        "Analysis failed. Try another file or try again later.";
      setError(msg);
    }
  };

  const runScanAnalyze = async () => {
    if (!scanFile) {
      setScanError("Choose a scan image first.");
      return;
    }

    const userStr = localStorage.getItem("user");
    if (!userStr) {
      setScanError("Please log in again.");
      return;
    }
    const user = JSON.parse(userStr);
    const patientId = user.id ?? user.patient_id;
    if (!patientId) {
      setScanError("Patient profile not found.");
      return;
    }

    const ext = scanFile.name.split(".").pop()?.toLowerCase();
    if (!ext || !["png", "jpg", "jpeg", "webp"].includes(ext)) {
      setScanError("Use a PNG, JPG, JPEG, or WEBP image (max 15 MB).");
      return;
    }
    if (scanFile.size > 15 * 1024 * 1024) {
      setScanError("File is too large (max 15 MB).");
      return;
    }

    const formData = new FormData();
    formData.append("file", scanFile);
    formData.append("patient_id", patientId);
    formData.append("title", scanFile.name.replace(/\.[^.]+$/, "") || "Medical image");

    setScanPhase("processing");
    setScanProgress(0);
    setScanError(null);

    try {
      const res = await apiClient.post("/reports/image/analyze", formData, {
        timeout: 180000,
        onUploadProgress: (evt) => {
          if (evt.total) {
            setScanProgress(Math.min(99, Math.round((evt.loaded * 100) / evt.total)));
          }
        },
      });

      setScanProgress(100);
      setScanReportId(res.data.report_id ?? null);
      setScanAnalysis(res.data.image_analysis ?? null);
      setScanPhase("success");
    } catch (err: unknown) {
      setScanPhase("error");
      setScanProgress(0);
      const ax = err as { response?: { data?: { error?: { message?: string } } } };
      const msg =
        ax.response?.data?.error?.message ??
        "Image analysis failed. Try a clearer scan image or try again later.";
      setScanError(msg);
    }
  };

  const urgency = analysis?.urgency ?? "normal";
  const urgencyClass =
    URGENCY_STYLES[urgency] ?? "bg-muted text-muted-foreground";

  const isLabProcessing = phase === "processing";
  const isScanProcessing = scanPhase === "processing";
  const showProcessingBridge = isLabProcessing || isScanProcessing;
  const showLabResults = phase === "success" && analysis;
  const showScanResults = scanPhase === "success" && scanAnalysis;
  const showResultsSection = showLabResults || showScanResults;

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Reports</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Upload a lab report or a scan image. Results appear below after you run an analysis.
          </p>
        </div>
        <Link
          href="/patient/reports"
          className="text-sm font-medium text-primary hover:underline"
        >
          Back to all reports
        </Link>
      </div>

      <div className="rounded-lg border border-amber-200/80 bg-amber-50/80 p-4 text-sm text-amber-950 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
        <div className="flex items-start gap-3">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <p>
            This tool is for education only. It is not a diagnosis. If you feel very unwell or may
            need emergency care, call your local emergency number or seek in-person care immediately.
          </p>
        </div>
      </div>

      {/* Top row: upload cards side by side (stack on small screens) */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Report Analysis (lab) */}
        <div className="flex h-full flex-col rounded-xl border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Lab report</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            PDF or photo of your lab report. We use digital text extraction when possible, then OCR,
            and summarize in plain language.
          </p>
          <p className="mt-1 text-xs text-muted-foreground">PDF, PNG, or JPEG · max 15 MB</p>

          <div className="mt-4 flex flex-1 flex-col space-y-4">
            <label className="block">
              <span className="text-sm font-medium text-foreground">Report Analysis</span>
              <div className="mt-2 flex flex-col gap-3 sm:flex-row sm:items-center">
                <label className="flex min-h-[7rem] flex-1 cursor-pointer items-center justify-center gap-2 rounded-lg border border-dashed border-border bg-muted/30 px-4 py-6 text-center text-sm text-muted-foreground transition-colors hover:bg-muted/50">
                  <FileUp className="h-5 w-5 shrink-0" />
                  <span className="break-all">{file ? file.name : "Choose PDF, PNG, or JPEG"}</span>
                  <input
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
                    className="hidden"
                    onChange={onFileChange}
                    disabled={phase === "processing"}
                  />
                </label>
                {file && (
                  <button
                    type="button"
                    onClick={() => setFile(null)}
                    className="shrink-0 text-sm text-muted-foreground underline hover:text-foreground"
                    disabled={phase === "processing"}
                  >
                    Clear
                  </button>
                )}
              </div>
            </label>

            <button
              type="button"
              onClick={() => void runAnalyze()}
              disabled={!file || phase === "processing"}
              className="mt-auto inline-flex w-full items-center justify-center gap-2 rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {phase === "processing" ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {progress < 100 ? `Uploading… ${progress}%` : "Extracting & analyzing…"}
                </>
              ) : (
                <>
                  <Stethoscope className="h-4 w-4" />
                  Analyze
                </>
              )}
            </button>

            {error && (
              <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <div>
                  <p className="font-medium">Lab report</p>
                  <p className="mt-1">{error}</p>
                  <button
                    type="button"
                    onClick={() => {
                      setError(null);
                      setPhase("idle");
                    }}
                    className="mt-2 text-xs font-medium underline"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* X-Ray / MRI */}
        <div className="flex h-full flex-col rounded-xl border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">X-Ray / MRI Image Analysis</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Scan image for AI-assisted interpretation. Informational only—not a final diagnosis.
          </p>
          <p className="mt-1 text-xs text-muted-foreground">PNG, JPG/JPEG, WEBP · max 15 MB</p>

          <div className="mt-4 flex flex-1 flex-col space-y-4">
            <label className="block">
              <span className="text-sm font-medium text-foreground">Scan image</span>
              <div className="mt-2 flex flex-col gap-3 sm:flex-row sm:items-center">
                <label className="flex min-h-[7rem] flex-1 cursor-pointer items-center justify-center gap-2 rounded-lg border border-dashed border-border bg-muted/30 px-4 py-6 text-center text-sm text-muted-foreground transition-colors hover:bg-muted/50">
                  <Camera className="h-5 w-5 shrink-0" />
                  <span className="break-all">
                    {scanFile ? scanFile.name : "Choose scan image (PNG/JPG/WEBP)"}
                  </span>
                  <input
                    type="file"
                    accept=".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp"
                    className="hidden"
                    onChange={onScanFileChange}
                    disabled={scanPhase === "processing"}
                  />
                </label>
                {scanFile && (
                  <button
                    type="button"
                    onClick={() => {
                      setScanFile(null);
                      setScanPreviewUrl((prev) => {
                        if (prev) URL.revokeObjectURL(prev);
                        return null;
                      });
                      setScanError(null);
                      setScanAnalysis(null);
                      setScanReportId(null);
                      setScanPhase("idle");
                      setScanProgress(0);
                    }}
                    className="shrink-0 text-sm text-muted-foreground underline hover:text-foreground"
                    disabled={scanPhase === "processing"}
                  >
                    Clear
                  </button>
                )}
              </div>
            </label>

            {scanPreviewUrl && (
              <div className="rounded-md border border-border bg-muted/10 p-3">
                <p className="text-xs font-medium text-muted-foreground">Preview</p>
                <img
                  src={scanPreviewUrl}
                  alt="Selected scan preview"
                  className="mt-2 max-h-[200px] w-full rounded-md object-contain lg:max-h-[220px]"
                />
              </div>
            )}

            <button
              type="button"
              onClick={() => void runScanAnalyze()}
              disabled={!scanFile || scanPhase === "processing"}
              className="mt-auto inline-flex w-full items-center justify-center gap-2 rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {scanPhase === "processing" ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {scanProgress < 100 ? `Uploading… ${scanProgress}%` : "Analyzing image…"}
                </>
              ) : (
                <>
                  <Camera className="h-4 w-4" />
                  Analyze
                </>
              )}
            </button>

            {scanError && (
              <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <div>
                  <p className="font-medium">Image analysis</p>
                  <p className="mt-1">{scanError}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Loading bridge: between uploads and results */}
      {showProcessingBridge && (
        <div
          className="rounded-xl border border-primary/20 bg-primary/5 px-6 py-8 text-center dark:bg-primary/10"
          role="status"
          aria-live="polite"
        >
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-primary" />
          <p className="mt-3 text-sm font-medium text-foreground">Analysis in progress</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {isLabProcessing && isScanProcessing
              ? "Lab report and scan analyses are running. This may take a few minutes."
              : isLabProcessing
                ? "Working on your lab report: extracting text and generating your summary."
                : "Working on your scan image with vision analysis."}
          </p>
        </div>
      )}

      {/* Results section: below uploads; only after success */}
      {showResultsSection && (
        <div className="space-y-8 rounded-2xl border-2 border-border bg-muted/20 p-6 shadow-inner dark:bg-muted/10 sm:p-8">
          <div className="border-b border-border pb-4">
            <h2 className="text-xl font-semibold text-foreground">Your analysis results</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Review the output below. Download a PDF when you are ready, or start over with another
              report.
            </p>
          </div>

          {showLabResults && (
            <div className="space-y-6">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Lab report analysis
              </p>
              <div
                className={`rounded-lg border-2 px-4 py-3 ${urgency === "emergency" || urgency === "urgent" ? "border-destructive" : "border-border"}`}
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Urgency
                  </span>
                  <span
                    className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold capitalize ${urgencyClass}`}
                  >
                    {urgency}
                  </span>
                  {analysis?.doctor_consultation && analysis.doctor_consultation !== "none" && (
                    <span className="text-xs text-muted-foreground">
                      Doctor follow-up:{" "}
                      <span className="font-medium text-foreground">
                        {analysis.doctor_consultation}
                      </span>
                    </span>
                  )}
                </div>
                {(urgency === "urgent" || urgency === "emergency") && (
                  <div className="mt-3 flex gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                    <AlertTriangle className="h-5 w-5 shrink-0" />
                    <div>
                      <p className="font-semibold">Important</p>
                      <p className="mt-1">
                        {analysis?.emergency_guidance ??
                          "These results may need prompt attention. Contact a qualified clinician or emergency services if you have severe symptoms or your report suggests a critical value."}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {analysis?.extraction_confidence_note && (
                <div className="rounded-md border border-amber-200 bg-amber-50/90 p-3 text-sm text-amber-950 dark:border-amber-900 dark:bg-amber-950/50 dark:text-amber-100">
                  <strong>Manual review suggested:</strong> {analysis.extraction_confidence_note}
                </div>
              )}

              <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
                <div className="flex items-center gap-2 text-green-700 dark:text-green-400">
                  <CheckCircle2 className="h-5 w-5" />
                  <h3 className="text-lg font-semibold text-foreground">Summary</h3>
                </div>
                {reportId && (
                  <p className="mt-1 text-xs text-muted-foreground">
                    Saved as report #{reportId.slice(0, 8)}…
                  </p>
                )}
                <p className="mt-3 whitespace-pre-wrap text-sm text-muted-foreground">
                  {analysis?.report_summary}
                </p>
                {aiSummary && (
                  <p className="mt-4 whitespace-pre-wrap text-sm text-foreground">{aiSummary}</p>
                )}
              </div>

              {analysis?.key_abnormal_findings && analysis.key_abnormal_findings.length > 0 && (
                <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
                  <h3 className="text-sm font-semibold text-foreground">Key abnormal findings</h3>
                  <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-muted-foreground">
                    {analysis.key_abnormal_findings.map((x, i) => (
                      <li key={i}>{x}</li>
                    ))}
                  </ul>
                </div>
              )}

              {analysis?.what_this_may_indicate && (
                <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
                  <h3 className="text-sm font-semibold text-foreground">What this may indicate</h3>
                  <p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">
                    {analysis.what_this_may_indicate}
                  </p>
                </div>
              )}

              {analysis?.precautions && analysis.precautions.length > 0 && (
                <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
                  <h3 className="text-sm font-semibold text-foreground">Precautions</h3>
                  <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-muted-foreground">
                    {analysis.precautions.map((x, i) => (
                      <li key={i}>{x}</li>
                    ))}
                  </ul>
                </div>
              )}

              {(analysis?.general_advice || analysis?.recommended_next_steps) && (
                <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
                  <h3 className="text-sm font-semibold text-foreground">Next steps</h3>
                  {analysis?.general_advice && (
                    <p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">
                      {analysis.general_advice}
                    </p>
                  )}
                  {analysis?.recommended_next_steps && (
                    <p className="mt-3 whitespace-pre-wrap text-sm font-medium text-foreground">
                      {analysis.recommended_next_steps}
                    </p>
                  )}
                </div>
              )}

              {structured.length > 0 && (
                <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
                  <h3 className="text-sm font-semibold text-foreground">
                    Extracted values (best effort)
                  </h3>
                  <div className="mt-3 overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-border text-muted-foreground">
                          <th className="py-2 pr-2">Test</th>
                          <th className="py-2 pr-2">Value</th>
                          <th className="py-2 pr-2">Flag</th>
                          <th className="py-2">Category</th>
                        </tr>
                      </thead>
                      <tbody>
                        {structured.slice(0, 40).map((row, i) => (
                          <tr key={i} className="border-b border-border/60">
                            <td className="py-2 pr-2 text-foreground">{row.test_name}</td>
                            <td className="py-2 pr-2 text-muted-foreground">
                              {row.value != null ? row.value : "—"} {row.unit ? row.unit : ""}
                            </td>
                            <td className="py-2 pr-2 capitalize">{row.abnormal_flag ?? "—"}</td>
                            <td className="py-2 text-muted-foreground">{row.category ?? "—"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {extraction && process.env.NODE_ENV !== "production" && (
                <details className="rounded-lg border border-dashed border-border bg-muted/20 p-4 text-xs">
                  <summary className="cursor-pointer font-medium text-muted-foreground">
                    Extraction debug (dev)
                  </summary>
                  <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap text-muted-foreground">
                    {JSON.stringify(extraction, null, 2)}
                  </pre>
                </details>
              )}

              {analysis?.medical_disclaimer && (
                <p className="text-center text-xs text-muted-foreground">{analysis.medical_disclaimer}</p>
              )}
            </div>
          )}

          {showScanResults && scanAnalysis && (
            <div className={`space-y-6 ${showLabResults ? "border-t border-border pt-8" : ""}`}>
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                X-Ray / MRI image analysis
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Urgency
                </span>
                <span
                  className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold capitalize ${
                    URGENCY_STYLES[scanAnalysis.urgency ?? "moderate"] ??
                    "bg-muted text-muted-foreground"
                  }`}
                >
                  {scanAnalysis.urgency ?? "moderate"}
                </span>
                {scanReportId && (
                  <span className="text-xs text-muted-foreground">
                    Saved as report #{scanReportId.slice(0, 8)}…
                  </span>
                )}
              </div>

              {scanAnalysis.summary && (
                <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
                  <h3 className="text-sm font-semibold text-foreground">Image analysis summary</h3>
                  <p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">
                    {scanAnalysis.summary}
                  </p>
                </div>
              )}

              {scanAnalysis.findings && scanAnalysis.findings.length > 0 && (
                <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
                  <h3 className="text-sm font-semibold text-foreground">Possible findings or anomalies</h3>
                  <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-muted-foreground">
                    {scanAnalysis.findings.map((x, i) => (
                      <li key={i}>{x}</li>
                    ))}
                  </ul>
                </div>
              )}

              {scanAnalysis.what_this_may_indicate && (
                <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
                  <h3 className="text-sm font-semibold text-foreground">What this may indicate</h3>
                  <p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">
                    {scanAnalysis.what_this_may_indicate}
                  </p>
                </div>
              )}

              {scanAnalysis.precautions && scanAnalysis.precautions.length > 0 && (
                <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
                  <h3 className="text-sm font-semibold text-foreground">Precautions</h3>
                  <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-muted-foreground">
                    {scanAnalysis.precautions.map((x, i) => (
                      <li key={i}>{x}</li>
                    ))}
                  </ul>
                </div>
              )}

              {scanAnalysis.next_steps && scanAnalysis.next_steps.length > 0 && (
                <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
                  <h3 className="text-sm font-semibold text-foreground">Next steps</h3>
                  <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-muted-foreground">
                    {scanAnalysis.next_steps.map((x, i) => (
                      <li key={i}>{x}</li>
                    ))}
                  </ul>
                </div>
              )}

              {(scanAnalysis.consultation_recommendation || scanAnalysis.confidence_note) && (
                <div className="rounded-md border border-amber-200 bg-amber-50/90 p-3 text-sm text-amber-950 dark:border-amber-900 dark:bg-amber-950/50 dark:text-amber-100">
                  {scanAnalysis.consultation_recommendation ? (
                    <p>
                      <strong>Consultation:</strong> {scanAnalysis.consultation_recommendation}
                    </p>
                  ) : null}
                  {scanAnalysis.confidence_note ? (
                    <p className={scanAnalysis.consultation_recommendation ? "mt-2" : ""}>
                      <strong>Limitations:</strong> {scanAnalysis.confidence_note}
                    </p>
                  ) : null}
                </div>
              )}

              {scanAnalysis.safety_disclaimer && (
                <p className="text-center text-xs text-muted-foreground">
                  {scanAnalysis.safety_disclaimer}
                </p>
              )}
            </div>
          )}

          {/* End of result section: PDFs then reset */}
          <div className="border-t border-border pt-6">
            <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-stretch">
              {showLabResults && reportId && (
                <button
                  type="button"
                  onClick={() => void downloadAnalysisPdf()}
                  disabled={analysisPdfLoading}
                  className="inline-flex flex-1 items-center justify-center gap-2 rounded-md bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50 sm:min-w-[200px]"
                >
                  {analysisPdfLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <FileDown className="h-4 w-4" />
                  )}
                  {analysisPdfLoading ? "Preparing PDF…" : "Download Analysis PDF"}
                </button>
              )}
              {showScanResults && scanReportId && (
                <button
                  type="button"
                  onClick={() => void downloadScanPdf()}
                  disabled={scanPdfLoading}
                  className="inline-flex flex-1 items-center justify-center gap-2 rounded-md bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50 sm:min-w-[220px]"
                >
                  {scanPdfLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <FileDown className="h-4 w-4" />
                  )}
                  {scanPdfLoading ? "Preparing PDF…" : "Download Image Analysis PDF"}
                </button>
              )}
            </div>
            <button
              type="button"
              onClick={reset}
              className="mt-3 w-full rounded-md border border-border bg-background px-4 py-2.5 text-sm font-medium text-foreground hover:bg-muted sm:mt-4 sm:w-auto"
            >
              Analyze Other Report
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
