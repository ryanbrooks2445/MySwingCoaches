"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AppNav } from "@/components/AppNav";
import { ScoreBar, SeverityBadge } from "@/components/ScoreRing";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import type { SwingIssue, SwingReport } from "@/lib/types";

export default function CoachReviewDetailPage() {
  const params = useParams();
  const router = useRouter();
  const reportId = params.id as string;
  const [report, setReport] = useState<SwingReport | null>(null);
  const [issues, setIssues] = useState<SwingIssue[]>([]);
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const fetchReport = useCallback(async () => {
    const res = await fetch(`/api/swings/${reportId}/status`);
    const data = await res.json();
    if (res.ok) {
      setReport(data.report);
      setIssues(data.issues ?? []);
    }
  }, [reportId]);

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  async function saveReview(complete: boolean) {
    setSaving(true);
    setMessage(null);
    const res = await fetch(`/api/coach/reviews/${reportId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes, complete }),
    });
    const data = await res.json();
    setSaving(false);
    if (!res.ok) {
      setMessage(data.error);
      return;
    }
    setMessage(complete ? "Review marked complete." : "Notes saved.");
    if (complete) router.push("/coach/reviews");
  }

  if (!report) {
    return (
      <div className="min-h-screen">
        <AppNav />
        <main className="mx-auto max-w-4xl px-4 py-16 text-center">Loading...</main>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <AppNav />
      <main className="mx-auto max-w-4xl px-4 py-8">
        <h1 className="text-3xl font-semibold">Coach review</h1>
        <p className="mt-1 text-[var(--color-muted)]">Report {reportId.slice(0, 8)}...</p>

        <Card className="mt-8">
          <h2 className="font-semibold">AI report summary</h2>
          <p className="mt-4 text-4xl font-semibold text-[var(--color-accent)]">
            {report.overall_score ?? "—"}
          </p>
          <p className="mt-2 text-[var(--color-muted)]">{report.main_diagnosis}</p>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <ScoreBar label="Setup" score={report.setup_score} />
            <ScoreBar label="Backswing" score={report.backswing_score} />
            <ScoreBar label="Downswing" score={report.downswing_score} />
            <ScoreBar label="Impact" score={report.impact_score} />
            <ScoreBar label="Finish" score={report.finish_score} />
          </div>
        </Card>

        <section className="mt-6">
          <h2 className="mb-3 font-semibold">Detected issues</h2>
          <div className="grid gap-3">
            {issues.slice(0, 5).map((issue) => (
              <Card key={issue.id}>
                <div className="flex items-center gap-2">
                  <span className="font-medium">{issue.issue}</span>
                  <SeverityBadge severity={issue.severity} />
                </div>
              </Card>
            ))}
          </div>
        </section>

        <Card className="mt-8 space-y-4">
          <h2 className="font-semibold">Human coach notes</h2>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={6}
            placeholder="Add your coaching notes for the golfer..."
            className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm"
          />
          {message && <p className="text-sm text-[var(--color-accent)]">{message}</p>}
          <div className="flex gap-3">
            <Button onClick={() => saveReview(false)} disabled={saving} variant="secondary">
              Save notes
            </Button>
            <Button onClick={() => saveReview(true)} disabled={saving}>
              Mark review complete
            </Button>
          </div>
        </Card>
      </main>
    </div>
  );
}
