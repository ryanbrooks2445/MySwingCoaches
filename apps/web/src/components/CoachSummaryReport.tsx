"use client";

import { ReportMarkdown } from "@/components/ReportMarkdown";
import { Card } from "@/components/ui/Card";
import type { CoachSummaryReport as CoachSummaryReportType } from "@/lib/types";

interface CoachSummaryReportProps {
  report: CoachSummaryReportType;
}

function label(text: string) {
  return text.replaceAll("_", " ");
}

export function CoachSummaryReport({ report }: CoachSummaryReportProps) {
  return (
    <div className="mt-10 space-y-6">
      <section>
        <h2 className="text-lg font-semibold">Your Analysis</h2>
        <Card className="mt-3">
          <ReportMarkdown content={report.coach_summary} className="leading-relaxed" />
        </Card>
      </section>

      <section>
        <h2 className="text-lg font-semibold">What&apos;s Working</h2>
        <Card className="mt-3">
          <ul className="space-y-3">
            {(report.whats_working ?? ["There is at least one useful pattern to build around."]).slice(0, 3).map((item) => (
              <li key={item} className="text-sm leading-relaxed">
                {item}
              </li>
            ))}
          </ul>
        </Card>
      </section>

      <section>
        <p className="text-sm font-medium uppercase tracking-widest text-[var(--color-accent)]">
          The Missing Piece
        </p>
        <h1 className="mt-1 text-3xl font-semibold">{report.main_swing_leak}</h1>
      </section>

      <section>
        <h2 className="text-lg font-semibold">The Physics Problem</h2>
        <ReportMarkdown content={report.why_it_matters} className="mt-3 text-[var(--color-muted)]" />
      </section>

      <section>
        <h2 className="text-lg font-semibold">Your Feel This Week</h2>
        <Card className="mt-3">
          <ReportMarkdown
            content={report.feel_this_week ?? "Make the first fix simple enough to repeat."}
            className="mb-4 text-sm leading-relaxed"
          />
          <ul className="space-y-3">
            {report.what_to_feel.slice(0, 3).map((feel) => (
              <li key={feel} className="text-sm leading-relaxed">
                {feel}
              </li>
            ))}
          </ul>
        </Card>
      </section>

      <section>
        <h2 className="text-lg font-semibold">Drills That Unlock It</h2>
        <Card className="mt-3 space-y-4">
          <div>
            <h3 className="font-semibold">{report.fix_it_drill.name}</h3>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed">
              {report.fix_it_drill.steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ul>
          </div>
          <p className="text-sm">
            <span className="font-medium">Dose:</span> {report.fix_it_drill.dose}
          </p>
          <p className="text-sm">
            <span className="font-medium">Success check:</span> {report.fix_it_drill.success_check}
          </p>
        </Card>
      </section>

      <section>
        <h2 className="text-lg font-semibold">Your 7-Day Plan</h2>
        <Card className="mt-3">
          <ul className="space-y-3 text-sm leading-relaxed">
            {report.practice_plan_7_day.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Card>
      </section>

      <section>
        <h2 className="text-lg font-semibold">Next Upload Goal</h2>
        <Card className="mt-3">
          <ReportMarkdown content={report.next_upload_goal} className="text-sm leading-relaxed" />
        </Card>
      </section>

      <details className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)]">
        <summary className="cursor-pointer px-4 py-3 text-sm font-medium">
          Advanced Evidence
        </summary>
        <div className="space-y-5 border-t border-[var(--color-border)] p-4 text-sm">
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-[var(--color-muted)]">First checkpoint</p>
              <p className="mt-1 font-medium capitalize">{label(report.advanced_details.first_breakdown_checkpoint)}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-[var(--color-muted)]">Root cause</p>
              <p className="mt-1 font-medium">{report.advanced_details.root_cause}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-[var(--color-muted)]">Symptom</p>
              <p className="mt-1 font-medium">{report.advanced_details.symptom}</p>
            </div>
          </div>

          <div>
            <h3 className="font-semibold">Confidence note</h3>
            <p className="mt-1 text-[var(--color-muted)]">{report.advanced_details.confidence_note}</p>
          </div>

          <div>
            <h3 className="font-semibold">Camera angle limitations</h3>
            <p className="mt-1 text-[var(--color-muted)]">{report.advanced_details.camera_angle_limitations}</p>
          </div>

          {report.advanced_details.evidence_plain_english.length > 0 && (
            <div>
              <h3 className="font-semibold">Evidence in plain English</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-[var(--color-muted)]">
                {report.advanced_details.evidence_plain_english.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </details>
    </div>
  );
}
