"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AppNav } from "@/components/AppNav";
import { DeleteSwingButton } from "@/components/DeleteSwingButton";
import { SimplifiedSwingReport } from "@/components/SimplifiedSwingReport";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { getSimplifiedReport, parseCoachingContent } from "@/lib/coaching";
import { SWING_MODE_LABELS } from "@/lib/pricing";
import { logTrace } from "@/lib/trace";
import { DISCLAIMER } from "@/lib/utils";
import type { SwingReport } from "@/lib/types";

export default function SwingReportPage() {
  const params = useParams();
  const reportId = params.id as string;
  const [report, setReport] = useState<SwingReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    const res = await fetch(`/api/swings/${reportId}/status`);
    const data = await res.json();
    if (!res.ok) {
      setError(data.error);
      return;
    }
    setReport(data.report);
    if (data.report) {
      logTrace("frontend_report_loaded", {
        trace_id: null,
        report_id: reportId,
        status: data.report.status,
        ai_narrative_available: data.report.ai_narrative_available,
      });
    }
  }, [reportId]);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(() => {
      if (report?.status === "processing") fetchStatus();
    }, 3000);
    return () => clearInterval(interval);
  }, [fetchStatus, report?.status]);

  if (error) {
    return (
      <div className="min-h-screen">
        <AppNav />
        <main className="mx-auto max-w-3xl px-4 py-8">
          <Card className="text-center">
            <p className="text-red-500">{error}</p>
            <Button className="mt-4" onClick={fetchStatus}>
              Retry
            </Button>
          </Card>
        </main>
      </div>
    );
  }

  if (!report || report.status === "processing") {
    return (
      <div className="min-h-screen">
        <AppNav />
        <main className="mx-auto max-w-3xl px-4 py-16 text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-[var(--color-border)] border-t-[var(--color-accent)]" />
          <h1 className="mt-6 text-2xl font-semibold">Unlocking your analysis</h1>
          <p className="mt-2 text-[var(--color-muted)]">Usually 1–3 minutes.</p>
        </main>
      </div>
    );
  }

  if (report.status === "failed") {
    return (
      <div className="min-h-screen">
        <AppNav />
        <main className="mx-auto max-w-3xl px-4 py-8">
          <Card>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h1 className="text-xl font-semibold text-red-500">Analysis failed</h1>
                <p className="mt-2 text-[var(--color-muted)]">{report.error_message}</p>
              </div>
              <DeleteSwingButton
                reportId={reportId}
                label="Delete swing"
                variant="secondary"
                redirectTo="/dashboard"
              />
            </div>
            <a href="/upload" className="mt-4 inline-block">
              <Button>Try again</Button>
            </a>
          </Card>
        </main>
      </div>
    );
  }

  const coaching = parseCoachingContent(report);
  const simplified = coaching ? getSimplifiedReport(coaching) : null;

  return (
    <div className="min-h-screen">
      <AppNav />
      <main className="mx-auto max-w-3xl px-4 py-8">
        {!report.ai_narrative_available && (
          <div className="mb-6 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-600">
            {report.error_message
              ? `Report unavailable: ${report.error_message}`
              : "Report unavailable — please try uploading again."}
          </div>
        )}

        <header className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
          {coaching?.personalized_greeting && (
            <div className="relative overflow-hidden rounded-2xl border border-[var(--color-accent)]/30 bg-gradient-to-br from-[var(--color-accent)]/20 via-emerald-400/10 to-sky-400/5 px-5 py-4 shadow-sm">
              <p className="text-base font-medium leading-snug text-[var(--color-foreground)]">
                {coaching.personalized_greeting}
              </p>
            </div>
          )}
          {report.swing_mode && (
            <p className="mt-3 text-xs font-semibold uppercase tracking-wider text-[var(--color-accent)]">
              {SWING_MODE_LABELS[report.swing_mode]}
            </p>
          )}
          <h1 className="mt-2 text-2xl font-bold leading-tight tracking-tight sm:text-3xl">
            Your coach read
          </h1>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            {new Date(report.created_at).toLocaleString()}
          </p>
          </div>
          <DeleteSwingButton
            reportId={reportId}
            label="Delete swing"
            variant="secondary"
            redirectTo="/dashboard"
          />
        </header>

        {simplified ? (
          <SimplifiedSwingReport report={simplified} />
        ) : (
          <Card className="mt-8">
            <p className="text-[var(--color-muted)]">
              This is an older report. Upload a new swing for the simplified coach plan.
            </p>
          </Card>
        )}

        <footer className="mt-10 border-t border-[var(--color-border)] pt-6 text-sm text-[var(--color-muted)]">
          {report.disclaimer ?? coaching?.disclaimer ?? DISCLAIMER}
        </footer>
      </main>
    </div>
  );
}
