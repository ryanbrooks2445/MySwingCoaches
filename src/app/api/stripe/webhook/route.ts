import { NextResponse } from "next/server";
import { headers } from "next/headers";
import type Stripe from "stripe";
import { addAnalysisCredit } from "@/lib/add-analysis-credit";
import { createServiceClient } from "@/lib/supabase/admin";
import { getStripe, isStripeConfigured } from "@/lib/stripe";

export const runtime = "nodejs";

async function fulfillCheckoutSession(session: Stripe.Checkout.Session): Promise<void> {
  const userId = session.metadata?.user_id;
  if (!userId) {
    throw new Error("checkout.session.completed missing metadata.user_id");
  }

  const serviceClient = createServiceClient();
  const { data: existing } = await serviceClient
    .from("stripe_checkout_sessions")
    .select("id")
    .eq("id", session.id)
    .maybeSingle();

  if (existing) {
    return;
  }

  const result = await addAnalysisCredit(userId);

  const { error: insertError } = await serviceClient.from("stripe_checkout_sessions").insert({
    id: session.id,
    user_id: userId,
    amount_cents: session.amount_total ?? 0,
    credits_added: 1,
    analyses_limit_after: result.analyses_limit,
  });

  if (insertError) {
    throw new Error(insertError.message);
  }
}

export async function POST(request: Request) {
  if (!isStripeConfigured()) {
    return NextResponse.json({ error: "Stripe not configured" }, { status: 503 });
  }

  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET?.trim();
  if (!webhookSecret) {
    return NextResponse.json({ error: "STRIPE_WEBHOOK_SECRET not set" }, { status: 503 });
  }

  const body = await request.text();
  const signature = (await headers()).get("stripe-signature");
  if (!signature) {
    return NextResponse.json({ error: "Missing stripe-signature" }, { status: 400 });
  }

  const stripe = getStripe();
  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Invalid signature";
    console.error("Stripe webhook signature error:", message);
    return NextResponse.json({ error: message }, { status: 400 });
  }

  try {
    if (event.type === "checkout.session.completed") {
      const session = event.data.object as Stripe.Checkout.Session;
      if (session.payment_status === "paid") {
        await fulfillCheckoutSession(session);
      }
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : "Webhook handler failed";
    console.error("Stripe webhook handler error:", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }

  return NextResponse.json({ received: true });
}
