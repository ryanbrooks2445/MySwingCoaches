import type { SupabaseClient } from "@supabase/supabase-js";

export async function deleteSwingByReportId(
  serviceClient: SupabaseClient,
  userId: string,
  reportId: string
): Promise<{ ok: true } | { ok: false; error: string }> {
  const { data: report, error: reportError } = await serviceClient
    .from("swing_reports")
    .select("id, video_id, user_id")
    .eq("id", reportId)
    .eq("user_id", userId)
    .single();

  if (reportError || !report) {
    return { ok: false, error: "Swing not found" };
  }

  const { data: video, error: videoError } = await serviceClient
    .from("swing_videos")
    .select("id, storage_path")
    .eq("id", report.video_id)
    .eq("user_id", userId)
    .single();

  if (videoError || !video) {
    return { ok: false, error: "Video not found" };
  }

  await serviceClient.from("coach_reviews").delete().eq("report_id", reportId);
  await serviceClient.from("swing_issues").delete().eq("report_id", reportId);
  await serviceClient.from("drill_recommendations").delete().eq("report_id", reportId);

  const { error: deleteReportError } = await serviceClient
    .from("swing_reports")
    .delete()
    .eq("id", reportId)
    .eq("user_id", userId);

  if (deleteReportError) {
    return { ok: false, error: deleteReportError.message };
  }

  await serviceClient.from("swing_videos").delete().eq("id", video.id).eq("user_id", userId);

  if (video.storage_path) {
    await serviceClient.storage.from("swing-videos").remove([video.storage_path]);
  }

  const framePrefix = `${userId}/${video.id}`;
  const { data: frameFiles } = await serviceClient.storage
    .from("swing-frames")
    .list(framePrefix);

  if (frameFiles?.length) {
    const framePaths = frameFiles.map((f) => `${framePrefix}/${f.name}`);
    await serviceClient.storage.from("swing-frames").remove(framePaths);
  }

  return { ok: true };
}

export async function deleteAllSwingsForUser(
  serviceClient: SupabaseClient,
  userId: string
): Promise<{ deleted: number; errors: string[] }> {
  const { data: reports } = await serviceClient
    .from("swing_reports")
    .select("id")
    .eq("user_id", userId);

  if (!reports?.length) {
    return { deleted: 0, errors: [] };
  }

  const errors: string[] = [];
  let deleted = 0;

  for (const row of reports) {
    const result = await deleteSwingByReportId(serviceClient, userId, row.id);
    if (result.ok) deleted += 1;
    else errors.push(result.error);
  }

  return { deleted, errors };
}
