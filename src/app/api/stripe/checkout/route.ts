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

function parseCheckoutProduct(body: unknown): CheckoutProduct {
  if (
    body &&
    typeof body === "object" &&
    "product" in body &&
    (body as { product?: string }).product === PRODUCT_ANNUAL_UNLIMITED
  ) {
    return PRODUCT_ANNUAL_UNLIMITED;
  }
  return PRODUCT_SWING_UPLOAD;
}

function parseReportId(body: unknown): string | null {
  if (!body || typeof body !== "object" || !("reportId" in body)) return null;
  const reportId = (body as { reportId?: unknown }).reportId;
  if (typeof reportId !== "string" || !reportId.trim()) return null;
  return reportId.trim();
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

  let product: CheckoutProduct = PRODUCT_SWING_UPLOAD;
  let reportId: string | null = null;
  try {
    const body = await request.json();
    product = parseCheckoutProduct(body);
    reportId = parseReportId(body);
  } catch {
    product = PRODUCT_SWING_UPLOAD;
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

  if (reportId) {
    const { data: report, error: reportError } = await serviceClient
      .from("swing_reports")
      .select("id, status")
      .eq("id", reportId)
      .eq("user_id", user.id)
      .single();
    if (reportError || !report) {
      return NextResponse.json({ error: "Swing report not found." }, { status: 404 });
    }
    if (report.status !== "awaiting_payment") {
      return NextResponse.json(
        { error: "This swing does not need payment before analysis." },
        { status: 409 }
      );
    }
  }

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
      ...(reportId ? { report_id: reportId } : {}),
    },
    success_url: reportId
      ? `${base}/swings/${reportId}?checkout=success`
      : `${base}/pricing?checkout=success`,
    cancel_url: reportId
      ? `${base}/swings/${reportId}?checkout=cancelled`
      : `${base}/pricing?checkout=cancelled`,
  });

  if (!session.url) {
    return NextResponse.json({ error: "Could not create checkout session" }, { status: 500 });
  }

  return NextResponse.json({ url: session.url });
}
