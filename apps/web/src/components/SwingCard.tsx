"use client";

import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { DeleteSwingButton } from "@/components/DeleteSwingButton";
import { StatusBadge } from "@/components/StatusBadge";
import { SWING_MODE_LABELS } from "@/lib/pricing";
import type { SwingReport, SwingVideo } from "@/lib/types";
import { getReportFocusLabel } from "@/lib/coaching";

export function SwingCard({
  video,
  report,
}: {
  video: SwingVideo;
  report?: SwingReport | null;
}) {
  const status = report?.status ?? video.status;
  const focus = report ? getReportFocusLabel(report) : null;
  const reportId = report?.id;

  return (
    <Card className="transition-shadow hover:shadow-md">
      <div className="flex items-center justify-between gap-4">
        <Link
          href={`/swings/${reportId ?? video.id}`}
          className="min-w-0 flex-1"
        >
          <p className="truncate font-medium">{video.original_filename ?? "Swing video"}</p>
          <p className="text-sm text-[var(--color-muted)]">
            {video.swing_mode && video.swing_mode in SWING_MODE_LABELS
              ? `${SWING_MODE_LABELS[video.swing_mode]} · `
              : ""}
            {new Date(video.created_at).toLocaleDateString()}
          </p>
          {focus && report?.status === "ready" && (
            <p className="mt-1 truncate text-sm text-[var(--color-accent)]">{focus}</p>
          )}
        </Link>
        <div className="flex shrink-0 flex-col items-end gap-2">
          {report?.status === "ready" && focus ? (
            <StatusBadge status="current_focus" />
          ) : (
            <p className="text-sm capitalize text-[var(--color-muted)]">{status}</p>
          )}
          {reportId && (
            <DeleteSwingButton reportId={reportId} label="Delete" />
          )}
        </div>
      </div>
    </Card>
  );
}
