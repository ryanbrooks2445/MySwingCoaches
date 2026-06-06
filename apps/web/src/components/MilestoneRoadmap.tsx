"use client";

import { useCallback, useEffect, useState } from "react";
import { ReportMarkdown } from "@/components/ReportMarkdown";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import type { MilestoneBlock } from "@/lib/types";

function storageKey(reportId: string) {
  return `roadmap-progress-${reportId}`;
}

interface MilestoneRoadmapProps {
  reportId: string;
  weeklyFocus: string;
  milestones: MilestoneBlock[];
  day7Test: string;
}

export function MilestoneRoadmap({
  reportId,
  weeklyFocus,
  milestones,
  day7Test,
}: MilestoneRoadmapProps) {
  const [completedThrough, setCompletedThrough] = useState(-1);

  useEffect(() => {
    const saved = localStorage.getItem(storageKey(reportId));
    if (saved != null) {
      const n = parseInt(saved, 10);
      if (!Number.isNaN(n)) setCompletedThrough(n);
    }
  }, [reportId]);

  const markComplete = useCallback(
    (index: number) => {
      setCompletedThrough(index);
      localStorage.setItem(storageKey(reportId), String(index));
    },
    [reportId]
  );

  const activeIndex = completedThrough + 1;

  return (
    <div className="space-y-4">
      <p className="text-lg">
        This week:{" "}
        <strong className="text-[var(--color-accent)]">{weeklyFocus.replace(/\*\*/g, "")}</strong>
      </p>
      <p className="text-sm text-[var(--color-muted)]">
        One milestone at a time. Do not skip ahead.
      </p>

      <div className="space-y-3">
        {milestones.map((m, i) => {
          const isLockedIn = i <= completedThrough;
          const isCurrent = i === activeIndex;
          const isUpNext = i > activeIndex;

          return (
            <Card
              key={m.days}
              className={
                isCurrent
                  ? "border-[var(--color-accent)]/40"
                  : isLockedIn
                    ? "border-emerald-500/20 opacity-90"
                    : "opacity-60"
              }
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-muted)]">
                    {m.days}
                  </p>
                  <h4 className="mt-1 font-semibold">{m.title}</h4>
                </div>
                {isLockedIn && <StatusBadge status="locked_in" />}
                {isCurrent && <StatusBadge status="current_focus" />}
                {isUpNext && <StatusBadge status="up_next" />}
              </div>
              <ReportMarkdown content={m.detail} className="mt-3" />
              {isCurrent && (
                <Button size="lg" className="mt-4 w-full sm:w-auto" onClick={() => markComplete(i)}>
                  Milestone complete →
                </Button>
              )}
            </Card>
          );
        })}
      </div>

      <Card className="border-amber-500/30 bg-amber-500/5">
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge
            status={completedThrough >= milestones.length - 1 ? "current_focus" : "up_next"}
          />
          <h4 className="font-semibold">Day 7 — Upload test</h4>
        </div>
        <ReportMarkdown content={day7Test} className="mt-3" />
      </Card>
    </div>
  );
}
