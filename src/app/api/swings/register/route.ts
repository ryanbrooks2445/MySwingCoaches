import { NextRequest, NextResponse } from "next/server";
import { createServiceClient } from "@/lib/supabase/admin";
import { createClient } from "@/lib/supabase/server";
import { enforceRateLimit } from "@/lib/rate-limit";

export async function POST(request: NextRequest) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const limited = await enforceRateLimit(request, {
    scope: "upload-register",
    identifier: user.id,
    limit: 10,
    windowSeconds: 3600,
  });
  if (limited) return limited;

  const { sessionId } = await request.json();
  if (!sessionId) {
    return NextResponse.json({ error: "Upload session is required." }, { status: 400 });
  }

  const service = createServiceClient();
  const { data: session, error: sessionError } = await service
    .from("upload_sessions")
    .select("*")
    .eq("id", sessionId)
    .eq("user_id", user.id)
    .single();
  if (sessionError || !session) {
    return NextResponse.json({ error: "Upload session not found." }, { status: 404 });
  }

  const folder = session.storage_path.split("/").slice(0, -1).join("/");
  const fileName = session.storage_path.split("/").pop()!;
  const { data: listed, error: listError } = await service.storage
    .from("swing-videos")
    .list(folder, { search: fileName });
  const uploaded = listed?.find((item) => item.name === fileName);
  const uploadedSize = Number(uploaded?.metadata?.size ?? 0);

  if (
    listError ||
    !uploaded ||
    uploadedSize <= 0 ||
    uploadedSize !== Number(session.size_bytes)
  ) {
    await service.storage.from("swing-videos").remove([session.storage_path]);
    await service.from("upload_sessions").update({ status: "failed" }).eq("id", sessionId);
    await service.rpc("service_restore_analysis_credit", {
      p_report_id: session.report_id,
      p_reason: "upload_verification_failed",
    });
    return NextResponse.json(
      { error: "The uploaded video could not be verified. Your credit was restored." },
      { status: 400 }
    );
  }

  await service.from("upload_sessions").update({ status: "uploaded" }).eq("id", sessionId);
  const { data: reportId, error: registerError } = await service.rpc(
    "service_register_uploaded_swing",
    {
      p_session_id: sessionId,
      p_user_id: user.id,
    }
  );

  if (registerError || !reportId) {
    await service.storage.from("swing-videos").remove([session.storage_path]);
    await service.from("upload_sessions").update({ status: "failed" }).eq("id", sessionId);
    await service.rpc("service_restore_analysis_credit", {
      p_report_id: session.report_id,
      p_reason: "registration_failed",
    });
    return NextResponse.json(
      { error: "We could not queue this analysis. Your credit was restored." },
      { status: 500 }
    );
  }

  return NextResponse.json({ reportId });
}
