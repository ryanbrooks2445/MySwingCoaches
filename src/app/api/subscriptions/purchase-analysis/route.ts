import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { createServiceClient } from "@/lib/supabase/admin";
import { addAnalysisCredit } from "@/lib/add-analysis-credit";
import { getNextAnalysisPrice, getNextAnalysisPriceDisplay } from "@/lib/pricing";
import { isStripeConfigured } from "@/lib/stripe";

/** Dev fallback when Stripe keys are not set. Production uses /api/stripe/checkout. */
export async function POST() {
  if (process.env.NODE_ENV === "production" || process.env.ENABLE_DEV_CREDIT_STUB !== "true") {
    return NextResponse.json(
      { error: "Dev credit stub is disabled. Configure Stripe Checkout to sell analysis credits." },
      { status: 403 }
    );
  }

  if (isStripeConfigured()) {
    return NextResponse.json(
      { error: "Use Stripe Checkout. Call POST /api/stripe/checkout instead." },
      { status: 400 }
    );
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const serviceClient = createServiceClient();
  const { data: sub, error: fetchError } = await serviceClient
    .from("subscriptions")
    .select("analyses_limit, analyses_used")
    .eq("user_id", user.id)
    .single();

  if (fetchError || !sub) {
    return NextResponse.json({ error: "Subscription not found" }, { status: 404 });
  }

  const analysesUsed = sub.analyses_used ?? 0;
  const analysesLimit = sub.analyses_limit ?? 0;
  const price = getNextAnalysisPrice(analysesUsed, analysesLimit);
  const priceDisplay = getNextAnalysisPriceDisplay(analysesUsed, analysesLimit);

  const result = await addAnalysisCredit(user.id);

  return NextResponse.json({
    success: true,
    message: `Added 1 analysis credit (${priceDisplay} — dev stub, no charge).`,
    analyses_remaining: result.analyses_remaining,
    price,
  });
}
