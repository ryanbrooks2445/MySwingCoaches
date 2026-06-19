import { NextRequest, NextResponse } from "next/server";
import { createServiceClient } from "@/lib/supabase/admin";
import { createClient } from "@/lib/supabase/server";

export async function POST(request: NextRequest) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { sessionId } = await request.json();
  if (!sessionId) {
    return NextResponse.json({ error: "Upload session is required." }, { status: 400 });
  }

  const service = createServiceClient();
  const { data: session, error: sessionError } = await service
    .from("upload_sessions")
    .select("id, report_id, storage_path, status")
    .eq("id", sessionId)
    .eq("user_id", user.id)
    .single();

  if (sessionError || !session) {
    return NextResponse.json({ error: "Upload session not found." }, { status: 404 });
  }

  if (session.status === "registered") {
    return NextResponse.json(
      { error: "This upload has already been queued for analysis." },
      { status: 409 }
    );
  }

  await service.storage.from("swing-videos").remove([session.storage_path]);
  await service.from("upload_sessions").update({ status: "failed" }).eq("id", session.id);
  await service.rpc("service_restore_analysis_credit", {
    p_report_id: session.report_id,
    p_reason: "upload_cancelled",
  });

  return NextResponse.json({ restored: true });
}
