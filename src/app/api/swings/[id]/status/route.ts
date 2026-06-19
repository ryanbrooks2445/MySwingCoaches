import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { createServiceClient } from "@/lib/supabase/admin";

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

  const service = createServiceClient();
  const refreshedFrames = await Promise.all(
    ((report.key_frame_urls ?? []) as Array<{
      phase: string;
      storage_path?: string;
      url?: string;
    }>).map(async (frame) => {
      if (!frame.storage_path) return frame;
      const { data } = await service.storage
        .from("swing-frames")
        .createSignedUrl(frame.storage_path, 3600);
      return { ...frame, url: data?.signedUrl ?? undefined };
    })
  );
  report.key_frame_urls = refreshedFrames;

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

  return NextResponse.json({
    report,
    issues: issues ?? [],
    drills: drills ?? [],
  });
}
