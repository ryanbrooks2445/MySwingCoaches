import { NextResponse } from "next/server";
import { headers } from "next/headers";
import type Stripe from "stripe";
import { createServiceClient } from "@/lib/supabase/admin";
import {
  PRICE_PER_ANALYSIS_CENTS,
  PRODUCT_ANNUAL_UNLIMITED,
  PRODUCT_SWING_UPLOAD,
} from "@/lib/pricing";
import { getStripe, isStripeConfigured } from "@/lib/stripe";

export const runtime = "nodejs";

const REVOKED_SUBSCRIPTION_STATUSES = new Set([
  "canceled",
  "unpaid",
  "past_due",
  "incomplete_expired",
]);

type SubscriptionWithPeriod = Stripe.Subscription & { current_period_end: number };
type InvoiceWithSubscription = Stripe.Invoice & {
  subscription?: string | Stripe.Subscription | null;
};

function subscriptionPeriodEndIso(subscription: Stripe.Subscription): string {
  const periodEnd = (subscription as SubscriptionWithPeriod).current_period_end;
  if (typeof periodEnd !== "number") {
    throw new Error("Subscription missing current_period_end");
  }
  return new Date(periodEnd * 1000).toISOString();
}

function invoiceSubscriptionId(invoice: Stripe.Invoice): string | null {
  const subscription = (invoice as InvoiceWithSubscription).subscription;
  if (!subscription) return null;
  return typeof subscription === "string" ? subscription : subscription.id;
}

async function verifyCustomerMatch(userId: string, customerId: string | Stripe.Customer | Stripe.DeletedCustomer | null): Promise<void> {
  const serviceClient = createServiceClient();
  const { data: subscription } = await serviceClient
    .from("subscriptions")
    .select("stripe_customer_id")
    .eq("user_id", userId)
    .single();
  if (
    !subscription?.stripe_customer_id ||
    String(customerId) !== subscription.stripe_customer_id
  ) {
    throw new Error("Checkout session customer did not match the signed-in account");
  }
}

async function fulfillSwingUploadSession(session: Stripe.Checkout.Session): Promise<void> {
  const userId = session.metadata?.user_id;
  if (!userId) {
    throw new Error("checkout.session.completed missing metadata.user_id");
  }

  const amount = session.amount_total ?? 0;
  const expectedAmount = Number(session.metadata?.expected_amount_cents);
  if (
    session.mode !== "payment" ||
    session.payment_status !== "paid" ||
    session.currency !== "usd" ||
    session.metadata?.product !== PRODUCT_SWING_UPLOAD ||
    amount !== PRICE_PER_ANALYSIS_CENTS ||
    amount !== expectedAmount
  ) {
    throw new Error("Checkout session payment details did not match the expected analysis price");
  }

  await verifyCustomerMatch(userId, session.customer);

  const serviceClient = createServiceClient();
  const { error } = await serviceClient.rpc("service_fulfill_checkout_session", {
    p_session_id: session.id,
    p_user_id: userId,
    p_amount_cents: amount,
  });
  if (error) {
    throw new Error(error.message);
  }
}

async function fulfillAnnualSubscriptionCheckout(
  session: Stripe.Checkout.Session,
  stripe: Stripe
): Promise<void> {
  const userId = session.metadata?.user_id;
  if (!userId) {
    throw new Error("checkout.session.completed missing metadata.user_id");
  }
  if (session.mode !== "subscription" || session.metadata?.product !== PRODUCT_ANNUAL_UNLIMITED) {
    throw new Error("Checkout session was not an annual unlimited subscription");
  }

  const subscriptionId =
    typeof session.subscription === "string" ? session.subscription : session.subscription?.id;
  if (!subscriptionId) {
    throw new Error("Subscription checkout missing subscription id");
  }

  await verifyCustomerMatch(userId, session.customer);

  const subscription = await stripe.subscriptions.retrieve(subscriptionId);
  const periodEnd = subscriptionPeriodEndIso(subscription);

  const serviceClient = createServiceClient();
  const { error } = await serviceClient.rpc("service_fulfill_subscription", {
    p_user_id: userId,
    p_stripe_subscription_id: subscription.id,
    p_period_end: periodEnd,
    p_plan: "unlimited_annual",
  });
  if (error) {
    throw new Error(error.message);
  }
}

async function extendSubscriptionPeriod(
  stripeSubscriptionId: string,
  periodEndIso: string
): Promise<void> {
  const serviceClient = createServiceClient();
  const { error } = await serviceClient.rpc("service_extend_subscription_period", {
    p_stripe_subscription_id: stripeSubscriptionId,
    p_period_end: periodEndIso,
  });
  if (error) {
    throw new Error(error.message);
  }
}

async function revokeSubscription(stripeSubscriptionId: string): Promise<void> {
  const serviceClient = createServiceClient();
  const { error } = await serviceClient.rpc("service_revoke_subscription", {
    p_stripe_subscription_id: stripeSubscriptionId,
  });
  if (error) {
    throw new Error(error.message);
  }
}

async function handleInvoicePaid(invoice: Stripe.Invoice, stripe: Stripe): Promise<void> {
  const subscriptionId = invoiceSubscriptionId(invoice);
  if (!subscriptionId || invoice.billing_reason === "subscription_create") {
    return;
  }

  const subscription = await stripe.subscriptions.retrieve(subscriptionId);
  const periodEnd = subscriptionPeriodEndIso(subscription);
  await extendSubscriptionPeriod(subscription.id, periodEnd);
}

async function handleSubscriptionUpdated(subscription: Stripe.Subscription): Promise<void> {
  if (REVOKED_SUBSCRIPTION_STATUSES.has(subscription.status)) {
    await revokeSubscription(subscription.id);
    return;
  }

  if (subscription.status === "active") {
    const periodEnd = subscriptionPeriodEndIso(subscription);
    await extendSubscriptionPeriod(subscription.id, periodEnd);
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
    switch (event.type) {
      case "checkout.session.completed": {
        const session = event.data.object as Stripe.Checkout.Session;
        if (session.payment_status !== "paid") break;
        if (session.mode === "payment") {
          await fulfillSwingUploadSession(session);
        } else if (session.mode === "subscription") {
          await fulfillAnnualSubscriptionCheckout(session, stripe);
        }
        break;
      }
      case "invoice.paid": {
        const invoice = event.data.object as Stripe.Invoice;
        await handleInvoicePaid(invoice, stripe);
        break;
      }
      case "customer.subscription.updated": {
        const subscription = event.data.object as Stripe.Subscription;
        await handleSubscriptionUpdated(subscription);
        break;
      }
      case "customer.subscription.deleted": {
        const subscription = event.data.object as Stripe.Subscription;
        await revokeSubscription(subscription.id);
        break;
      }
      default:
        break;
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : "Webhook handler failed";
    console.error("Stripe webhook handler error:", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }

  return NextResponse.json({ received: true });
}
