"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

const POSE_CONNECTIONS = [
  ["left_shoulder", "right_shoulder"],
  ["left_shoulder", "left_hip"],
  ["right_shoulder", "right_hip"],
  ["left_hip", "right_hip"],
  ["left_shoulder", "left_elbow"],
  ["left_elbow", "left_wrist"],
  ["right_shoulder", "right_elbow"],
  ["right_elbow", "right_wrist"],
  ["left_hip", "left_knee"],
  ["left_knee", "left_ankle"],
  ["right_hip", "right_knee"],
  ["right_knee", "right_ankle"],
];

function drawPoseOverlay(
  ctx: CanvasRenderingContext2D,
  landmarks: Record<string, { x: number; y: number }> | null,
  width: number,
  height: number
) {
  if (!landmarks) return;

  ctx.strokeStyle = "#22c55e";
  ctx.lineWidth = 2;
  for (const [a, b] of POSE_CONNECTIONS) {
    const p1 = landmarks[a];
    const p2 = landmarks[b];
    if (p1 && p2) {
      ctx.beginPath();
      ctx.moveTo(p1.x * width, p1.y * height);
      ctx.lineTo(p2.x * width, p2.y * height);
      ctx.stroke();
    }
  }

  const nose = landmarks.nose;
  if (nose) {
    ctx.fillStyle = "#ef4444";
    ctx.beginPath();
    ctx.arc(nose.x * width, nose.y * height, 5, 0, Math.PI * 2);
    ctx.fill();
  }
}

interface ComparisonPanelProps {
  userImageUrl: string | null;
  idealImageUrl: string;
  phase: string;
  landmarks: Record<string, { x: number; y: number }> | null;
  notes?: string;
}

export function ComparisonPanel({
  userImageUrl,
  idealImageUrl,
  phase,
  landmarks,
  notes,
}: ComparisonPanelProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !userImageUrl) return;

    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.drawImage(img, 0, 0);
      drawPoseOverlay(ctx, landmarks, canvas.width, canvas.height);
    };
    img.src = userImageUrl;
  }, [userImageUrl, landmarks]);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <p className="text-sm font-medium capitalize">{phase} — Your swing</p>
          <div className="relative overflow-hidden rounded-xl border border-[var(--color-border)] bg-neutral-900 aspect-[3/4]">
            {userImageUrl ? (
              <canvas ref={canvasRef} className="h-full w-full object-contain" />
            ) : (
              <div className="flex h-full items-center justify-center text-[var(--color-muted)]">
                No frame available
              </div>
            )}
          </div>
        </div>
        <div className="space-y-2">
          <p className="text-sm font-medium capitalize">{phase} — Reference model</p>
          <div className="relative overflow-hidden rounded-xl border border-[var(--color-border)] bg-neutral-800 aspect-[3/4]">
            <div
              className="flex h-full flex-col items-center justify-center bg-gradient-to-b from-neutral-700 to-neutral-900 p-6 text-center"
            >
              <span className="mb-2 rounded-full bg-amber-500/20 px-3 py-1 text-xs font-medium text-amber-400">
                Reference model — placeholder
              </span>
              <p className="text-sm text-[var(--color-muted)]">
                Pro swing library coming soon. Architecture supports real model images at this slot.
              </p>
            </div>
          </div>
        </div>
      </div>
      {notes && (
        <p className="rounded-lg bg-[var(--color-accent-muted)]/40 p-3 text-sm">{notes}</p>
      )}
    </div>
  );
}
