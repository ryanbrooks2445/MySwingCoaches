import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { createServiceClient } from "@/lib/supabase/admin";
import { buildHistorySummary } from "@/lib/subscription";

export async function POST(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: reportId } = await params;
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const serviceClient = createServiceClient();
  const { data: report, error: reportError } = await serviceClient
    .from("swing_reports")
    .select("*, swing_videos(*)")
    .eq("id", reportId)
    .eq("user_id", user.id)
    .single();

  if (reportError || !report) {
    return NextResponse.json({ error: "Report not found" }, { status: 404 });
  }

  const { data: profile } = await serviceClient
    .from("profiles")
    .select("handedness, skill_level, camera_angle_pref")
    .eq("id", user.id)
    .single();

  const video = report.swing_videos as {
    id: string;
    storage_path: string;
    camera_angle: string;
  };

  const { data: signed, error: signError } = await serviceClient.storage
    .from("swing-videos")
    .createSignedUrl(video.storage_path, 3600);

  if (signError || !signed?.signedUrl) {
    return NextResponse.json({ error: "Could not sign video URL" }, { status: 500 });
  }

  const profileData = profile;

  const historySummary = await buildHistorySummary(user.id);

  const analysisUrl = process.env.ANALYSIS_SERVICE_URL || "http://localhost:8001";
  const secret = process.env.ANALYSIS_SERVICE_SECRET || "";

  try {
    const response = await fetch(`${analysisUrl}/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Analysis-Secret": secret,
      },
      body: JSON.stringify({
        analysis_id: reportId,
        video_id: video.id,
        user_id: user.id,
        video_url: signed.signedUrl,
        handedness: profileData?.handedness ?? "right",
        skill_level: profileData?.skill_level ?? "intermediate",
        camera_angle: video.camera_angle || profileData?.camera_angle_pref || "unknown",
        history_summary: historySummary,
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      await serviceClient.from("swing_reports").update({
        status: "failed",
        error_message: errText.slice(0, 500),
      }).eq("id", reportId);
      return NextResponse.json({ error: "Analysis service failed" }, { status: 502 });
    }

    const result = await response.json();
    return NextResponse.json({ success: true, report: result });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Analysis request failed";
    await serviceClient.from("swing_reports").update({
      status: "failed",
      error_message: message,
    }).eq("id", reportId);
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
