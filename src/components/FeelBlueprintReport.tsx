"use client";

import { ReportMarkdown } from "@/components/ReportMarkdown";
import { Card } from "@/components/ui/Card";
import type { FeelBlueprintDiagnostic } from "@/lib/types";

interface FeelBlueprintReportProps {
  feel: FeelBlueprintDiagnostic;
}

export function FeelBlueprintReport({ feel }: FeelBlueprintReportProps) {
  return (
    <Card className="mt-3 space-y-8">
      <ReportMarkdown content={feel.opening_narrative} className="text-[var(--color-foreground)] leading-relaxed" />

      <div>
        <h3 className="text-base font-semibold">What&apos;s working</h3>
        <p className="text-xs text-[var(--color-muted)]">Your athletic engine</p>
        <ul className="mt-4 space-y-5">
          {feel.strengths.map((item) => (
            <li key={item.title}>
              <p className="font-medium text-[var(--color-foreground)]">{item.title}</p>
              <ReportMarkdown content={item.detail} className="mt-1 text-sm leading-relaxed" />
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h3 className="text-base font-semibold">The missing piece</h3>
        <p className="text-xs text-[var(--color-muted)]">Final puzzle links in your chain</p>
        <ol className="mt-4 list-decimal space-y-5 pl-5">
          {feel.flaws.map((item) => (
            <li key={item.title}>
              <p className="font-medium text-[var(--color-foreground)]">{item.title}</p>
              <ReportMarkdown content={item.detail} className="mt-1 text-sm leading-relaxed" />
            </li>
          ))}
        </ol>
      </div>

      <div className="space-y-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-background)]/50 p-4">
        <div>
          <h3 className="text-sm font-semibold">What is their ceiling?</h3>
          <p className="mt-1 text-xs font-medium uppercase tracking-wide text-[var(--color-muted)]">
            If nothing changes
          </p>
          <ReportMarkdown content={feel.current_ceiling} className="mt-2 text-sm leading-relaxed" />
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-accent)]">
            When they unlock the missing piece
          </p>
          <ReportMarkdown content={feel.potential_ceiling} className="mt-2 text-sm leading-relaxed" />
        </div>
      </div>

      <div>
        <h3 className="text-base font-semibold">The pro fixes</h3>
        <ul className="mt-4 space-y-5">
          {feel.pro_fixes.map((fix) => (
            <li key={fix.title}>
              <p className="font-medium text-[var(--color-accent)]">{fix.title}</p>
              <ReportMarkdown content={fix.detail} className="mt-1 text-sm leading-relaxed" />
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-xl border border-[var(--color-accent)]/30 bg-[var(--color-accent)]/10 p-4">
        <h3 className="text-sm font-semibold text-[var(--color-accent)]">Exact feels at the ball</h3>
        <div className="mt-3 space-y-3">
          <div>
            <p className="text-xs font-medium text-[var(--color-muted)]">Body</p>
            <ReportMarkdown content={feel.body_part_cue} className="mt-1" />
          </div>
          <div>
            <p className="text-xs font-medium text-[var(--color-muted)]">Space</p>
            <ReportMarkdown content={feel.spatial_cue} className="mt-1" />
          </div>
        </div>
      </div>
    </Card>
  );
}
