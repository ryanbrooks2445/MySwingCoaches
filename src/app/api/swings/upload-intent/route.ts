import { randomUUID } from "crypto";
import { NextRequest, NextResponse } from "next/server";
import { createServiceClient } from "@/lib/supabase/admin";
import { createClient } from "@/lib/supabase/server";
import { requireGolferProfile } from "@/lib/require-golfer-profile";
import { enforceRateLimit } from "@/lib/rate-limit";
import {
  ALLOWED_VIDEO_EXTENSIONS,
  ALLOWED_VIDEO_TYPES,
  MAX_VIDEO_SIZE_BYTES,
} from "@/lib/utils";

export async function POST(request: NextRequest) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const limited = await enforceRateLimit(request, {
    scope: "upload-intent",
    identifier: user.id,
    limit: 10,
    windowSeconds: 3600,
  });
  if (limited) return limited;

  const profile = await requireGolferProfile(user.id);
  if (!profile.ok) return NextResponse.json({ error: profile.error }, { status: 403 });

  const body = await request.json();
  const originalFilename = String(body.originalFilename || "").trim();
  const mimeType = String(body.mimeType || "").trim();
  const sizeBytes = Number(body.sizeBytes);
  const swingMode = String(body.swingMode || "full_swing");
  const extension = originalFilename.split(".").pop()?.toLowerCase() || "";

  if (!["full_swing", "chipping", "putting"].includes(swingMode)) {
    return NextResponse.json({ error: "Choose a valid analysis mode." }, { status: 400 });
  }
  if (
    !ALLOWED_VIDEO_EXTENSIONS.includes(extension) ||
    !ALLOWED_VIDEO_TYPES.includes(mimeType)
  ) {
    return NextResponse.json({ error: "Upload an MP4 or MOV video." }, { status: 400 });
  }
  if (!Number.isFinite(sizeBytes) || sizeBytes <= 0 || sizeBytes > MAX_VIDEO_SIZE_BYTES) {
    return NextResponse.json({ error: "Video must be between 1 byte and 100 MB." }, { status: 400 });
  }

  const reportId = randomUUID();
  const videoId = randomUUID();
  const sessionId = randomUUID();
  const storagePath = `${user.id}/${videoId}/swing.${extension}`;
  const service = createServiceClient();

  const { error: sessionError } = await service.from("upload_sessions").insert({
    id: sessionId,
    user_id: user.id,
    report_id: reportId,
    video_id: videoId,
    storage_path: storagePath,
    original_filename: originalFilename,
    mime_type: mimeType,
    size_bytes: sizeBytes,
    swing_mode: swingMode,
  });

  if (sessionError) {
    return NextResponse.json({ error: "Could not prepare the upload." }, { status: 500 });
  }

  const { data: signed, error: signedError } = await service.storage
    .from("swing-videos")
    .createSignedUploadUrl(storagePath);

  if (signedError || !signed?.token) {
    await service.from("upload_sessions").update({ status: "failed" }).eq("id", sessionId);
    return NextResponse.json({ error: "Could not prepare secure video storage." }, { status: 500 });
  }

  return NextResponse.json({
    sessionId,
    reportId,
    path: signed.path || storagePath,
    token: signed.token,
  });
}
