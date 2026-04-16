"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import apiClient from "@/lib/api-client";

interface MedicalReport {
  id: string;
  report_type: string;
  title: string;
  content: string | null;
  file_url: string | null;
  file_type: string | null;
  ai_summary: string | null;
  ai_analysis: Record<string, unknown> | null;
  status: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
  created_by: string;
}

const reportTypeBadge: Record<string, string> = {
  lab: "bg-blue-100 text-blue-700",
  imaging: "bg-purple-100 text-purple-700",
  pathology: "bg-red-100 text-red-700",
  radiology: "bg-indigo-100 text-indigo-700",
  discharge: "bg-gray-100 text-gray-700",
  consultation: "bg-teal-100 text-teal-700",
  progress: "bg-green-100 text-green-700",
  other: "bg-gray-100 text-gray-700",
};

const statusBadge: Record<string, string> = {
  pending: "bg-amber-100 text-amber-700",
  processing: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  reviewed: "bg-green-100 text-green-700",
};

export default function ReportsPage() {
  const [reports, setReports] = useState<MedicalReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const userStr = localStorage.getItem("user");
      if (!userStr) {
        setError("User not found. Please log in again.");
        setLoading(false);
        return;
      }
      const user = JSON.parse(userStr);
      const patientId = user.id ?? user.patient_id;

      const res = await apiClient.get(`/reports/${patientId}`);
      const data = res.data?.reports ?? res.data;
      setReports(Array.isArray(data) ? data : []);
    } catch (err: unknown) {
      const status =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { status?: number } }).response?.status
          : undefined;
      if (status === 404) {
        setReports([]);
      } else {
        setError("Failed to load medical reports.");
      }
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Medical Reports</h1>
          <p className="mt-1 text-muted-foreground">
            View your medical reports and AI-generated analysis summaries.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href="/patient/reports/upload"
            className="inline-flex items-center rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Upload lab report
          </Link>
          <span className="text-sm text-muted-foreground">
            {reports.length} report{reports.length !== 1 ? "s" : ""}
          </span>
        </div>
      </div>

      {loading ? (
        <div className="rounded-lg border border-border bg-card p-12 text-center">
          <p className="text-sm text-muted-foreground">Loading reports...</p>
        </div>
      ) : error ? (
        <div className="rounded-lg border border-border bg-card p-12 text-center">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      ) : reports.length === 0 ? (
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex flex-col items-center justify-center py-12">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
              <span className="text-2xl font-bold text-muted-foreground">R</span>
            </div>
            <h3 className="mt-4 text-lg font-semibold text-foreground">No Reports Yet</h3>
            <p className="mt-2 max-w-sm text-center text-sm text-muted-foreground">
              Your medical reports and lab results will appear here once uploaded. AI-powered
              analysis will provide plain-language summaries of your results.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {reports.map((report) => (
            <div
              key={report.id}
              className="rounded-lg border border-border bg-card shadow-sm"
            >
              <button
                onClick={() => toggleExpand(report.id)}
                className="flex w-full items-center justify-between px-6 py-4 text-left hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                    <span className="text-sm font-bold text-muted-foreground">
                      {report.report_type.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-foreground">{report.title}</h3>
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                          reportTypeBadge[report.report_type] ?? reportTypeBadge.other
                        }`}
                      >
                        {report.report_type}
                      </span>
                    </div>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {new Date(report.created_at).toLocaleDateString("en-US", {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                      })}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span
                    className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      statusBadge[report.status] ?? "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {report.status}
                  </span>
                  <span className="text-muted-foreground">
                    {expandedId === report.id ? "\u25B2" : "\u25BC"}
                  </span>
                </div>
              </button>

              {expandedId === report.id && (
                <div className="border-t border-border px-6 py-4">
                  {report.ai_summary ? (
                    <div className="space-y-3">
                      <div>
                        <h4 className="text-sm font-medium text-foreground">AI Summary</h4>
                        <p className="mt-1 text-sm text-muted-foreground whitespace-pre-wrap">
                          {report.ai_summary}
                        </p>
                      </div>
                      {report.ai_analysis && (
                        <div>
                          <h4 className="text-sm font-medium text-foreground">
                            Detailed Analysis
                          </h4>
                          <div className="mt-1 rounded-md bg-muted/50 p-3">
                            <pre className="text-xs text-muted-foreground overflow-x-auto whitespace-pre-wrap">
                              {JSON.stringify(report.ai_analysis, null, 2)}
                            </pre>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground italic">
                      {report.status === "pending" || report.status === "processing"
                        ? "AI analysis is in progress..."
                        : "No AI analysis available for this report."}
                    </p>
                  )}

                  {report.content && (
                    <div className="mt-3">
                      <h4 className="text-sm font-medium text-foreground">Report Content</h4>
                      <p className="mt-1 text-sm text-muted-foreground whitespace-pre-wrap">
                        {report.content}
                      </p>
                    </div>
                  )}

                  {report.reviewed_by && (
                    <p className="mt-3 text-xs text-muted-foreground">
                      Reviewed on{" "}
                      {report.reviewed_at
                        ? new Date(report.reviewed_at).toLocaleDateString()
                        : "N/A"}
                    </p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
