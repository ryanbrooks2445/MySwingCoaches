import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { createServiceClient } from "@/lib/supabase/admin";
import { requireGolferProfile } from "@/lib/require-golfer-profile";
import { canRunAnalysis } from "@/lib/subscription";
import { logTrace } from "@/lib/trace";
import { ALLOWED_VIDEO_TYPES, MAX_VIDEO_SIZE_BYTES } from "@/lib/utils";
import { randomUUID } from "crypto";

function isAllowedVideo(fileName: string, mimeType: string): boolean {
  const ext = fileName.split(".").pop()?.toLowerCase();
  if (ext === "mp4" || ext === "mov") return true;
  return ALLOWED_VIDEO_TYPES.includes(mimeType);
}

function guessMimeType(file: File): string {
  if (file.type) return file.type;
  const ext = file.name.split(".").pop()?.toLowerCase();
  if (ext === "mov") return "video/quicktime";
  return "video/mp4";
}

export async function POST(request: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const profileCheck = await requireGolferProfile(user.id);
  if (!profileCheck.ok) {
    return NextResponse.json({ error: profileCheck.error }, { status: 403 });
  }

  const quota = await canRunAnalysis(user.id);
  if (!quota.allowed) {
    return NextResponse.json({ error: quota.reason }, { status: 403 });
  }

  const formData = await request.formData();
  const file = formData.get("file") as File | null;
  const swingMode = String(formData.get("swingMode") || "full_swing");
  const allowedModes = ["full_swing", "chipping", "putting"];

  if (!file) {
    return NextResponse.json({ error: "No file provided" }, { status: 400 });
  }

  if (!allowedModes.includes(swingMode)) {
    return NextResponse.json({ error: "Invalid swing mode" }, { status: 400 });
  }

  const mimeType = guessMimeType(file);
  if (!isAllowedVideo(file.name, mimeType)) {
    return NextResponse.json({ error: "Only MP4 and MOV files are supported" }, { status: 400 });
  }

  if (file.size > MAX_VIDEO_SIZE_BYTES) {
    return NextResponse.json({ error: "File must be under 100MB" }, { status: 400 });
  }

  const traceId = randomUUID();
  const videoId = randomUUID();
  const reportId = randomUUID();
  const ext = file.name.split(".").pop() || "mp4";
  const storagePath = `${user.id}/${videoId}/swing.${ext}`;

  logTrace("upload_started", {
    trace_id: traceId,
    user_id: user.id,
    report_id: reportId,
    status: "started",
  });

  const serviceClient = createServiceClient();
  const buffer = Buffer.from(await file.arrayBuffer());

  const { error: uploadError } = await serviceClient.storage
    .from("swing-videos")
    .upload(storagePath, buffer, {
      contentType: mimeType,
      upsert: false,
    });

  if (uploadError) {
    logTrace("upload_complete", {
      trace_id: traceId,
      user_id: user.id,
      report_id: reportId,
      status: "error",
      error: uploadError.message,
    });
    return NextResponse.json({ error: uploadError.message }, { status: 500 });
  }

  logTrace("upload_complete", {
    trace_id: traceId,
    user_id: user.id,
    report_id: reportId,
    status: "ok",
    storage_path: storagePath,
  });

  const { error: videoError } = await serviceClient.from("swing_videos").insert({
    id: videoId,
    user_id: user.id,
    storage_path: storagePath,
    original_filename: file.name,
    mime_type: mimeType,
    size_bytes: file.size,
    swing_mode: swingMode,
    status: "processing",
  });

  if (videoError) {
    return NextResponse.json({ error: videoError.message }, { status: 500 });
  }

  const { error: reportError } = await serviceClient.from("swing_reports").insert({
    id: reportId,
    user_id: user.id,
    video_id: videoId,
    swing_mode: swingMode,
    status: "processing",
  });

  if (reportError) {
    logTrace("db_row_created", {
      trace_id: traceId,
      user_id: user.id,
      report_id: reportId,
      status: "error",
      error: reportError.message,
    });
    return NextResponse.json({ error: reportError.message }, { status: 500 });
  }

  logTrace("db_row_created", {
    trace_id: traceId,
    user_id: user.id,
    report_id: reportId,
    status: "processing",
    video_id: videoId,
  });

  return NextResponse.json({
    videoId,
    reportId,
    storagePath,
    traceId,
  });
}
