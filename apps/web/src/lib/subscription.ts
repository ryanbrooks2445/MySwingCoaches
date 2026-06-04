import { createServiceClient } from "@/lib/supabase/admin";
import { PLAN_LIMITS, type CoachingContent, type Subscription } from "@/lib/types";

export async function getSubscription(userId: string): Promise<Subscription | null> {
  const supabase = createServiceClient();
  const { data } = await supabase
    .from("subscriptions")
    .select("*")
    .eq("user_id", userId)
    .single();
  return data;
}

export async function canRunAnalysis(userId: string): Promise<{ allowed: boolean; reason?: string }> {
  const sub = await getSubscription(userId);
  if (!sub) return { allowed: false, reason: "No subscription found" };

  const limit = PLAN_LIMITS[sub.plan as keyof typeof PLAN_LIMITS] ?? sub.analyses_limit;
  if (limit === -1) return { allowed: true };
  if (sub.analyses_used >= limit) {
    return { allowed: false, reason: `Analysis limit reached (${limit} on ${sub.plan} plan)` };
  }
  return { allowed: true };
}

function firstName(displayName: string | null | undefined): string | null {
  if (!displayName?.trim()) return null;
  return displayName.trim().split(/\s+/)[0] ?? null;
}

function coachingFromRow(row: {
  main_diagnosis: string | null;
  practice_plan: string | null;
  coaching_content: unknown;
}): CoachingContent | null {
  const raw = row.coaching_content as CoachingContent | null;
  if (raw?.diagnostic) return raw;
  return null;
}

export async function buildPlayerContext(userId: string): Promise<{
  playerName: string | null;
  swingNumber: number;
  historySummary: string | null;
  playerContext: string;
}> {
  const supabase = createServiceClient();

  const { data: profile } = await supabase
    .from("profiles")
    .select("display_name")
    .eq("id", userId)
    .single();

  const { count } = await supabase
    .from("swing_reports")
    .select("*", { count: "exact", head: true })
    .eq("user_id", userId)
    .eq("status", "ready");

  const completed = count ?? 0;
  const swingNumber = completed + 1;
  const playerName = firstName(profile?.display_name);

  const { data: prior } = await supabase
    .from("swing_reports")
    .select("main_diagnosis, practice_plan, coaching_content, created_at")
    .eq("user_id", userId)
    .eq("status", "ready")
    .order("created_at", { ascending: false })
    .limit(5);

  const historySummary =
    prior?.length ?
      prior
        .map((r, i) => {
          const c = coachingFromRow(r);
          const headline = c?.diagnostic.headline ?? r.main_diagnosis ?? "Unknown";
          const focus = c?.roadmap.weekly_focus ?? r.practice_plan ?? "—";
          return `Swing ${i + 1} (${new Date(r.created_at).toLocaleDateString()}): "${headline}" — focus was ${focus}`;
        })
        .join("\n")
    : null;

  const last = prior?.[0] ? coachingFromRow(prior[0]) : null;
  const lastHeadline = last?.diagnostic.headline ?? prior?.[0]?.main_diagnosis;
  const lastFocus = last?.roadmap.weekly_focus ?? prior?.[0]?.practice_plan;

  const lines: string[] = [];
  if (playerName) lines.push(`Player first name: ${playerName}`);
  lines.push(`Completed analyses before this upload: ${completed}`);
  lines.push(`This is swing #${swingNumber} in the app.`);

  if (completed === 0) {
    lines.push("First blueprint — welcome them and pick ONE clear weekly focus.");
  } else if (lastHeadline) {
    lines.push(`Last pattern we saw: "${lastHeadline}".`);
    if (lastFocus) lines.push(`Last weekly focus: "${String(lastFocus).replace(/\*\*/g, "")}".`);
    lines.push(
      "Compare this video to last time — call out if the same fault persists or if they improved."
    );
  }

  return {
    playerName,
    swingNumber,
    historySummary,
    playerContext: lines.join(" "),
  };
}

/** @deprecated use buildPlayerContext */
export async function buildHistorySummary(userId: string): Promise<string | null> {
  const ctx = await buildPlayerContext(userId);
  return ctx.historySummary;
}
