import { redirect } from "next/navigation";
import type React from "react";
import { AppNav } from "@/components/AppNav";
import { Card } from "@/components/ui/Card";
import { createServiceClient } from "@/lib/supabase/admin";
import { createClient } from "@/lib/supabase/server";
import type { CoachingContent, SwingReport, SwingVideo } from "@/lib/types";

type AuditReport = SwingReport & {
  swing_videos?: SwingVideo | null;
};

type DebugPayload = {
  gemini_input?: Record<string, unknown>;
  gemini_raw_response?: unknown;
  frontend_display_source?: unknown;
  processing_time_ms?: number;
  processing_time_sec?: number;
  camera_angle_detection?: string;
  confidence_scores?: unknown;
  hybrid_vision_evidence?: Record<string, unknown>;
};

function JsonBlock({ value }: { value: unknown }) {
  return (
    <pre className="max-h-[520px] overflow-auto rounded-lg border border-[var(--color-border)] bg-black/80 p-4 text-xs leading-relaxed text-white">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

function getDebug(raw: Record<string, unknown> | null): DebugPayload | null {
  const debug = raw?._debug;
  return debug && typeof debug === "object" ? (debug as DebugPayload) : null;
}

function getInput(debug: DebugPayload | null, raw: Record<string, unknown> | null) {
  return debug?.gemini_input ?? (raw?._meta as Record<string, unknown> | undefined) ?? {};
}

function getFrames(input: Record<string, unknown>, report: AuditReport | null) {
  const debugFrames = Array.isArray(input.frames) ? input.frames : [];
  const frameUrls = report?.key_frame_urls ?? [];
  return frameUrls.map((frame, index) => {
    const meta = debugFrames.find(
      (item) =>
        item &&
        typeof item === "object" &&
        "label" in item &&
        (item as { label?: string }).label === frame.phase
    ) as Record<string, unknown> | undefined;

    return {
      phase: frame.phase,
      url: frame.url,
      order: index + 1,
      timestamp: meta?.timestamp_sec,
      frameIndex: meta?.frame_index,
      confidence: frame.confidence,
    };
  });
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-muted)]">{label}</p>
      <div className="mt-1 text-sm text-[var(--color-foreground)]">{value}</div>
    </div>
  );
}

function stringify(value: unknown) {
  if (value === null || value === undefined || value === "") return "Not available";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value);
}

