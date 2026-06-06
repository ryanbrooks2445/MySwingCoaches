import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { createServiceClient } from "@/lib/supabase/admin";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: reportId } = await params;
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { data: profile } = await supabase
    .from("profiles")
    .select("role")
    .eq("id", user.id)
    .single();

  if (!profile || !["coach", "admin"].includes(profile.role)) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const { notes, complete } = await request.json() as { notes: string; complete: boolean };
  const serviceClient = createServiceClient();

  const { data: report } = await serviceClient
    .from("swing_reports")
    .select("video_id, user_id")
    .eq("id", reportId)
    .single();

  if (!report) {
    return NextResponse.json({ error: "Report not found" }, { status: 404 });
  }

  const { data: existing } = await serviceClient
    .from("coach_reviews")
    .select("id")
    .eq("report_id", reportId)
    .maybeSingle();

  const payload = {
    notes,
    reviewer_id: user.id,
    status: complete ? "completed" : "in_progress",
    completed_at: complete ? new Date().toISOString() : null,
  };

  if (existing) {
    await serviceClient.from("coach_reviews").update(payload).eq("id", existing.id);
  } else {
    await serviceClient.from("coach_reviews").insert({
      report_id: reportId,
      video_id: report.video_id,
      user_id: report.user_id,
      ...payload,
    });
  }

  return NextResponse.json({ success: true });
}
