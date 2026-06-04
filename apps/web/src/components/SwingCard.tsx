"use client";

import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/StatusBadge";
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

  return (
    <Link href={`/swings/${report?.id ?? video.id}`}>
      <Card className="transition-shadow hover:shadow-md">
        <div className="flex items-center justify-between gap-4">
          <div className="min-w-0">
            <p className="truncate font-medium">{video.original_filename ?? "Swing video"}</p>
            <p className="text-sm text-[var(--color-muted)]">
              {new Date(video.created_at).toLocaleDateString()}
            </p>
            {focus && report?.status === "ready" && (
              <p className="mt-1 truncate text-sm text-[var(--color-accent)]">{focus}</p>
            )}
          </div>
          <div className="shrink-0">
            {report?.status === "ready" && focus ? (
              <StatusBadge status="current_focus" />
            ) : (
              <p className="text-sm capitalize text-[var(--color-muted)]">{status}</p>
            )}
          </div>
        </div>
      </Card>
    </Link>
  );
}
