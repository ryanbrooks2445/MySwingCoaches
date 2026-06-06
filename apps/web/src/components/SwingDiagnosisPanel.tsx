"use client";

import type { SwingDiagnosisEngine } from "@/lib/types";

interface AnnotationPoint {
  x: number;
  y: number;
}

interface AnnotationLine {
  type: string;
  from: AnnotationPoint;
  to: AnnotationPoint;
}

interface AnnotationBox {
  type: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

interface CheckpointAnnotation {
  checkpoint: string;
  lines?: AnnotationLine[];
  boxes?: AnnotationBox[];
}

interface SwingDiagnosisPanelProps {
  diagnosis: SwingDiagnosisEngine;
  checkpointImageUrl?: string | null;
  annotation?: CheckpointAnnotation | null;
}

function label(text: string) {
  return text.replaceAll("_", " ");
}

function confidence(value: number) {
  return `${Math.round(value * 100)}%`;
}

export function SwingDiagnosisPanel({
  diagnosis,
  checkpointImageUrl,
  annotation,
}: SwingDiagnosisPanelProps) {
  const drill = diagnosis.one_drill;
  const bestConfidence = Math.max(0, ...diagnosis.evidence.map((item) => item.confidence));
  const isLikely = bestConfidence > 0 && bestConfidence < 0.75;
  const title = isLikely ? "Likely first breakdown" : "Where the swing first broke down";

  return (
    <section className="mt-10">
      <p className="text-sm font-medium uppercase tracking-widest text-[var(--color-accent)]">
        {title}
      </p>
      <h2 className="mt-1 text-2xl font-semibold capitalize">
        {label(diagnosis.first_breakdown_checkpoint)}
      </h2>
      <p className="mt-2 text-[var(--color-muted)]">{diagnosis.main_diagnosis}</p>
      {diagnosis.coach_warning && (
        <p className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-700">
          {diagnosis.coach_warning}
        </p>
      )}

      <div className="mt-5 overflow-hidden rounded-lg border border-[var(--color-border)] bg-[var(--color-card)]">
        <div className="relative aspect-[3/4] max-h-[560px] bg-neutral-950">
          {checkpointImageUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={checkpointImageUrl}
              alt={`Swing checkpoint at ${diagnosis.first_breakdown_checkpoint}`}
              className="h-full w-full object-contain"
            />
          ) : (
            <div className="flex h-full items-center justify-center px-6 text-center text-sm text-[var(--color-muted)]">
              No checkpoint image available for this breakdown.
            </div>
          )}

          {annotation && (
            <svg className="pointer-events-none absolute inset-0 h-full w-full" viewBox="0 0 1 1" preserveAspectRatio="none">
              {(annotation.boxes ?? []).map((box) => (
                <rect
                  key={`${box.type}-${box.x}-${box.y}`}
                  x={box.x}
                  y={box.y}
                  width={box.width}
                  height={box.height}
                  fill="none"
                  stroke="#22c55e"
                  strokeDasharray="0.02 0.012"
                  strokeWidth="0.006"
                />
              ))}
              {(annotation.lines ?? []).map((line) => (
                <line
                  key={`${line.type}-${line.from.x}-${line.from.y}`}
                  x1={line.from.x}
                  y1={line.from.y}
                  x2={line.to.x}
                  y2={line.to.y}
                  stroke={line.type === "spine_angle_line" ? "#f97316" : "#22c55e"}
                  strokeLinecap="round"
                  strokeWidth="0.008"
                />
              ))}
            </svg>
          )}
        </div>

        <div className="grid gap-4 border-t border-[var(--color-border)] p-4 sm:grid-cols-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-[var(--color-muted)]">Root cause</p>
            <p className="mt-1 text-sm font-medium">{diagnosis.root_cause}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-[var(--color-muted)]">Symptom</p>
            <p className="mt-1 text-sm font-medium">{diagnosis.symptom}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-[var(--color-muted)]">Next checkpoint</p>
            <p className="mt-1 text-sm font-medium">{diagnosis.next_upload_focus}</p>
          </div>
        </div>
      </div>

      <div className="mt-5 grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-[var(--color-border)] p-4">
          <p className="text-xs uppercase tracking-wide text-[var(--color-muted)]">Primary fix</p>
          <p className="mt-1 text-sm font-medium">{diagnosis.fix_priority.primary}</p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] p-4">
          <p className="text-xs uppercase tracking-wide text-[var(--color-muted)]">Secondary</p>
          <p className="mt-1 text-sm font-medium">{diagnosis.fix_priority.secondary}</p>
        </div>
        <div className="rounded-lg border border-[var(--color-border)] p-4">
          <p className="text-xs uppercase tracking-wide text-[var(--color-muted)]">Optional</p>
          <p className="mt-1 text-sm font-medium">{diagnosis.fix_priority.optional}</p>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        <h3 className="text-base font-semibold">Evidence metrics</h3>
        {diagnosis.evidence.length > 0 ? (
          diagnosis.evidence.map((item) => (
            <div
              key={`${item.checkpoint}-${item.metric}`}
              className="rounded-lg border border-[var(--color-border)] p-4"
            >
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <span className="font-medium capitalize">{label(item.checkpoint)}</span>
                <span className="text-[var(--color-muted)]">/</span>
                <span className="text-[var(--color-muted)]">{label(item.metric)}</span>
                <span className="rounded-full bg-[var(--color-border)] px-2 py-0.5 text-xs">
                  {confidence(item.confidence)}
                </span>
              </div>
              <p className="mt-2 text-sm">
                Observed: {item.observed}. Expected: {item.expected}.
              </p>
              {item.interpretation && (
                <p className="mt-1 text-sm text-[var(--color-muted)]">{item.interpretation}</p>
              )}
            </div>
          ))
        ) : (
          <p className="rounded-lg border border-[var(--color-border)] p-4 text-sm text-[var(--color-muted)]">
            Confidence was too low to cite a measured checkpoint.
          </p>
        )}
      </div>

      <div className="mt-5 rounded-lg border border-[var(--color-border)] p-4">
        <h3 className="font-semibold">Why it causes the miss</h3>
        <p className="mt-2 text-sm text-[var(--color-muted)]">{diagnosis.chain_reaction}</p>
        <h3 className="mt-4 font-semibold">What to feel</h3>
        <p className="mt-2 text-sm text-[var(--color-muted)]">{diagnosis.what_to_feel}</p>
      </div>

      <div className="mt-5 rounded-lg border border-[var(--color-border)] p-4">
        <p className="text-xs uppercase tracking-wide text-[var(--color-muted)]">One drill</p>
        <h3 className="mt-1 font-semibold">{drill.name}</h3>
        <p className="mt-2 text-sm text-[var(--color-muted)]">{drill.instructions}</p>
        <p className="mt-3 text-sm">
          <span className="font-medium">Dose:</span> {drill.sets_reps}
        </p>
        <p className="mt-1 text-sm">
          <span className="font-medium">Success metric:</span> {drill.success_metric}
        </p>
      </div>

    </section>
  );
}
