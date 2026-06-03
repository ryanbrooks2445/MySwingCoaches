import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { createServiceClient } from "@/lib/supabase/admin";
import { canRunAnalysis } from "@/lib/subscription";
import { ALLOWED_VIDEO_TYPES, MAX_VIDEO_SIZE_BYTES } from "@/lib/utils";
import { randomUUID } from "crypto";

export async function POST(request: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const quota = await canRunAnalysis(user.id);
  if (!quota.allowed) {
    return NextResponse.json({ error: quota.reason }, { status: 403 });
  }

  const formData = await request.formData();
  const file = formData.get("file") as File | null;
  const handedness = (formData.get("handedness") as string) || "right";
  const skillLevel = (formData.get("skillLevel") as string) || "intermediate";
  const cameraAngle = (formData.get("cameraAngle") as string) || "unknown";

  if (!file) {
    return NextResponse.json({ error: "No file provided" }, { status: 400 });
  }

  if (!ALLOWED_VIDEO_TYPES.includes(file.type)) {
    return NextResponse.json({ error: "Only MP4 and MOV files are supported" }, { status: 400 });
  }

  if (file.size > MAX_VIDEO_SIZE_BYTES) {
    return NextResponse.json({ error: "File must be under 100MB" }, { status: 400 });
  }

  const videoId = randomUUID();
  const reportId = randomUUID();
  const ext = file.name.split(".").pop() || "mp4";
  const storagePath = `${user.id}/${videoId}/swing.${ext}`;

  const serviceClient = createServiceClient();
  const buffer = Buffer.from(await file.arrayBuffer());

  const { error: uploadError } = await serviceClient.storage
    .from("swing-videos")
    .upload(storagePath, buffer, {
      contentType: file.type,
      upsert: false,
    });

  if (uploadError) {
    return NextResponse.json({ error: uploadError.message }, { status: 500 });
  }

  const { error: videoError } = await serviceClient.from("swing_videos").insert({
    id: videoId,
    user_id: user.id,
    storage_path: storagePath,
    original_filename: file.name,
    mime_type: file.type,
    size_bytes: file.size,
    status: "processing",
    camera_angle: cameraAngle,
  });

  if (videoError) {
    return NextResponse.json({ error: videoError.message }, { status: 500 });
  }

  await serviceClient.from("profiles").update({
    handedness,
    skill_level: skillLevel,
    camera_angle_pref: cameraAngle,
  }).eq("id", user.id);

  const { error: reportError } = await serviceClient.from("swing_reports").insert({
    id: reportId,
    user_id: user.id,
    video_id: videoId,
    status: "processing",
  });

  if (reportError) {
    return NextResponse.json({ error: reportError.message }, { status: 500 });
  }

  return NextResponse.json({
    videoId,
    reportId,
    storagePath,
  });
}
