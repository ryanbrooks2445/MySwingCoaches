import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { createServiceClient } from "@/lib/supabase/admin";
import { requireGolferProfile } from "@/lib/require-golfer-profile";
import { canRunAnalysis } from "@/lib/subscription";
import { ALLOWED_VIDEO_TYPES, MAX_VIDEO_SIZE_BYTES } from "@/lib/utils";

function isAllowedVideo(fileName: string, mimeType: string): boolean {
  const ext = fileName.split(".").pop()?.toLowerCase();
  if (ext === "mp4" || ext === "mov") return true;
  return ALLOWED_VIDEO_TYPES.includes(mimeType);
}

function cleanText(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const cleaned = value.trim();
  return cleaned ? cleaned.slice(0, 300) : null;
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

  const body = await request.json();
  const {
    videoId,
    reportId,
    storagePath,
    originalFilename,
    mimeType,
    sizeBytes,
    swingMode = "full_swing",
    intake: rawIntake = {},
  } = body;
  const allowedCameraAngles = ["face-on", "down-the-line", "unknown"];
  const rawCameraAngle = cleanText(rawIntake?.cameraAngle) || "unknown";
  const intake = {
    ballFlight: cleanText(rawIntake?.ballFlight),
    userGoal: cleanText(rawIntake?.userGoal),
    clubUsed: cleanText(rawIntake?.clubUsed),
    practiceAvailability: cleanText(rawIntake?.practiceAvailability),
    handicap: cleanText(rawIntake?.handicap),
    cameraAngle: allowedCameraAngles.includes(rawCameraAngle) ? rawCameraAngle : "unknown",
    handedness: cleanText(rawIntake?.handedness),
  };

  const allowedModes = ["full_swing", "chipping", "putting"];
  if (!allowedModes.includes(swingMode)) {
    return NextResponse.json({ error: "Invalid swing mode" }, { status: 400 });
  }

  if (!videoId || !reportId || !storagePath || !originalFilename || !sizeBytes) {
    return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
  }

  if (!storagePath.startsWith(`${user.id}/`)) {
    return NextResponse.json({ error: "Invalid storage path" }, { status: 400 });
  }

  if (!isAllowedVideo(originalFilename, mimeType || "")) {
    return NextResponse.json({ error: "Only MP4 and MOV files are supported" }, { status: 400 });
  }

  if (sizeBytes > MAX_VIDEO_SIZE_BYTES) {
    return NextResponse.json({ error: "File must be under 100MB" }, { status: 400 });
  }

  const serviceClient = createServiceClient();

  // Verify file exists in storage
  const folder = storagePath.split("/").slice(0, -1).join("/");
  const fileName = storagePath.split("/").pop()!;
  const { data: listed, error: listError } = await serviceClient.storage
    .from("swing-videos")
    .list(folder, { search: fileName });

  if (listError || !listed?.length) {
    return NextResponse.json(
      { error: "Video not found in storage. Upload may have failed." },
      { status: 400 }
    );
  }

  const { error: videoError } = await serviceClient.from("swing_videos").insert({
    id: videoId,
    user_id: user.id,
    storage_path: storagePath,
    original_filename: originalFilename,
    mime_type: mimeType || "video/mp4",
    size_bytes: sizeBytes,
    swing_mode: swingMode,
    camera_angle: intake.cameraAngle,
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
    pose_landmarks: { intake },
    status: "processing",
  });

  if (reportError) {
    return NextResponse.json({ error: reportError.message }, { status: 500 });
  }

  return NextResponse.json({ videoId, reportId, storagePath });
}
