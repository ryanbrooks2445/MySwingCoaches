import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { createServiceClient } from "@/lib/supabase/admin";
import { PRICE_PER_ANALYSIS, PRICE_PER_ANALYSIS_DISPLAY } from "@/lib/pricing";

function appUrl() {
  return process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";
}

async function createStripeCheckoutSession(userId: string) {
  const stripeSecretKey = process.env.STRIPE_SECRET_KEY;
  const stripePriceId = process.env.STRIPE_PRICE_ID_ANALYSIS;

  if (!stripeSecretKey || !stripePriceId) return null;

  const params = new URLSearchParams();
  params.set("mode", "payment");
  params.set("client_reference_id", userId);
  params.set("line_items[0][price]", stripePriceId);
  params.set("line_items[0][quantity]", "1");
  params.set("success_url", `${appUrl()}/pricing?checkout=success`);
  params.set("cancel_url", `${appUrl()}/pricing?checkout=cancelled`);
  params.set("metadata[user_id]", userId);
  params.set("metadata[credits]", "1");

  const response = await fetch("https://api.stripe.com/v1/checkout/sessions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${stripeSecretKey}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: params,
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error?.message || "Stripe checkout failed");
  }

  return data.url as string | null;
}

export async function POST() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const checkoutUrl = await createStripeCheckoutSession(user.id);
    if (checkoutUrl) {
      return NextResponse.json({
        success: true,
        checkout_url: checkoutUrl,
        message: "Redirecting to Stripe Checkout.",
      });
    }
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Stripe checkout failed" },
      { status: 502 }
    );
  }

  if (process.env.ENABLE_DEV_CREDIT_STUB !== "true") {
    return NextResponse.json(
      {
        error:
          "Payments are not configured. Set STRIPE_SECRET_KEY, STRIPE_PRICE_ID_ANALYSIS, and STRIPE_WEBHOOK_SECRET before launch.",
      },
      { status: 503 }
    );
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

  const newLimit = (sub.analyses_limit ?? 0) + 1;
  const { error: updateError } = await serviceClient
    .from("subscriptions")
    .update({ analyses_limit: newLimit, status: "active" })
    .eq("user_id", user.id);

  if (updateError) {
    return NextResponse.json({ error: updateError.message }, { status: 500 });
  }

  const remaining = newLimit - (sub.analyses_used ?? 0);

  return NextResponse.json({
    success: true,
    message: `Added 1 dev analysis credit (${PRICE_PER_ANALYSIS_DISPLAY} — no charge).`,
    analyses_remaining: remaining,
    price: PRICE_PER_ANALYSIS,
  });
}
