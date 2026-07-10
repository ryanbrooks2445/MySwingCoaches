import { NextRequest, NextResponse } from "next/server";
import { createServiceClient } from "@/lib/supabase/admin";
import { enforceRateLimit } from "@/lib/rate-limit";
import { createClient } from "@/lib/supabase/server";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: reportId } = await params;
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const limited = await enforceRateLimit(request, {
    scope: "analysis-retry",
    identifier: `${user.id}:${reportId}`,
    limit: 3,
    windowSeconds: 86400,
  });
  if (limited) return limited;

  const service = createServiceClient();
  const { data: report } = await service
    .from("swing_reports")
    .select("id,status,source_video_deleted_at")
    .eq("id", reportId)
    .eq("user_id", user.id)
    .single();
  if (!report) return NextResponse.json({ error: "Report not found." }, { status: 404 });
  if (report.source_video_deleted_at) {
    return NextResponse.json(
      { error: "The source video has expired. Upload a new swing to run another analysis." },
      { status: 410 }
    );
  }
  if (report.status === "awaiting_payment") {
    const { data: started, error } = await service.rpc("service_start_queued_analysis", {
      p_report_id: reportId,
      p_user_id: user.id,
    });
    if (error || !started) {
      return NextResponse.json(
        { error: "Payment is required before analysis can start.", needsCheckout: true },
        { status: 402 }
      );
    }
    return NextResponse.json({ queued: true });
  }
  if (report.status !== "failed") {
    return NextResponse.json({ queued: report.status === "processing" });
  }

  const { data: queued, error } = await service.rpc("service_requeue_analysis", {
    p_report_id: reportId,
    p_user_id: user.id,
  });
  if (error || !queued) {
    return NextResponse.json(
      { error: "A new analysis credit is required before retrying this report." },
      { status: 402 }
    );
  }
  return NextResponse.json({ queued: true });
}
