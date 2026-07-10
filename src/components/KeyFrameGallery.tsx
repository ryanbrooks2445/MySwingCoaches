"use client";

import { formatPhaseLabel } from "@/lib/status-labels";
import { cn } from "@/lib/utils";

interface KeyFrameGalleryProps {
  frames: { phase: string; url: string | null }[];
  activePhase: string;
  onPhaseChange: (phase: string) => void;
}

export function KeyFrameGallery({ frames, activePhase, onPhaseChange }: KeyFrameGalleryProps) {
  const active = frames.find((f) => f.phase === activePhase) ?? frames[0];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {frames.map((frame) => (
          <button
            key={frame.phase}
            onClick={() => onPhaseChange(frame.phase)}
            className={cn(
              "rounded-full px-4 py-1.5 text-sm transition-colors",
              activePhase === frame.phase
                ? "bg-[var(--color-accent)] text-white"
                : "bg-[var(--color-border)]/50 hover:bg-[var(--color-border)]"
            )}
          >
            {formatPhaseLabel(frame.phase)}
          </button>
        ))}
      </div>

      <div className="overflow-hidden rounded-xl border border-[var(--color-border)] bg-neutral-900 aspect-[3/4] max-h-[520px]">
        {active?.url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={active.url}
            alt={`Swing at ${formatPhaseLabel(active.phase)}`}
            className="h-full w-full object-contain"
          />
        ) : (
          <div className="flex h-full min-h-[320px] items-center justify-center text-[var(--color-muted)]">
            No frame available
          </div>
        )}
      </div>

      <p className="text-sm text-[var(--color-muted)]">
        Key moments from your swing video. Coaching is based on the full video, not these stills alone.
      </p>
    </div>
  );
}
