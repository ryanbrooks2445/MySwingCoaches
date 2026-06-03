"use client";

import Link from "next/link";
import { Card } from "@/components/ui/Card";
import type { SwingReport, SwingVideo } from "@/lib/types";

export function SwingCard({
  video,
  report,
}: {
  video: SwingVideo;
  report?: SwingReport | null;
}) {
  const status = report?.status ?? video.status;
  const score = report?.overall_score;

  return (
    <Link href={`/swings/${report?.id ?? video.id}`}>
      <Card className="transition-shadow hover:shadow-md">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">{video.original_filename ?? "Swing video"}</p>
            <p className="text-sm text-[var(--color-muted)]">
              {new Date(video.created_at).toLocaleDateString()}
            </p>
          </div>
          <div className="text-right">
            {score != null ? (
              <p className="text-2xl font-semibold text-[var(--color-accent)]">{score}</p>
            ) : (
              <p className="text-sm capitalize text-[var(--color-muted)]">{status}</p>
            )}
          </div>
        </div>
      </Card>
    </Link>
  );
}
