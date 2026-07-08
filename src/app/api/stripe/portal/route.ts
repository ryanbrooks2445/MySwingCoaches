import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { createServiceClient } from "@/lib/supabase/admin";
import { appUrl, getStripe, isStripeConfigured } from "@/lib/stripe";
import { enforceRateLimit } from "@/lib/rate-limit";

export async function POST(request: NextRequest) {
  if (!isStripeConfigured()) {
    return NextResponse.json(
      { error: "Billing portal is temporarily unavailable." },
      { status: 503 }
    );
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const limited = await enforceRateLimit(request, {
    scope: "billing-portal",
    identifier: user.id,
    limit: 10,
    windowSeconds: 3600,
  });
  if (limited) return limited;

  const serviceClient = createServiceClient();
  const { data: sub, error } = await serviceClient
    .from("subscriptions")
    .select("stripe_customer_id, stripe_subscription_id")
    .eq("user_id", user.id)
    .single();

  if (error || !sub?.stripe_customer_id || !sub.stripe_subscription_id) {
    return NextResponse.json({ error: "No active subscription to manage." }, { status: 404 });
  }

  const stripe = getStripe();
  const portalSession = await stripe.billingPortal.sessions.create({
    customer: sub.stripe_customer_id,
    return_url: `${appUrl()}/pricing`,
  });

  return NextResponse.json({ url: portalSession.url });
}
