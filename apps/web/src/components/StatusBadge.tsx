"use client";

import { cn } from "@/lib/utils";

type PhaseStatus = "current_focus" | "locked_in" | "up_next";

const STATUS_LABEL: Record<PhaseStatus, string> = {
  current_focus: "Current Focus",
  locked_in: "Locked In",
  up_next: "Up Next",
};

const STATUS_STYLE: Record<PhaseStatus, string> = {
  current_focus: "bg-[var(--color-accent)] text-white",
  locked_in: "bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/40",
  up_next: "bg-[var(--color-border)]/60 text-[var(--color-muted)]",
};

export function StatusBadge({
  status,
  className,
}: {
  status: PhaseStatus;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-3 py-1 text-xs font-medium",
        STATUS_STYLE[status],
        className
      )}
    >
      {STATUS_LABEL[status]}
    </span>
  );
}
