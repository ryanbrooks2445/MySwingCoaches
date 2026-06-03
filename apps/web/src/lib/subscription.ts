import { createServiceClient } from "@/lib/supabase/admin";
import { PLAN_LIMITS, type Subscription } from "@/lib/types";

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

export async function buildHistorySummary(userId: string): Promise<string | null> {
  const supabase = createServiceClient();
  const { data } = await supabase
    .from("swing_reports")
    .select("overall_score, main_diagnosis, created_at")
    .eq("user_id", userId)
    .eq("status", "ready")
    .order("created_at", { ascending: false })
    .limit(5);

  if (!data?.length) return null;
  return data
    .map((r, i) => `Swing ${i + 1}: score ${r.overall_score}, ${r.main_diagnosis?.slice(0, 80)}`)
    .join("\n");
}
