import { createServiceClient } from "@/lib/supabase/admin";
import { PRICE_PER_ANALYSIS_DISPLAY } from "@/lib/pricing";
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

export function analysisCreditsRemaining(sub: Subscription): number | "unlimited" {
  const planLimit = PLAN_LIMITS[sub.plan as keyof typeof PLAN_LIMITS];
  const limit = planLimit === -1 ? -1 : sub.analyses_limit;
  if (limit === -1) return "unlimited";
  return Math.max(0, limit - sub.analyses_used);
}

export async function canRunAnalysis(userId: string): Promise<{ allowed: boolean; reason?: string }> {
  const sub = await getSubscription(userId);
  if (!sub) return { allowed: false, reason: "No account found" };

  const remaining = analysisCreditsRemaining(sub);
  if (remaining === "unlimited") return { allowed: true };
  if (remaining < 1) {
    return {
      allowed: false,
      reason: `No analyses left. Purchase one for ${PRICE_PER_ANALYSIS_DISPLAY} on the pricing page.`,
    };
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
  if (raw?.feel_blueprint || raw?.diagnostic) return raw;
  return null;
}

export async function buildPlayerContext(
  userId: string,
  swingMode?: string
): Promise<{
  playerName: string | null;
  swingNumber: number;
  historySummary: string | null;
  playerContext: string;
  playerAge: number | null;
  yearsPlaying: number | null;
  physicalLimitations: string | null;
  handedness: string | null;
  skillLevel: string | null;
  cameraAnglePref: string | null;
  priorProgress: Record<string, unknown> | null;
}> {
  const supabase = createServiceClient();

  const { data: profile } = await supabase
    .from("profiles")
    .select("display_name, age, years_playing, physical_limitations, handedness, skill_level, camera_angle_pref")
    .eq("id", userId)
    .single();

  let countQuery = supabase
    .from("swing_reports")
    .select("*", { count: "exact", head: true })
    .eq("user_id", userId)
    .eq("status", "ready");
  if (swingMode) countQuery = countQuery.eq("swing_mode", swingMode);
  const { count } = await countQuery;

  const completed = count ?? 0;
  const swingNumber = completed + 1;
  const playerName = firstName(profile?.display_name);

  let priorQuery = supabase
    .from("swing_reports")
    .select("main_diagnosis, practice_plan, coaching_content, created_at, swing_mode")
    .eq("user_id", userId)
    .eq("status", "ready")
    .order("created_at", { ascending: false })
    .limit(5);
  if (swingMode) priorQuery = priorQuery.eq("swing_mode", swingMode);
  const { data: prior } = await priorQuery;

  const historySummary =
    prior?.length ?
      prior
        .map((r, i) => {
          const c = coachingFromRow(r);
          const headline =
            c?.feel_blueprint?.headline ?? c?.diagnostic?.headline ?? r.main_diagnosis ?? "Unknown";
          const focus = c?.roadmap.weekly_focus ?? r.practice_plan ?? "—";
          return `Swing ${i + 1} (${new Date(r.created_at).toLocaleDateString()}): "${headline}" — focus was ${focus}`;
        })
        .join("\n")
    : null;

  const last = prior?.[0] ? coachingFromRow(prior[0]) : null;
  const priorProgress = last?.improvement_engine?.progress_score
    ? {
        progress_score: last.improvement_engine.progress_score,
        main_diagnosis: last.improvement_engine.main_diagnosis,
        benchmark: last.improvement_engine.improvement_benchmark,
      }
    : null;
  const lastHeadline =
    last?.feel_blueprint?.headline ?? last?.diagnostic?.headline ?? prior?.[0]?.main_diagnosis;
  const lastFocus = last?.roadmap.weekly_focus ?? prior?.[0]?.practice_plan;

  const lines: string[] = [];
  if (playerName) lines.push(`Player first name: ${playerName}`);
  if (swingMode) lines.push(`Mode for this upload: ${swingMode}.`);
  lines.push(`Completed ${swingMode ?? "total"} analyses before this upload: ${completed}`);
  lines.push(`This is their #${swingNumber} analysis in this mode.`);

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
    playerAge: profile?.age ?? null,
    yearsPlaying: profile?.years_playing ?? null,
    physicalLimitations: profile?.physical_limitations ?? null,
    handedness: profile?.handedness ?? null,
    skillLevel: profile?.skill_level ?? null,
    cameraAnglePref: profile?.camera_angle_pref ?? null,
    priorProgress,
  };
}

/** @deprecated use buildPlayerContext */
export async function buildHistorySummary(userId: string): Promise<string | null> {
  const ctx = await buildPlayerContext(userId);
  return ctx.historySummary;
}
