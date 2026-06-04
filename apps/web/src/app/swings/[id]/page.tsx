"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AppNav } from "@/components/AppNav";
import { BlueprintPhaseViewer } from "@/components/BlueprintPhaseViewer";
import { KeyFrameGallery } from "@/components/KeyFrameGallery";
import { MilestoneRoadmap } from "@/components/MilestoneRoadmap";
import { ReportMarkdown } from "@/components/ReportMarkdown";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { parseCoachingContent } from "@/lib/coaching";
import { DISCLAIMER } from "@/lib/utils";
import type { KeyFrameUrl, SwingReport } from "@/lib/types";

const PHASES = ["address", "takeaway", "top", "downswing", "impact", "finish"];

export default function SwingReportPage() {
  const params = useParams();
  const reportId = params.id as string;
  const [report, setReport] = useState<SwingReport | null>(null);
  const [activePhase, setActivePhase] = useState("address");
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    const res = await fetch(`/api/swings/${reportId}/status`);
    const data = await res.json();
    if (!res.ok) {
      setError(data.error);
      return;
    }
    setReport(data.report);
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
        <main className="mx-auto max-w-4xl px-4 py-8">
          <Card className="text-center">
            <p className="text-red-500">{error}</p>
            <Button className="mt-4" onClick={fetchStatus}>Retry</Button>
          </Card>
        </main>
      </div>
    );
  }

  if (!report || report.status === "processing") {
    return (
      <div className="min-h-screen">
        <AppNav />
        <main className="mx-auto max-w-4xl px-4 py-16 text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-[var(--color-border)] border-t-[var(--color-accent)]" />
          <h1 className="mt-6 text-2xl font-semibold">Building your coaching blueprint</h1>
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
            <a href="/upload" className="mt-4 inline-block">
              <Button>Try again</Button>
            </a>
          </Card>
        </main>
      </div>
    );
  }

  const coaching = parseCoachingContent(report);
  const keyFrames = (report.key_frame_urls ?? []) as KeyFrameUrl[];
  const galleryFrames = PHASES.map((phase) => ({
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
              ? `Blueprint unavailable: ${report.error_message}`
              : "Blueprint unavailable — please try uploading again."}
          </div>
        )}

        <div>
          {coaching?.personalized_greeting && (
            <p className="text-lg leading-snug text-[var(--color-foreground)]">
              {coaching.personalized_greeting}
            </p>
          )}
          <p className="mt-4 text-sm font-medium uppercase tracking-widest text-[var(--color-accent)]">
            Your focus
          </p>
          <h1 className="mt-1 text-3xl font-semibold">
            {coaching?.diagnostic.headline ?? report.main_diagnosis ?? "Swing blueprint"}
          </h1>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            {new Date(report.created_at).toLocaleString()}
          </p>
        </div>

        {coaching ? (
          <>
            <section className="mt-10">
              <h2 className="text-lg font-semibold">What&apos;s happening</h2>
              <Card className="mt-3 space-y-4">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-muted)]">Ball flight</p>
                  <ReportMarkdown content={coaching.diagnostic.what_your_eye_sees} className="mt-1" />
                </div>
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-muted)]">Root cause</p>
                  <ReportMarkdown content={coaching.diagnostic.mechanical_cause} className="mt-1" />
                </div>
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-muted)]">Chain reaction</p>
                  <ReportMarkdown content={coaching.diagnostic.kinetic_chain} className="mt-1" />
                </div>
              </Card>
            </section>

            <section className="mt-10">
              <h2 className="text-lg font-semibold">Your feels</h2>
              <p className="mt-1 text-sm text-[var(--color-muted)]">One phase at a time. Watch the clip. Lock in the feel.</p>
              <Card className="mt-4">
                <BlueprintPhaseViewer
                  reportId={reportId}
                  headline={coaching.blueprint.headline}
                  intro={coaching.blueprint.intro}
                  steps={coaching.blueprint.steps}
                />
              </Card>
            </section>

            <section className="mt-10">
              <h2 className="text-lg font-semibold">This week</h2>
              <Card className="mt-4">
                <MilestoneRoadmap
                  reportId={reportId}
                  weeklyFocus={coaching.roadmap.weekly_focus}
                  milestones={coaching.roadmap.milestones}
                  day7Test={coaching.roadmap.day_7_test}
                />
              </Card>
            </section>

            <Card className="mt-6">
              <h2 className="text-sm font-medium">Next film</h2>
              <ReportMarkdown
                content={coaching.next_upload_focus || report.next_upload_focus || ""}
                className="mt-2"
              />
            </Card>
          </>
        ) : (
          <Card className="mt-8">
            <p className="text-[var(--color-muted)]">
              This is an older report format. Upload a new swing to get the full 3-part coaching blueprint.
            </p>
            {report.main_diagnosis && (
              <ReportMarkdown content={report.main_diagnosis} className="mt-4" />
            )}
          </Card>
        )}

        {keyFrames.length > 0 && (
          <section className="mt-12">
            <h2 className="mb-4 text-xl font-semibold">Swing reference frames</h2>
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
