import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { createServiceClient } from "@/lib/supabase/admin";

type KeyFrameRow = {
  phase?: string;
  url?: string;
  storage_path?: string;
};

async function refreshKeyFrameUrls(report: {
  user_id: string;
  video_id: string;
  key_frame_urls?: KeyFrameRow[] | null;
}) {
  const frames = Array.isArray(report.key_frame_urls) ? report.key_frame_urls : [];
  if (!frames.length) return frames;

  const serviceClient = createServiceClient();
  return Promise.all(
    frames.map(async (frame) => {
      if (!frame.phase) return frame;
      const storagePath = frame.storage_path || `${report.user_id}/${report.video_id}/${frame.phase}.jpg`;
      const { data } = await serviceClient.storage
        .from("swing-frames")
        .createSignedUrl(storagePath, 3600);

      return {
        ...frame,
        storage_path: storagePath,
        url: data?.signedUrl || frame.url || null,
      };
    })
  );
}

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: reportId } = await params;
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { data: report, error } = await supabase
    .from("swing_reports")
    .select("*")
    .eq("id", reportId)
    .eq("user_id", user.id)
    .single();

  if (error || !report) {
    return NextResponse.json({ error: "Report not found" }, { status: 404 });
  }

  const { data: issues } = await supabase
    .from("swing_issues")
    .select("*")
    .eq("report_id", reportId)
    .order("sort_order");

  const { data: drills } = await supabase
    .from("drill_recommendations")
    .select("*")
    .eq("report_id", reportId)
    .order("sort_order");

  const refreshedFrames = await refreshKeyFrameUrls(report);

  return NextResponse.json({
    report: {
      ...report,
      key_frame_urls: refreshedFrames,
    },
    issues: issues ?? [],
    drills: drills ?? [],
  });
}
