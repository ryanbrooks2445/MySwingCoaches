import { cn } from "@/lib/utils";

export function ScoreRing({
  score,
  label,
  size = 120,
}: {
  score: number | null;
  label: string;
  size?: number;
}) {
  const value = score ?? 0;
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <div className="relative flex flex-col items-center gap-2">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth={8}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-accent)"
          strokeWidth={8}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute flex flex-col items-center" style={{ width: size, height: size }}>
        <span className="mt-[38%] text-2xl font-semibold">{score ?? "—"}</span>
      </div>
      <span className="text-sm text-[var(--color-muted)]">{label}</span>
    </div>
  );
}

export function ScoreBar({
  label,
  score,
}: {
  label: string;
  score: number | null;
}) {
  const value = score ?? 0;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span>{label}</span>
        <span className="font-medium">{score ?? "—"}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-[var(--color-border)]">
        <div
          className="h-full rounded-full bg-[var(--color-accent)] transition-all"
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

export function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span
      className={cn(
        "rounded-full px-2.5 py-0.5 text-xs font-medium capitalize",
        severity === "high" && "bg-red-500/15 text-red-500",
        severity === "medium" && "bg-amber-500/15 text-amber-500",
        severity === "low" && "bg-emerald-500/15 text-emerald-500"
      )}
    >
      {severity}
    </span>
  );
}
