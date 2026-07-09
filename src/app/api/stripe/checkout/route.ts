import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { createServiceClient } from "@/lib/supabase/admin";
import { CHECKOUT_ANNUAL_PRODUCT_NAME, CHECKOUT_PRODUCT_NAME } from "@/lib/brand";
import {
  PRICE_ANNUAL_UNLIMITED_CENTS,
  PRICE_PER_ANALYSIS_CENTS,
  PRODUCT_ANNUAL_UNLIMITED,
  PRODUCT_SWING_UPLOAD,
  type CheckoutProduct,
} from "@/lib/pricing";
import {
  appUrl,
  checkoutDisplayName,
  checkoutStatementDescriptor,
  getStripe,
  isStripeConfigured,
} from "@/lib/stripe";
import { enforceRateLimit } from "@/lib/rate-limit";
import { hasUnlimitedAccess } from "@/lib/subscription-access";
import type { Subscription } from "@/lib/types";

function parseCheckoutProduct(body: unknown): CheckoutProduct | null {
  if (!body || typeof body !== "object" || !("product" in body)) return null;
  const product = (body as { product?: string }).product;
  if (product === PRODUCT_ANNUAL_UNLIMITED) return PRODUCT_ANNUAL_UNLIMITED;
  if (product === PRODUCT_SWING_UPLOAD) return PRODUCT_SWING_UPLOAD;
  return null;
}

async function ensureStripeCustomer(
  user: { id: string; email?: string | null },
  existingCustomerId: string | null
): Promise<string> {
  if (existingCustomerId) return existingCustomerId;

  const stripe = getStripe();
  const customer = await stripe.customers.create({
    email: user.email ?? undefined,
    metadata: { user_id: user.id },
  });

  const serviceClient = createServiceClient();
  await serviceClient
    .from("subscriptions")
    .update({ stripe_customer_id: customer.id })
    .eq("user_id", user.id);

  return customer.id;
}

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

  let product: CheckoutProduct | null = null;
  try {
    const body = await request.json();
    product = parseCheckoutProduct(body);
  } catch {
    return NextResponse.json({ error: "Invalid request body" }, { status: 400 });
  }

  if (!product) {
    return NextResponse.json(
      { error: "Invalid product. Accepted values: 'swing_upload' or 'annual_unlimited'." },
      { status: 400 }
    );
  }

  const serviceClient = createServiceClient();
  const { data: sub, error: fetchError } = await serviceClient
    .from("subscriptions")
    .select("stripe_customer_id, stripe_subscription_id, plan, analyses_limit, status, period_end")
    .eq("user_id", user.id)
    .single();

  if (fetchError || !sub) {
    return NextResponse.json({ error: "Subscription not found" }, { status: 404 });
  }

  if (
    product === PRODUCT_ANNUAL_UNLIMITED &&
    sub.stripe_subscription_id &&
    hasUnlimitedAccess(sub as Subscription)
  ) {
    return NextResponse.json(
      { error: "You already have an active subscription. Manage it from the pricing page." },
      { status: 409 }
    );
  }

  const stripe = getStripe();
  const customerId = await ensureStripeCustomer(user, sub.stripe_customer_id as string | null);
  const base = appUrl();

  if (product === PRODUCT_ANNUAL_UNLIMITED) {
    const session = await stripe.checkout.sessions.create({
      mode: "subscription",
      customer: customerId,
      branding_settings: {
        display_name: checkoutDisplayName(),
      },
      line_items: [
        {
          quantity: 1,
          price_data: {
            currency: "usd",
            unit_amount: PRICE_ANNUAL_UNLIMITED_CENTS,
            recurring: { interval: "year" },
            product_data: {
              name: CHECKOUT_ANNUAL_PRODUCT_NAME,
              description: "Unlimited swing analyses for one year",
              statement_descriptor: checkoutStatementDescriptor(),
            },
          },
        },
      ],
      metadata: {
        user_id: user.id,
        product: PRODUCT_ANNUAL_UNLIMITED,
      },
      subscription_data: {
        metadata: {
          user_id: user.id,
          product: PRODUCT_ANNUAL_UNLIMITED,
        },
      },
      success_url: `${base}/pricing?checkout=success&product=annual`,
      cancel_url: `${base}/pricing?checkout=cancelled`,
    });

    if (!session.url) {
      return NextResponse.json({ error: "Could not create checkout session" }, { status: 500 });
    }

    return NextResponse.json({ url: session.url });
  }

  const unitAmount = PRICE_PER_ANALYSIS_CENTS;
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
            name: CHECKOUT_PRODUCT_NAME,
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
      product: PRODUCT_SWING_UPLOAD,
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
