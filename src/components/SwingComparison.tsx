"use client";

import type { KeyFrameUrl } from "@/lib/types";
import type { ProgressState } from "@/lib/phase-frames";
import { confidenceBadgeClass, confidenceLabel } from "@/lib/phase-frames";
import { formatPhaseLabel } from "@/lib/status-labels";
import { cn } from "@/lib/utils";

const STATE_LABELS: Record<ProgressState, string> = {
  first_upload: "First upload — baseline set",
  improved: "Progress since last upload",
  same_priority: "Same priority as last time",
  new_priority: "New priority this upload",
};

interface SwingComparisonProps {
  state: ProgressState;
  currentMainFix: string;
  priorMainFix: string | null;
  priorCreatedAt: string | null;
  currentFrames: KeyFrameUrl[];
  priorFrames: KeyFrameUrl[];
}

export function SwingComparison({
  state,
  currentMainFix,
  priorMainFix,
  priorCreatedAt,
  currentFrames,
  priorFrames,
}: SwingComparisonProps) {
  const comparePhases = ["address", "top", "impact", "impact_window_estimate", "finish"];

  const pairs = comparePhases
    .map((phase) => {
      const current = currentFrames.find((f) => f.phase === phase);
      const prior = priorFrames.find((f) => f.phase === phase);
      if (!current?.url && !prior?.url) return null;
      return { phase, current, prior };
    })
    .filter(Boolean) as Array<{
    phase: string;
    current?: KeyFrameUrl;
    prior?: KeyFrameUrl;
  }>;

  return (
    <section className="mt-8 space-y-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-[var(--color-accent)]">
          Since your last upload
        </p>
        <h2 className="mt-1 text-lg font-semibold">{STATE_LABELS[state]}</h2>
        {priorCreatedAt && state !== "first_upload" && (
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            Compared to {new Date(priorCreatedAt).toLocaleDateString()}
          </p>
        )}
      </div>

      {state !== "first_upload" && priorMainFix && (
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-lg border border-[var(--color-border)] p-3">
            <p className="text-xs font-medium uppercase text-[var(--color-muted)]">Then</p>
            <p className="mt-1 text-sm">{priorMainFix}</p>
          </div>
          <div className="rounded-lg border border-[var(--color-accent)]/30 bg-[var(--color-accent)]/5 p-3">
            <p className="text-xs font-medium uppercase text-[var(--color-muted)]">Now</p>
            <p className="mt-1 text-sm">{currentMainFix}</p>
          </div>
        </div>
      )}

      {pairs.length > 0 && state !== "first_upload" && (
        <div className="space-y-3">
          <p className="text-sm font-medium text-[var(--color-foreground)]">Same phase comparison</p>
          <div className="grid gap-4">
            {pairs.map(({ phase, current, prior }) => (
              <div key={phase} className="grid grid-cols-2 gap-2">
                <figure className="overflow-hidden rounded-lg border border-[var(--color-border)]">
                  {prior?.url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={prior.url}
                      alt={`Prior ${phase}`}
                      className="aspect-[4/3] w-full bg-black object-contain"
                    />
                  ) : (
                    <div className="flex aspect-[4/3] items-center justify-center bg-[var(--color-border)]/30 text-xs text-[var(--color-muted)]">
                      No prior frame
                    </div>
                  )}
                  <figcaption className="px-2 py-1 text-xs text-[var(--color-muted)]">
                    Then · {formatPhaseLabel(phase)}
                  </figcaption>
                </figure>
                <figure className="overflow-hidden rounded-lg border border-[var(--color-border)]">
                  {current?.url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={current.url}
                      alt={`Current ${phase}`}
                      className="aspect-[4/3] w-full bg-black object-contain"
                    />
                  ) : (
                    <div className="flex aspect-[4/3] items-center justify-center bg-[var(--color-border)]/30 text-xs text-[var(--color-muted)]">
                      Not visible
                    </div>
                  )}
                  <figcaption className="flex gap-1 px-2 py-1 text-xs text-[var(--color-muted)]">
                    <span>Now · {formatPhaseLabel(phase)}</span>
                    {current?.confidence !== undefined && (
                      <span
                        className={cn(
                          "rounded px-1 text-[10px] font-semibold uppercase",
                          confidenceBadgeClass(confidenceLabel(current.confidence))
                        )}
                      >
                        {confidenceLabel(current.confidence)}
                      </span>
                    )}
                  </figcaption>
                </figure>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
