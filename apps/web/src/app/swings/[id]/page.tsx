"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AppNav } from "@/components/AppNav";
import { ComparisonPanel } from "@/components/ComparisonPanel";
import { ScoreBar, ScoreRing, SeverityBadge } from "@/components/ScoreRing";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DISCLAIMER } from "@/lib/utils";
import type { DrillRecommendation, KeyFrameUrl, SwingIssue, SwingReport } from "@/lib/types";

const PHASES = ["address", "takeaway", "top", "downswing", "impact", "finish"];

export default function SwingReportPage() {
  const params = useParams();
  const reportId = params.id as string;
  const [report, setReport] = useState<SwingReport | null>(null);
  const [issues, setIssues] = useState<SwingIssue[]>([]);
  const [drills, setDrills] = useState<DrillRecommendation[]>([]);
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
    setIssues(data.issues ?? []);
    setDrills(data.drills ?? []);
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
          <h1 className="mt-6 text-2xl font-semibold">Analyzing your swing</h1>
          <p className="mt-2 text-[var(--color-muted)]">
            Extracting frames, running pose detection, and generating your coaching report...
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

  const keyFrames = (report.key_frame_urls ?? []) as KeyFrameUrl[];
  const activeFrame = keyFrames.find((f) => f.phase === activePhase);
  const landmarks = (report.pose_landmarks?.[activePhase] ?? null) as Record<string, { x: number; y: number }> | null;

  return (
    <div className="min-h-screen">
      <AppNav />
      <main className="mx-auto max-w-6xl px-4 py-8">
        {!report.ai_narrative_available && (
          <div className="mb-6 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-600">
            AI narrative unavailable — showing rules-based analysis with fallback scoring.
          </div>
        )}

        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold">Swing report</h1>
            <p className="mt-1 text-[var(--color-muted)]">
              {new Date(report.created_at).toLocaleString()}
            </p>
          </div>
          <div className="relative">
            <ScoreRing score={report.overall_score} label="Overall" size={140} />
          </div>
        </div>

        <Card className="mt-8">
          <h2 className="mb-4 font-semibold">Phase scores</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <ScoreBar label="Setup" score={report.setup_score} />
            <ScoreBar label="Backswing" score={report.backswing_score} />
            <ScoreBar label="Downswing" score={report.downswing_score} />
            <ScoreBar label="Impact" score={report.impact_score} />
            <ScoreBar label="Finish" score={report.finish_score} />
          </div>
        </Card>

        {report.main_diagnosis && (
          <Card className="mt-6">
            <h2 className="font-semibold">Main diagnosis</h2>
            <p className="mt-2 text-[var(--color-muted)]">{report.main_diagnosis}</p>
          </Card>
        )}

        <section className="mt-8">
          <h2 className="mb-4 text-xl font-semibold">Top issues</h2>
          <div className="grid gap-4 md:grid-cols-3">
            {issues.slice(0, 3).map((issue) => (
              <Card key={issue.id}>
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-medium">{issue.issue}</h3>
                  <SeverityBadge severity={issue.severity} />
                </div>
                {issue.why_it_matters && (
                  <p className="mt-2 text-sm text-[var(--color-muted)]">{issue.why_it_matters}</p>
                )}
                {issue.fix && (
                  <p className="mt-2 text-sm"><strong>Fix:</strong> {issue.fix}</p>
                )}
                {issue.drill && (
                  <p className="mt-1 text-sm"><strong>Drill:</strong> {issue.drill}</p>
                )}
              </Card>
            ))}
          </div>
        </section>

        <section className="mt-10">
          <h2 className="mb-4 text-xl font-semibold">Side-by-side comparison</h2>
          <div className="mb-4 flex flex-wrap gap-2">
            {PHASES.map((phase) => (
              <button
                key={phase}
                onClick={() => setActivePhase(phase)}
                className={`rounded-full px-4 py-1.5 text-sm capitalize transition-colors ${
                  activePhase === phase
                    ? "bg-[var(--color-accent)] text-white"
                    : "bg-[var(--color-border)]/50 hover:bg-[var(--color-border)]"
                }`}
              >
                {phase.replace("-", " ")}
              </button>
            ))}
          </div>
          <Card>
            <ComparisonPanel
              userImageUrl={activeFrame?.url ?? null}
              idealImageUrl="/placeholders/checkpoints/placeholder.svg"
              phase={activePhase}
              landmarks={landmarks}
              notes={`Checkpoint confidence: ${((activeFrame?.confidence ?? 0.5) * 100).toFixed(0)}% (MVP heuristic)`}
            />
          </Card>
        </section>

        {drills.length > 0 && (
          <section className="mt-10">
            <h2 className="mb-4 text-xl font-semibold">Recommended drills</h2>
            <div className="grid gap-4 md:grid-cols-3">
              {drills.map((drill) => (
                <Card key={drill.id}>
                  <h3 className="font-medium">{drill.title}</h3>
                  {drill.description && (
                    <p className="mt-2 text-sm text-[var(--color-muted)]">{drill.description}</p>
                  )}
                </Card>
              ))}
            </div>
          </section>
        )}

        {report.practice_plan && (
          <Card className="mt-8">
            <h2 className="font-semibold">Practice plan</h2>
            <p className="mt-2 text-[var(--color-muted)]">{report.practice_plan}</p>
          </Card>
        )}

        {report.next_upload_focus && (
          <Card className="mt-4">
            <h2 className="font-semibold">Next upload focus</h2>
            <p className="mt-2 text-[var(--color-muted)]">{report.next_upload_focus}</p>
          </Card>
        )}

        <footer className="mt-10 border-t border-[var(--color-border)] pt-6 text-sm text-[var(--color-muted)]">
          {report.disclaimer ?? DISCLAIMER}
        </footer>
      </main>
    </div>
  );
}
