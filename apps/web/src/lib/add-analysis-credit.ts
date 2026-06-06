import { createServiceClient } from "@/lib/supabase/admin";

export async function addAnalysisCredit(userId: string): Promise<{
  analyses_remaining: number;
  analyses_limit: number;
}> {
  const serviceClient = createServiceClient();
  const { data: sub, error: fetchError } = await serviceClient
    .from("subscriptions")
    .select("analyses_limit, analyses_used")
    .eq("user_id", userId)
    .single();

  if (fetchError || !sub) {
    throw new Error("Subscription not found");
  }

  const analysesUsed = sub.analyses_used ?? 0;
  const newLimit = (sub.analyses_limit ?? 0) + 1;

  const { error: updateError } = await serviceClient
    .from("subscriptions")
    .update({ analyses_limit: newLimit, status: "active" })
    .eq("user_id", userId);

  if (updateError) {
    throw new Error(updateError.message);
  }

  return {
    analyses_remaining: newLimit - analysesUsed,
    analyses_limit: newLimit,
  };
}
