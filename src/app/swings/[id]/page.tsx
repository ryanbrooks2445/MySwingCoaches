"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { AppNav } from "@/components/AppNav";
import { DeleteSwingButton } from "@/components/DeleteSwingButton";
import { SimplifiedSwingReport } from "@/components/SimplifiedSwingReport";
import { SwingComparison } from "@/components/SwingComparison";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { readApiResponse } from "@/lib/api-response";
import { getFeelBlueprint, getSimplifiedReport, getVisiblePhaseMap, parseCoachingContent } from "@/lib/coaching";
import { SWING_MODE_LABELS } from "@/lib/pricing";
import { logTrace } from "@/lib/trace";
import { DISCLAIMER } from "@/lib/utils";
import type { SwingReport } from "@/lib/types";
import type { ProgressState } from "@/lib/phase-frames";

function DebugBlock({ title, value }: { title: string; value: unknown }) {
  return (
    <details className="rounded-lg border border-[var(--color-border)] bg-[var(--color-background)]">
      <summary className="cursor-pointer px-4 py-3 text-sm font-semibold">{title}</summary>
      <pre className="max-h-96 overflow-auto whitespace-pre-wrap border-t border-[var(--color-border)] px-4 py-3 text-xs text-[var(--color-muted)]">
        {typeof value === "string" ? value : JSON.stringify(value, null, 2)}
      </pre>
    </details>
  );
}

function AnalysisDebugPanel({ report, finalReport }: { report: SwingReport; finalReport: unknown }) {
  const rawResponses = Array.isArray(report.gemini_raw?.raw_responses)
    ? report.gemini_raw.raw_responses
    : [];

  return (
    <section className="mt-8 space-y-4 rounded-lg border border-dashed border-sky-500/50 bg-sky-50/40 p-4">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-sky-700">Developer analysis debug</p>
        <h2 className="mt-1 text-lg font-semibold">Gemini input/output audit</h2>
      </div>

      {report.key_frame_urls?.length ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {report.key_frame_urls.map((frame) => (
            <figure key={frame.phase} className="overflow-hidden rounded-lg border border-[var(--color-border)] bg-white">
              {frame.url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={frame.url} alt={`${frame.phase} debug frame`} className="aspect-[4/3] w-full object-contain bg-black" />
              ) : null}
              <figcaption className="px-2 py-1 text-xs text-[var(--color-muted)]">
                {frame.phase.replaceAll("_", " ")}
              </figcaption>
            </figure>
          ))}
        </div>
      ) : null}

      <DebugBlock title="Phase labels" value={report.phase_map ?? []} />
      <DebugBlock title="Raw Gemini response" value={rawResponses} />
      <DebugBlock title="Final formatted report" value={finalReport} />
      <DebugBlock title="Gemini debug payload" value={report.gemini_raw ?? {}} />
    </section>
  );
}

export default function SwingReportPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const reportId = params.id as string;
  const [report, setReport] = useState<SwingReport | null>(null);
  const [comparison, setComparison] = useState<{
    state: ProgressState;
    priorMainFix: string | null;
    priorCreatedAt: string | null;
    priorFrames: SwingReport["key_frame_urls"];
  } | null>(null);
  const [drillVideoUrl, setDrillVideoUrl] = useState<string | null>(null);
  const [drillVideoTitle, setDrillVideoTitle] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);

  const fetchStatus = useCallback(async () => {
    const res = await fetch(`/api/swings/${reportId}/status`);
    const data = await readApiResponse<{
      report?: SwingReport;
      comparison?: typeof comparison;
      drillVideoUrl?: string | null;
      drillVideoTitle?: string | null;
    }>(res);
    if (!res.ok) {
      setError(data.error || "Could not load this report.");
      return;
    }
    if (!data.report) {
      setError("Could not load this report.");
      return;
    }
    setReport(data.report);
    if (data.comparison) setComparison(data.comparison);
    if (data.drillVideoUrl !== undefined) setDrillVideoUrl(data.drillVideoUrl);
    if (data.drillVideoTitle !== undefined) setDrillVideoTitle(data.drillVideoTitle);
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
            <div className="mt-4 flex flex-wrap gap-3">
              <Button
                disabled={retrying}
                onClick={async () => {
                  setRetrying(true);
                  const res = await fetch(`/api/swings/${reportId}/analyze`, { method: "POST" });
                  const data = await readApiResponse(res);
                  if (!res.ok) setError(data.error || "Could not retry this analysis.");
                  else await fetchStatus();
                  setRetrying(false);
                }}
              >
                {retrying ? "Queueing retry..." : "Retry analysis"}
              </Button>
              <a href="/upload">
                <Button variant="secondary">Upload a new swing</Button>
              </a>
            </div>
          </Card>
        </main>
      </div>
    );
  }

  const coaching = parseCoachingContent(report);
  const simplified = coaching ? getSimplifiedReport(coaching, report.phase_map) : null;
  const coachLetter = coaching ? getFeelBlueprint(coaching) : null;
  const debugEnabled =
    searchParams.get("debug") === "1" || process.env.NEXT_PUBLIC_ANALYSIS_DEBUG === "true";

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
            <div className="relative overflow-hidden rounded-lg border border-[var(--color-accent)]/30 bg-emerald-50 px-5 py-4 shadow-sm">
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
            {coachLetter?.headline?.trim() || "Your coach read"}
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
          <>
            {comparison && (
              <SwingComparison
                state={comparison.state}
                currentMainFix={simplified.main_fix}
                priorMainFix={comparison.priorMainFix}
                priorCreatedAt={comparison.priorCreatedAt}
                currentFrames={report.key_frame_urls ?? []}
                priorFrames={comparison.priorFrames ?? []}
              />
            )}
            <SimplifiedSwingReport
              report={simplified}
              frames={report.key_frame_urls}
              phaseMap={getVisiblePhaseMap(report.phase_map)}
              drillVideoUrl={drillVideoUrl}
              drillVideoTitle={drillVideoTitle}
            />
            {debugEnabled && <AnalysisDebugPanel report={report} finalReport={coaching ?? simplified} />}
            <a href="/upload" className="mt-8 block">
              <Button className="w-full" size="lg">Upload another swing</Button>
            </a>
          </>
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
