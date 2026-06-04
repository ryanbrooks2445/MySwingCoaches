"use client";

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
            className={`rounded-full px-4 py-1.5 text-sm capitalize transition-colors ${
              activePhase === frame.phase
                ? "bg-[var(--color-accent)] text-white"
                : "bg-[var(--color-border)]/50 hover:bg-[var(--color-border)]"
            }`}
          >
            {frame.phase.replace("_", " ")}
          </button>
        ))}
      </div>

      <div className="overflow-hidden rounded-xl border border-[var(--color-border)] bg-neutral-900 aspect-[3/4] max-h-[520px]">
        {active?.url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={active.url}
            alt={`Swing at ${active.phase}`}
            className="h-full w-full object-contain"
          />
        ) : (
          <div className="flex h-full min-h-[320px] items-center justify-center text-[var(--color-muted)]">
            No frame available
          </div>
        )}
      </div>

      <p className="text-sm text-[var(--color-muted)]">
        Key moments from your swing video (evenly sampled). Coaching is based on the full video, not these stills alone.
      </p>
    </div>
  );
}
