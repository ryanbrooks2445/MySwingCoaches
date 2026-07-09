"use client";

import { DrillVideoEmbed } from "@/components/DrillVideoEmbed";
import { ReportMarkdown } from "@/components/ReportMarkdown";
import type { PrioritizedFeelFix } from "@/lib/types";

interface PrioritizedFeelsHeroProps {
  priorities: PrioritizedFeelFix[];
  drillVideoUrl?: string | null;
  drillVideoTitle?: string | null;
}

function FeelList({ label, feels }: { label: string; feels: string[] }) {
  if (!feels.length) return null;
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wider text-[var(--color-muted)]">{label}</p>
      <ul className="mt-2 space-y-2">
        {feels.map((feel) => (
          <li
            key={feel}
            className="rounded-lg border border-[var(--color-border)] bg-white/70 px-3 py-2 text-sm leading-relaxed text-[var(--color-foreground)]"
          >
            <ReportMarkdown content={feel} />
          </li>
        ))}
      </ul>
    </div>
  );
}

export function PrioritizedFeelsHero({
  priorities,
  drillVideoUrl,
  drillVideoTitle,
}: PrioritizedFeelsHeroProps) {
  if (!priorities.length) return null;

  return (
    <section className="overflow-hidden rounded-2xl border border-amber-500/35 bg-gradient-to-br from-amber-50 via-white to-orange-50 shadow-sm">
      <div className="border-b border-amber-500/20 bg-amber-500/10 px-5 py-4 sm:px-6">
        <p className="text-xs font-semibold uppercase tracking-wider text-amber-800">Your fix list</p>
        <h2 className="mt-1 text-xl font-semibold tracking-tight text-[var(--color-foreground)] sm:text-2xl">
          Prioritized feels
        </h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Root cause first — work down the chain when each step holds on film.
        </p>
      </div>

      <ol className="divide-y divide-amber-500/15">
        {priorities.map((priority) => (
          <li key={`${priority.rank}-${priority.title}`} className="px-5 py-5 sm:px-6">
            <div className="flex flex-wrap items-start gap-3">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-amber-500 text-sm font-bold text-white">
                {priority.rank}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-lg font-semibold text-[var(--color-foreground)]">{priority.title}</h3>
                  <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-900">
                    {priority.phase}
                  </span>
                </div>
                <ReportMarkdown
                  content={priority.issue}
                  className="mt-2 text-sm leading-relaxed text-[var(--color-foreground)]"
                />
                <p className="mt-2 text-xs font-medium uppercase tracking-wide text-amber-800">Why this rank</p>
                <ReportMarkdown
                  content={priority.why_first}
                  className="mt-1 text-sm leading-relaxed text-[var(--color-muted)]"
                />
              </div>
            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <FeelList label="Body feels" feels={priority.body_feels} />
              <FeelList label="Space feels" feels={priority.space_feels} />
            </div>

            {priority.drill?.name && (
              <div className="mt-4 rounded-xl border border-[var(--color-accent)]/25 bg-white/80 p-4">
                <p className="text-xs font-semibold uppercase tracking-wider text-[var(--color-accent)]">
                  Drill for this priority
                </p>
                <p className="mt-1 font-medium text-[var(--color-foreground)]">{priority.drill.name}</p>
                {priority.drill.why_it_helps && (
                  <ReportMarkdown content={priority.drill.why_it_helps} className="mt-2 text-sm" />
                )}
                {priority.drill.how_to_do_it && (
                  <ReportMarkdown content={priority.drill.how_to_do_it} className="mt-2 text-sm text-[var(--color-muted)]" />
                )}
                {priority.rank === 1 && drillVideoUrl && (
                  <DrillVideoEmbed
                    videoUrl={drillVideoUrl}
                    title={drillVideoTitle ?? undefined}
                    className="mt-4"
                  />
                )}
              </div>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}
