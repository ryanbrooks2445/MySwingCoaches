import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

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

  return NextResponse.json({
    report,
    issues: issues ?? [],
    drills: drills ?? [],
  });
}
