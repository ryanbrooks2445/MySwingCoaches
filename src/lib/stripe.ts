import Stripe from "stripe";

let stripeClient: Stripe | null = null;

export function isStripeConfigured(): boolean {
  return Boolean(process.env.STRIPE_SECRET_KEY?.trim());
}

export function getStripe(): Stripe {
  const key = process.env.STRIPE_SECRET_KEY?.trim();
  if (!key) {
    throw new Error("STRIPE_SECRET_KEY is not set");
  }
  if (!stripeClient) {
    stripeClient = new Stripe(key);
  }
  return stripeClient;
}

export function appUrl(): string {
  const configured = process.env.NEXT_PUBLIC_APP_URL?.trim();
  if (configured) return configured.replace(/\/$/, "");
  if (process.env.NODE_ENV === "production") {
    throw new Error("NEXT_PUBLIC_APP_URL is required in production");
  }
  return "http://localhost:3000";
}

/** Shown at the top of Stripe Checkout (overrides the Stripe account business name). */
export function checkoutDisplayName(): string {
  return process.env.STRIPE_CHECKOUT_DISPLAY_NAME?.trim() || "MySwingCoaches";
}

/** Appears on the customer's card/bank statement (max 22 chars, letters required). */
export function checkoutStatementDescriptor(): string {
  const configured = process.env.STRIPE_CHECKOUT_STATEMENT_DESCRIPTOR?.trim();
  if (configured) return configured.slice(0, 22);
  return "MYSWINGCOACHES";
}