export default async function GeminiDebugPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  if (process.env.NODE_ENV === "production" && process.env.ENABLE_GEMINI_DEBUG_PAGE !== "true") {
    redirect("/");
  }

  const { id } = await params;
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const serviceClient = createServiceClient();
  const { data } = await serviceClient
    .from("swing_reports")
    .select("*, swing_videos(*)")
    .eq("id", id)
    .eq("user_id", user.id)
    .single();

  const report = data as AuditReport | null;
  const debug = getDebug(report?.gemini_raw ?? null);
  const input = getInput(debug, report?.gemini_raw ?? null);
  const frames = getFrames(input, report);
  const coaching = report?.coaching_content as CoachingContent | null | undefined;
  const metricPayload = report?.pose_landmarks ?? {};
  const cameraAngle =
    debug?.camera_angle_detection ??
    input.camera_angle_detected ??
    (metricPayload as { camera_angle?: string }).camera_angle ??
    report?.swing_videos?.camera_angle ??
    "unknown";
  const processingTime =
    debug?.processing_time_sec ??
    (typeof debug?.processing_time_ms === "number" ? Math.round(debug.processing_time_ms / 10) / 100 : null);
  let videoUrl: string | null = null;

  if (report?.swing_videos?.storage_path) {
    const { data: signed } = await serviceClient.storage
      .from("swing-videos")
      .createSignedUrl(report.swing_videos.storage_path, 3600);
    videoUrl = signed?.signedUrl ?? null;
  }

  return (
    <div className="min-h-screen">
      <AppNav />
      <main className="mx-auto max-w-5xl px-4 py-8">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-muted)]">
            Developer audit
          </p>
          <h1 className="mt-1 text-2xl font-semibold">Analysis audit</h1>
          <p className="mt-2 text-sm text-[var(--color-muted)]">
            Report {id}
          </p>
        </div>

        {!report ? (
          <Card className="mt-6">
            <p>Report not found.</p>
          </Card>
        ) : (
          <div className="mt-6 space-y-6">
            <Card>
              <h2 className="text-lg font-semibold">Original uploaded video</h2>
              <div className="mt-4 overflow-hidden rounded-lg border border-[var(--color-border)] bg-black">
                {videoUrl ? (
                  <video src={videoUrl} controls className="max-h-[640px] w-full" />
                ) : (
                  <div className="flex min-h-[260px] items-center justify-center text-sm text-white/70">
                    Video URL unavailable
                  </div>
                )}
              </div>
              <div className="mt-4 grid gap-4 md:grid-cols-3">
                <Field label="Original filename" value={report.swing_videos?.original_filename ?? "Unknown"} />
                <Field label="Mime type" value={report.swing_videos?.mime_type ?? "Unknown"} />
                <Field label="Storage path" value={report.swing_videos?.storage_path ?? "Unknown"} />
              </div>
            </Card>

            <Card>
              <h2 className="text-lg font-semibold">Audit summary</h2>
              <div className="mt-4 grid gap-4 md:grid-cols-4">
                <Field label="Model" value={stringify(input.model_name)} />
                <Field label="Full video sent" value={stringify(input.full_video_sent)} />
                <Field label="Frame count" value={stringify(input.frame_count ?? frames.length)} />
                <Field label="Processing time" value={processingTime ? `${processingTime}s` : "Not available"} />
                <Field label="Camera angle detection" value={stringify(cameraAngle)} />
                <Field label="Video attached" value={stringify(input.video_attached)} />
                <Field label="Report status" value={report.status} />
                <Field label="AI narrative" value={report.ai_narrative_available ? "Available" : "Unavailable"} />
              </div>
            </Card>

            <Card>
              <h2 className="text-lg font-semibold">Hybrid vision evidence</h2>
              <div className="mt-4 grid gap-4 md:grid-cols-4">
                <Field
                  label="Primary truth"
                  value={stringify(debug?.hybrid_vision_evidence?.primary_truth)}
                />
                <Field
                  label="Fusion confidence"
                  value={stringify(debug?.hybrid_vision_evidence?.fusion_confidence)}
                />
                <Field
                  label="Body tracker"
                  value={stringify(
                    (debug?.hybrid_vision_evidence?.body_tracking as { provider?: string } | undefined)?.provider
                  )}
                />
                <Field
                  label="Club tracker"
                  value={stringify(
                    (debug?.hybrid_vision_evidence?.club_tracking as { provider?: string } | undefined)?.provider
                  )}
                />
              </div>
              <div className="mt-4">
                <JsonBlock value={debug?.hybrid_vision_evidence ?? null} />
              </div>
            </Card>

            <Card>
              <h2 className="text-lg font-semibold">Extracted key frames in order</h2>
              <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {frames.map((frame) => (
                  <div key={frame.phase} className="overflow-hidden rounded-lg border border-[var(--color-border)]">
                    <div className="aspect-[3/4] bg-black">
                      {frame.url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={frame.url} alt={frame.phase} className="h-full w-full object-contain" />
                      ) : (
                        <div className="flex h-full items-center justify-center text-sm text-white/70">
                          No frame
                        </div>
                      )}
                    </div>
                    <div className="space-y-1 p-3 text-sm">
                      <p className="font-medium">
                        {frame.order}. {frame.phase.replaceAll("_", " ")}
                      </p>
                      <p className="text-xs text-[var(--color-muted)]">
                        timestamp: {stringify(frame.timestamp)}s · frame: {stringify(frame.frameIndex)}
                      </p>
                      <p className="text-xs text-[var(--color-muted)]">
                        confidence: {stringify(frame.confidence)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card>
              <h2 className="text-lg font-semibold">What Gemini received</h2>
              <div className="mt-4 space-y-4">
                <div>
                  <h3 className="text-sm font-semibold">Raw Gemini prompt</h3>
                  <JsonBlock value={input.prompt ?? null} />
                </div>
                <div>
                  <h3 className="text-sm font-semibold">Input payload summary</h3>
                  <JsonBlock value={input} />
                </div>
              </div>
            </Card>

            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <h2 className="text-lg font-semibold">What Gemini returned</h2>
                <div className="mt-4">
                  <JsonBlock value={debug?.gemini_raw_response ?? report.gemini_raw} />
                </div>
              </Card>

              <Card>
                <h2 className="text-lg font-semibold">What the frontend displayed</h2>
                <div className="mt-4">
                  <JsonBlock
                    value={{
                      title: coaching?.feel_blueprint?.headline ?? report.main_diagnosis,
                      improvement_engine: coaching?.improvement_engine ?? null,
                      pga_coach_analysis: coaching?.pga_coach_analysis ?? null,
                      diagnosis_engine: coaching?.diagnosis_engine ?? null,
                      feel_blueprint: coaching?.feel_blueprint ?? null,
                      blueprint: coaching?.blueprint ?? null,
                      roadmap: coaching?.roadmap ?? null,
                      next_upload_focus: coaching?.next_upload_focus ?? report.next_upload_focus,
                    }}
                  />
                </div>
              </Card>
            </div>

            <Card>
              <h2 className="text-lg font-semibold">Confidence scores</h2>
              <div className="mt-4">
                <JsonBlock
                  value={
                    debug?.confidence_scores ?? {
                      diagnosis_evidence: coaching?.diagnosis_engine?.evidence ?? [],
                      metric_payload: metricPayload,
                    }
                  }
                />
              </div>
            </Card>

            <Card>
              <h2 className="text-lg font-semibold">Final stored report</h2>
              <div className="mt-4">
                <JsonBlock value={report.coaching_content} />
              </div>
            </Card>
          </div>
        )}
      </main>
    </div>
  );
}
