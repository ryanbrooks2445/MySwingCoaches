"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AppNav } from "@/components/AppNav";
import { CoachSummaryReport } from "@/components/CoachSummaryReport";
import { KeyFrameGallery } from "@/components/KeyFrameGallery";
import { ReportMarkdown } from "@/components/ReportMarkdown";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { getCoachSummaryReport, parseCoachingContent } from "@/lib/coaching";
import { SWING_MODE_LABELS } from "@/lib/pricing";
import { DISCLAIMER } from "@/lib/utils";
import type { KeyFrameUrl, SwingReport } from "@/lib/types";

const PHASES = [
  "setup_address",
  "takeaway",
  "club_parallel_back",
  "lead_arm_parallel_back",
  "top_of_backswing",
  "transition",
  "lead_arm_parallel_down",
  "shaft_parallel_down",
  "impact",
  "release",
  "finish",
];

export default function SwingReportPage() {
  const params = useParams();
  const reportId = params.id as string;
  const [report, setReport] = useState<SwingReport | null>(null);
  const [activePhase, setActivePhase] = useState("setup_address");
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);

  const fetchStatus = useCallback(async () => {
    const res = await fetch(`/api/swings/${reportId}/status`);
    const data = await res.json();
    if (!res.ok) {
      setError(data.error);
      return;
    }
    setReport(data.report);
  }, [reportId]);

  const retryAnalysis = useCallback(async () => {
    setRetrying(true);
    setError(null);
    setReport((current) => current ? { ...current, status: "processing", error_message: null } : current);
    try {
      const res = await fetch(`/api/swings/${reportId}/analyze`, { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || "Analysis retry failed.");
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis retry failed.");
      await fetchStatus();
    } finally {
      setRetrying(false);
    }
  }, [fetchStatus, reportId]);

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
        <main className="mx-auto max-w-4xl px-4 py-8">
          <Card className="text-center">
            <p className="text-red-500">{error}</p>
            <Button className="mt-4" onClick={fetchStatus}>Retry</Button>
          </Card>
        </main>
      </div>
    );
  }

  if (!report || report.status === "processing" || retrying) {
    return (
      <div className="min-h-screen">
        <AppNav />
        <main className="mx-auto max-w-4xl px-4 py-16 text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-[var(--color-border)] border-t-[var(--color-accent)]" />
            <h1 className="mt-6 text-2xl font-semibold">
            {retrying ? "Retrying your analysis" : "Building your swing analysis"}
          </h1>
          <p className="mt-2 text-[var(--color-muted)]">
            Watching your swing and mapping feels, cause-and-effect, and milestones. Usually 1–3 minutes.
          </p>
        </main>
      </div>
    );
  }

  if (report.status === "failed") {
    return (
      <div className="min-h-screen">
        <AppNav />
        <main className="mx-auto max-w-4xl px-4 py-8">
          <Card>
            <h1 className="text-xl font-semibold text-red-500">Analysis failed</h1>
            <p className="mt-2 text-[var(--color-muted)]">{report.error_message}</p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Button onClick={retryAnalysis} disabled={retrying}>
                {retrying ? "Retrying..." : "Retry analysis"}
              </Button>
              <a href="/upload" className="inline-block">
                <Button variant="ghost">Upload Another Swing</Button>
              </a>
            </div>
          </Card>
        </main>
      </div>
    );
  }

  const coaching = parseCoachingContent(report);
  const coachReport = coaching ? getCoachSummaryReport(coaching) : null;
  const keyFrames = (report.key_frame_urls ?? []) as KeyFrameUrl[];
  const phases =
    keyFrames.length > 0 ? keyFrames.map((f) => f.phase) : PHASES;
  const galleryFrames = phases.map((phase) => ({
    phase,
    url: keyFrames.find((f) => f.phase === phase)?.url ?? null,
  }));

  return (
    <div className="min-h-screen">
      <AppNav />
      <main className="mx-auto max-w-3xl px-4 py-8">
        {!report.ai_narrative_available && (
          <div className="mb-6 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-600">
            {report.error_message
              ? `Analysis unavailable: ${report.error_message}`
              : "Analysis unavailable — please try uploading again."}
          </div>
        )}

        <div>
          {coaching?.personalized_greeting && (
            <p className="text-lg leading-snug text-[var(--color-foreground)]">
              {coaching.personalized_greeting}
            </p>
          )}
          {report.swing_mode && (
            <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-muted)]">
              {SWING_MODE_LABELS[report.swing_mode]}
            </p>
          )}
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            {new Date(report.created_at).toLocaleString()}
          </p>
        </div>

        {coaching ? (
          <>
            {coachReport && <CoachSummaryReport report={coachReport} />}
          </>
        ) : (
          <Card className="mt-8">
            <p className="text-[var(--color-muted)]">
              This is an older report format. Upload a new swing to get the latest coaching analysis.
            </p>
            {report.main_diagnosis && (
              <ReportMarkdown content={report.main_diagnosis} className="mt-4" />
            )}
          </Card>
        )}

        {keyFrames.length > 0 && (
          <section className="mt-12">
            <h2 className="mb-4 text-xl font-semibold">Swing Reference Frames</h2>
            <Card>
              <KeyFrameGallery
                frames={galleryFrames}
                activePhase={activePhase}
                onPhaseChange={setActivePhase}
              />
            </Card>
          </section>
        )}

        <footer className="mt-10 border-t border-[var(--color-border)] pt-6 text-sm text-[var(--color-muted)]">
          {report.disclaimer ?? coaching?.disclaimer ?? DISCLAIMER}
        </footer>
      </main>
    </div>
  );
}
