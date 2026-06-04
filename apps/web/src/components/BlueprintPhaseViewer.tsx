"use client";

import { useCallback, useEffect, useState } from "react";
import { DrillVideoEmbed } from "@/components/DrillVideoEmbed";
import { ReportMarkdown } from "@/components/ReportMarkdown";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { resolveDrillVideoUrl } from "@/lib/drill-videos";
import type { BlueprintStep } from "@/lib/types";

function storageKey(reportId: string) {
  return `blueprint-progress-${reportId}`;
}

function stepStatus(index: number, activeIndex: number, lockedThrough: number): "current_focus" | "locked_in" | "up_next" {
  if (index < lockedThrough) return "locked_in";
  if (index === activeIndex) return "current_focus";
  return "up_next";
}

const STEP_TYPE_LABEL: Record<BlueprintStep["step_type"], string> = {
  setup: "Setup anchor",
  visual_cue: "Visual cue",
  constraint_drill: "Constraint drill",
};

interface BlueprintPhaseViewerProps {
  reportId: string;
  headline: string;
  intro: string;
  steps: BlueprintStep[];
}

export function BlueprintPhaseViewer({
  reportId,
  headline,
  intro,
  steps,
}: BlueprintPhaseViewerProps) {
  const [lockedThrough, setLockedThrough] = useState(0);
  const activeIndex = Math.min(lockedThrough, steps.length - 1);

  useEffect(() => {
    const saved = localStorage.getItem(storageKey(reportId));
    if (saved != null) {
      const n = parseInt(saved, 10);
      if (!Number.isNaN(n)) setLockedThrough(Math.min(n, steps.length - 1));
    }
  }, [reportId, steps.length]);

  const markLockedIn = useCallback(() => {
    if (activeIndex >= steps.length - 1) {
      setLockedThrough(steps.length);
      localStorage.setItem(storageKey(reportId), String(steps.length));
      return;
    }
    const next = activeIndex + 1;
    setLockedThrough(next);
    localStorage.setItem(storageKey(reportId), String(next));
  }, [activeIndex, reportId, steps.length]);

  const step = steps[activeIndex];
  const allComplete = lockedThrough >= steps.length;
  const drillVideo = step ? resolveDrillVideoUrl(step.video_url, step.video_slug, step.step_type) : null;

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold">{headline}</h3>
        <ReportMarkdown content={intro} className="mt-2" />
      </div>

      <div className="flex flex-wrap gap-2">
        {steps.map((s, i) => (
          <StatusBadge
            key={s.title}
            status={stepStatus(i, activeIndex, lockedThrough)}
          />
        ))}
      </div>

      {!allComplete && step && (
        <Card className="border-[var(--color-accent)]/30">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-muted)]">
              Phase {activeIndex + 1} · {STEP_TYPE_LABEL[step.step_type]}
            </p>
            <StatusBadge status="current_focus" />
          </div>
          <h4 className="mt-3 text-xl font-semibold">{step.title}</h4>

          {drillVideo && (
            <DrillVideoEmbed
              className="mt-4"
              videoUrl={drillVideo.url}
              title={step.video_title ?? drillVideo.title}
            />
          )}

          {step.adjustment && (
            <div className="mt-4">
              <p className="text-sm font-medium text-[var(--color-foreground)]">The adjustment</p>
              <ReportMarkdown content={step.adjustment} className="mt-1" />
            </div>
          )}
          {step.action && (
            <div className="mt-4">
              <p className="text-sm font-medium text-[var(--color-foreground)]">The action</p>
              <ReportMarkdown content={step.action} className="mt-1" />
            </div>
          )}
          <div className="mt-4 rounded-lg bg-[var(--color-accent)]/10 p-4">
            <p className="text-sm font-medium text-[var(--color-accent)]">The feel</p>
            <ReportMarkdown content={step.feel} className="mt-1 text-[var(--color-foreground)]" />
          </div>
          {step.success_condition && (
            <div className="mt-4">
              <p className="text-sm font-medium text-[var(--color-foreground)]">Success condition</p>
              <ReportMarkdown content={step.success_condition} className="mt-1" />
            </div>
          )}

          <Button className="mt-6 w-full sm:w-auto" onClick={markLockedIn}>
            {activeIndex >= steps.length - 1 ? "Blueprint complete — start the roadmap" : "I've got this feel — unlock next phase"}
          </Button>
        </Card>
      )}

      {allComplete && (
        <Card className="border-emerald-500/30 bg-emerald-500/5 text-center">
          <StatusBadge status="locked_in" className="mb-3" />
          <p className="font-medium text-emerald-400">All blueprint phases locked in</p>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            Move to your 7-day milestone plan below.
          </p>
        </Card>
      )}
    </div>
  );
}
