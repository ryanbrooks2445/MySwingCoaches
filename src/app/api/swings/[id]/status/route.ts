import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { createServiceClient } from "@/lib/supabase/admin";
import { compareToPriorReport } from "@/lib/phase-frames";
import type { SwingReport } from "@/lib/types";

async function refreshFrameUrls(
  service: ReturnType<typeof createServiceClient>,
  frames: SwingReport["key_frame_urls"]
) {
  return Promise.all(
    (frames ?? []).map(async (frame) => {
      if (!frame.storage_path) return frame;
      const { data } = await service.storage
        .from("swing-frames")
        .createSignedUrl(frame.storage_path, 3600);
      return { ...frame, url: data?.signedUrl ?? undefined };
    })
  );
}

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: reportId } = await params;
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
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
  report.key_frame_urls = await refreshFrameUrls(service, report.key_frame_urls);

  const { data: priorReports } = await supabase
    .from("swing_reports")
    .select("*")
    .eq("user_id", user.id)
    .eq("swing_mode", report.swing_mode ?? "full_swing")
    .eq("status", "ready")
    .neq("id", reportId)
    .order("created_at", { ascending: false })
    .limit(1);

  const prior = (priorReports?.[0] as SwingReport | undefined) ?? null;
  if (prior) {
    prior.key_frame_urls = await refreshFrameUrls(service, prior.key_frame_urls);
  }

  const comparison = compareToPriorReport(report as SwingReport, prior);

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

  const blueprint = report.coaching_content?.blueprint;
  const drillStep = blueprint?.steps?.find(
    (s: { step_type?: string; video_url?: string | null }) =>
      s.step_type === "constraint_drill" && s.video_url
  );

  return NextResponse.json({
    report,
    comparison,
    drillVideoUrl: drillStep?.video_url ?? null,
    drillVideoTitle: drillStep?.video_title ?? null,
    issues: issues ?? [],
    drills: drills ?? [],
  });
}
