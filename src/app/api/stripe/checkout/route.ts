import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { createServiceClient } from "@/lib/supabase/admin";
import { PRICE_PER_ANALYSIS_CENTS } from "@/lib/pricing";
import {
  appUrl,
  checkoutDisplayName,
  checkoutStatementDescriptor,
  getStripe,
  isStripeConfigured,
} from "@/lib/stripe";
import { enforceRateLimit } from "@/lib/rate-limit";

export async function POST(request: NextRequest) {
  if (!isStripeConfigured()) {
    return NextResponse.json(
      { error: "Checkout is temporarily unavailable. Please contact support." },
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
    scope: "checkout",
    identifier: user.id,
    limit: 5,
    windowSeconds: 3600,
  });
  if (limited) return limited;

  const serviceClient = createServiceClient();
  const { data: sub, error: fetchError } = await serviceClient
    .from("subscriptions")
    .select("stripe_customer_id")
    .eq("user_id", user.id)
    .single();

  if (fetchError || !sub) {
    return NextResponse.json({ error: "Subscription not found" }, { status: 404 });
  }

  const unitAmount = PRICE_PER_ANALYSIS_CENTS;

  const stripe = getStripe();
  let customerId = sub.stripe_customer_id as string | null;

  if (!customerId) {
    const customer = await stripe.customers.create({
      email: user.email ?? undefined,
      metadata: { user_id: user.id },
    });
    customerId = customer.id;
    await serviceClient
      .from("subscriptions")
      .update({ stripe_customer_id: customerId })
      .eq("user_id", user.id);
  }

  const base = appUrl();
  const session = await stripe.checkout.sessions.create({
    mode: "payment",
    customer: customerId,
    branding_settings: {
      display_name: checkoutDisplayName(),
    },
    line_items: [
      {
        quantity: 1,
        price_data: {
          currency: "usd",
          unit_amount: unitAmount,
          product_data: {
            name: "MySwingCoaches — Swing Analysis",
            description: "One swing upload with AI coaching feedback",
          },
        },
      },
    ],
    payment_intent_data: {
      statement_descriptor: checkoutStatementDescriptor(),
    },
    metadata: {
      user_id: user.id,
      product: "swing_upload",
      expected_amount_cents: String(unitAmount),
    },
    success_url: `${base}/pricing?checkout=success`,
    cancel_url: `${base}/pricing?checkout=cancelled`,
  });

  if (!session.url) {
    return NextResponse.json({ error: "Could not create checkout session" }, { status: 500 });
  }

  return NextResponse.json({ url: session.url });
}
