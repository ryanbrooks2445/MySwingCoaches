import { createServiceClient } from "@/lib/supabase/admin";
import { getNextAnalysisPriceDisplay } from "@/lib/pricing";
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
    const price = getNextAnalysisPriceDisplay(sub.analyses_used, sub.analyses_limit);
    return {
      allowed: false,
      reason: `No analyses left. Purchase one for ${price} on the pricing page.`,
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
  if (raw?.main_fix || raw?.feel_blueprint || raw?.diagnostic) return raw;
  return null;
}

function priorCoachingSummary(row: {
  main_diagnosis: string | null;
  practice_plan: string | null;
  coaching_content: unknown;
}): { focus: string; mainFix: string | null; drills: string[] } {
  const c = coachingFromRow(row);
  const focus =
    c?.roadmap?.weekly_focus ??
    c?.main_fix?.split(/[.!?]/)[0]?.trim() ??
    row.practice_plan ??
    row.main_diagnosis ??
    "Unknown";
  const mainFix = c?.main_fix?.trim() ?? null;
  const drills = (c?.drills ?? []).map((d) => d.name).filter(Boolean);
  return { focus, mainFix, drills };
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
  average9Score: number | null;
  typicalMiss: string | null;
  primaryGoal: string | null;
}> {
  const supabase = createServiceClient();

  const { data: profile } = await supabase
    .from("profiles")
    .select("display_name, age, years_playing, physical_limitations, average_9_score, typical_miss, primary_goal")
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
          const summary = priorCoachingSummary(r);
          const drillLine =
            summary.drills.length > 0 ? ` · drills: ${summary.drills.join(", ")}` : "";
          const fixLine = summary.mainFix ? ` · unlock was: ${summary.mainFix.slice(0, 120)}` : "";
          return `Swing ${i + 1} (${new Date(r.created_at).toLocaleDateString()}): focus "${summary.focus}"${fixLine}${drillLine}`;
        })
        .join("\n")
    : null;

  const lastSummary = prior?.[0] ? priorCoachingSummary(prior[0]) : null;
  const lastHeadline = lastSummary?.focus;
  const lastFocus = lastSummary?.focus;

  const lines: string[] = [];
  if (playerName) lines.push(`Player first name: ${playerName}`);
  if (profile?.average_9_score) lines.push(`Average 9-hole score: ${profile.average_9_score}.`);
  if (profile?.typical_miss) lines.push(`Typical miss: ${profile.typical_miss}.`);
  if (profile?.primary_goal) lines.push(`Main goal: ${profile.primary_goal}.`);
  if (swingMode) lines.push(`Mode for this upload: ${swingMode}.`);
  lines.push(`Completed ${swingMode ?? "total"} analyses before this upload: ${completed}`);
  lines.push(`This is their #${swingNumber} analysis in this mode.`);

  if (completed === 0) {
    lines.push("First blueprint — welcome them and pick ONE clear weekly focus.");
  } else if (lastHeadline) {
    lines.push(`Last focus we coached: "${lastHeadline}".`);
    if (lastSummary?.mainFix) {
      lines.push(`Last main unlock: "${lastSummary.mainFix.slice(0, 160)}".`);
    }
    if (lastSummary?.drills?.length) {
      lines.push(`Last drills prescribed: ${lastSummary.drills.join(", ")}.`);
      lines.push(
        "Do NOT repeat the same diagnosis or drill unless that exact Constraint is still visible on this new video."
      );
    }
    if (lastFocus) lines.push(`Last weekly focus: "${String(lastFocus).replace(/\*\*/g, "")}".`);
    lines.push(
      "Compare this video to last time — call out if the same missing piece persists or if they unlocked progress."
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
    average9Score: profile?.average_9_score ?? null,
    typicalMiss: profile?.typical_miss ?? null,
    primaryGoal: profile?.primary_goal ?? null,
  };
}

/** @deprecated use buildPlayerContext */
export async function buildHistorySummary(userId: string): Promise<string | null> {
  const ctx = await buildPlayerContext(userId);
  return ctx.historySummary;
}
