"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AppNav } from "@/components/AppNav";
import { ReportMarkdown } from "@/components/ReportMarkdown";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { readApiResponse } from "@/lib/api-response";
import { getFeelBlueprint, parseCoachingContent } from "@/lib/coaching";
import type { SwingReport } from "@/lib/types";

export default function CoachReviewDetailPage() {
  const params = useParams();
  const router = useRouter();
  const reportId = params.id as string;
  const [report, setReport] = useState<SwingReport | null>(null);
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const fetchReport = useCallback(async () => {
    const res = await fetch(`/api/swings/${reportId}/status`);
    const data = await readApiResponse<{ report?: SwingReport }>(res);
    if (res.ok) {
      setReport(data.report ?? null);
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
    const data = await readApiResponse(res);
    setSaving(false);
    if (!res.ok) {
      setMessage(data.error || "Could not save review.");
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

  const coaching = parseCoachingContent(report);
  const feel = coaching ? getFeelBlueprint(coaching) : null;

  return (
    <div className="min-h-screen">
      <AppNav />
      <main className="mx-auto max-w-4xl px-4 py-8">
        <h1 className="text-3xl font-semibold">Coach review</h1>
        <p className="mt-1 text-[var(--color-muted)]">Report {reportId.slice(0, 8)}...</p>

        <Card className="mt-8">
          <h2 className="font-semibold">AI blueprint summary</h2>
          {coaching && feel ? (
            <div className="mt-4 space-y-4">
              <p className="text-xl font-semibold text-[var(--color-accent)]">{feel.headline}</p>
              <ReportMarkdown content={feel.opening_narrative} />
              <p className="text-sm text-[var(--color-muted)]">
                Ceiling: {feel.current_ceiling.slice(0, 120)}…
              </p>
              <p className="text-sm text-[var(--color-muted)]">
                Feels: {feel.body_part_cue} · {feel.spatial_cue}
              </p>
              <p className="text-sm text-[var(--color-muted)]">
                Weekly focus: {coaching.roadmap?.weekly_focus?.replace(/\*\*/g, "") ?? "—"}
              </p>
            </div>
          ) : (
            <p className="mt-2 text-[var(--color-muted)]">{report.main_diagnosis}</p>
          )}
        </Card>

        <Card className="mt-6">
          <h2 className="mb-3 font-semibold">Coach notes</h2>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={6}
            className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm"
            placeholder="Add review notes for the player..."
          />
          {message && <p className="mt-2 text-sm text-[var(--color-muted)]">{message}</p>}
          <div className="mt-4 flex gap-3">
            <Button onClick={() => saveReview(false)} disabled={saving}>
              Save notes
            </Button>
            <Button variant="secondary" onClick={() => saveReview(true)} disabled={saving}>
              Complete review
            </Button>
          </div>
        </Card>
      </main>
    </div>
  );
}
