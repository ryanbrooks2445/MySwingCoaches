import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { createServiceClient } from "@/lib/supabase/admin";
import { PLAN_LIMITS, type SubscriptionPlan } from "@/lib/types";

export async function POST(request: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { plan } = await request.json() as { plan: SubscriptionPlan };
  if (!plan || !PLAN_LIMITS[plan]) {
    return NextResponse.json({ error: "Invalid plan" }, { status: 400 });
  }

  const serviceClient = createServiceClient();
  const updatePayload: Record<string, unknown> = {
    plan,
    analyses_limit: PLAN_LIMITS[plan],
    status: "active",
  };
  if (plan !== "free") {
    updatePayload.analyses_used = 0;
  }

  const { error } = await serviceClient
    .from("subscriptions")
    .update(updatePayload)
    .eq("user_id", user.id);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({
    success: true,
    message: "Plan updated (Stripe stub — no payment processed)",
  });
}
