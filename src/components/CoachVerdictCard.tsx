"use client";

import { ReportMarkdown } from "@/components/ReportMarkdown";
import { overallRatingNumber } from "@/lib/coach-verdict";
import type { CoachVerdict } from "@/lib/types";
import { cn } from "@/lib/utils";

interface CoachVerdictCardProps {
  verdict: CoachVerdict;
  className?: string;
}

export function CoachVerdictCard({ verdict, className }: CoachVerdictCardProps) {
  const score = overallRatingNumber(verdict.overall_rating);

  return (
    <section
      className={cn(
        "overflow-hidden rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-50 via-white to-sky-50 shadow-sm",
        className
      )}
    >
      <div className="border-b border-emerald-500/15 px-5 py-4 sm:px-6">
        <p className="text-xs font-semibold uppercase tracking-wider text-emerald-700">
          Coach verdict
        </p>
        <div className="mt-2 flex flex-wrap items-end gap-4">
          {score ? (
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-bold tracking-tight text-[var(--color-foreground)] sm:text-5xl">
                {score}
              </span>
              <span className="pb-1 text-lg font-medium text-[var(--color-muted)]">/10</span>
            </div>
          ) : verdict.overall_rating ? (
            <p className="text-lg font-semibold text-[var(--color-foreground)]">
              {verdict.overall_rating}
            </p>
          ) : null}
          {verdict.category_ratings.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {verdict.category_ratings.map((item) => (
                <span
                  key={item.label}
                  className="rounded-full border border-emerald-500/20 bg-white/80 px-3 py-1 text-xs font-medium text-[var(--color-foreground)]"
                >
                  {item.label}: {item.rating}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="space-y-4 px-5 py-5 sm:px-6">
        {verdict.biggest_positive && (
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-emerald-700">
              The big positive
            </p>
            <ReportMarkdown
              content={verdict.biggest_positive}
              className="mt-1 text-base text-[var(--color-foreground)]"
            />
          </div>
        )}
        {verdict.main_issue && (
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-amber-700">
              Main issue
            </p>
            <ReportMarkdown
              content={verdict.main_issue}
              className="mt-1 text-base text-[var(--color-foreground)]"
            />
          </div>
        )}
        {verdict.best_fix && (
          <div className="rounded-xl border border-sky-500/25 bg-sky-50/70 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-sky-700">
              Best fix
            </p>
            <ReportMarkdown
              content={verdict.best_fix}
              className="mt-1 text-base font-medium text-[var(--color-foreground)]"
            />
          </div>
        )}
      </div>
    </section>
  );
}
