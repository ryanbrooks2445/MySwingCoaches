import { createHmac, timingSafeEqual } from "crypto";
import { NextRequest, NextResponse } from "next/server";
import { createServiceClient } from "@/lib/supabase/admin";

export const runtime = "nodejs";

function verifyStripeSignature(payload: string, signatureHeader: string | null, secret: string) {
  if (!signatureHeader) return false;
  const parts = Object.fromEntries(
    signatureHeader.split(",").map((part) => {
      const [key, value] = part.split("=");
      return [key, value];
    })
  );
  if (!parts.t || !parts.v1) return false;
  const timestamp = Number.parseInt(parts.t, 10);
  if (!Number.isFinite(timestamp)) return false;
  const ageSeconds = Math.abs(Date.now() / 1000 - timestamp);
  if (ageSeconds > 300) return false;

  const expected = createHmac("sha256", secret)
    .update(`${parts.t}.${payload}`)
    .digest("hex");

  const expectedBuffer = Buffer.from(expected, "hex");
  const receivedBuffer = Buffer.from(parts.v1, "hex");
  if (expectedBuffer.length !== receivedBuffer.length) return false;
  return timingSafeEqual(expectedBuffer, receivedBuffer);
}

export async function POST(request: NextRequest) {
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!webhookSecret) {
    return NextResponse.json({ error: "Stripe webhook not configured" }, { status: 500 });
  }

  const payload = await request.text();
  const signature = request.headers.get("stripe-signature");
  if (!verifyStripeSignature(payload, signature, webhookSecret)) {
    return NextResponse.json({ error: "Invalid Stripe signature" }, { status: 400 });
  }

  const event = JSON.parse(payload) as {
    type?: string;
    data?: {
      object?: {
        id?: string;
        client_reference_id?: string;
        amount_total?: number;
        metadata?: Record<string, string | undefined>;
      };
    };
  };

  if (event.type !== "checkout.session.completed") {
    return NextResponse.json({ received: true });
  }

  const session = event.data?.object;
  const userId = session?.metadata?.user_id || session?.client_reference_id;
  const sessionId = session?.id;
  const credits = Number.parseInt(session?.metadata?.credits || "1", 10);

  if (!sessionId || !userId || !Number.isFinite(credits) || credits < 1) {
    return NextResponse.json({ error: "Invalid checkout session payload" }, { status: 400 });
  }

  const supabase = createServiceClient();
  const { data: existing } = await supabase
    .from("stripe_checkout_sessions")
    .select("id")
    .eq("id", sessionId)
    .maybeSingle();

  if (existing) {
    return NextResponse.json({ received: true, duplicate: true });
  }

  const { data: sub, error: subError } = await supabase
    .from("subscriptions")
    .select("analyses_limit")
    .eq("user_id", userId)
    .single();

  if (subError || !sub) {
    return NextResponse.json({ error: "Subscription not found" }, { status: 404 });
  }

  const limitAfter = (sub.analyses_limit ?? 0) + credits;
  const { error: updateError } = await supabase
    .from("subscriptions")
    .update({ analyses_limit: limitAfter, status: "active" })
    .eq("user_id", userId);

  if (updateError) {
    return NextResponse.json({ error: updateError.message }, { status: 500 });
  }

  const { error: insertError } = await supabase.from("stripe_checkout_sessions").insert({
    id: sessionId,
    user_id: userId,
    amount_cents: session.amount_total ?? 0,
    credits_added: credits,
    analyses_limit_after: limitAfter,
  });

  if (insertError) {
    return NextResponse.json({ error: insertError.message }, { status: 500 });
  }

  return NextResponse.json({ received: true });
}
