"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { AppNav } from "@/components/AppNav";
import { PublicHeader } from "@/components/PublicHeader";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { readApiResponse } from "@/lib/api-response";
import { createClient } from "@/lib/supabase/client";
import {
  PRICE_ANNUAL_UNLIMITED_DISPLAY,
  PRICE_PER_ANALYSIS_DISPLAY,
  PRODUCT_ANNUAL_UNLIMITED,
  SWING_MODE_LABELS,
  SWING_MODES,
} from "@/lib/pricing";
import {
  analysisCreditsRemaining,
  hasActiveAnnualSubscription,
} from "@/lib/subscription-access";
import type { Subscription } from "@/lib/types";

function PricingContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [message, setMessage] = useState<string | null>(null);
  const [loadingProduct, setLoadingProduct] = useState<string | null>(null);
  const [portalLoading, setPortalLoading] = useState(false);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [signedIn, setSignedIn] = useState<boolean | null>(null);

  const refreshPricing = useCallback(async (): Promise<Subscription | null> => {
    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();
    if (!user) {
      setSignedIn(false);
      setSubscription(null);
      return null;
    }
    setSignedIn(true);
    const { data: sub } = await supabase
      .from("subscriptions")
      .select("*")
      .eq("user_id", user.id)
      .single();
    setSubscription(sub ?? null);
    return sub ?? null;
  }, []);

  useEffect(() => {
    refreshPricing();
  }, [refreshPricing]);

  useEffect(() => {
    const checkout = searchParams.get("checkout");
    const product = searchParams.get("product");
    if (checkout === "success") {
      const successMessage =
        product === "annual"
          ? "Payment received. Confirming your unlimited subscription..."
          : "Payment received. Confirming your analysis credit...";
      setMessage(successMessage);
      let attempts = 0;
      const poll = window.setInterval(async () => {
        attempts += 1;
        const sub = await refreshPricing();
        const remaining = sub ? analysisCreditsRemaining(sub) : null;
        const unlimited = sub ? hasActiveAnnualSubscription(sub) : false;
        if (unlimited || (remaining !== null && remaining !== "unlimited" && remaining > 0)) {
          window.clearInterval(poll);
          setMessage(
            unlimited
              ? "Payment confirmed. Your unlimited subscription is active."
              : "Payment confirmed. Your analysis credit is ready."
          );
          return;
        }
        if (attempts >= 10) {
          window.clearInterval(poll);
          setMessage(
            "Payment received. Confirmation is taking longer than expected; refresh shortly or contact support."
          );
        }
      }, 1500);
      router.replace("/pricing");
      return () => window.clearInterval(poll);
    }
    if (checkout === "cancelled") {
      setMessage("Checkout cancelled. No charge was made.");
      router.replace("/pricing");
    }
  }, [searchParams, refreshPricing, router]);

  async function startCheckout(product: typeof PRODUCT_ANNUAL_UNLIMITED | "swing_upload") {
    setLoadingProduct(product);
    setMessage(null);
    try {
      const checkoutRes = await fetch("/api/stripe/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product }),
      });
      const checkoutData = await readApiResponse<{ url?: string }>(checkoutRes);

      if (checkoutRes.status === 401) {
        router.push("/login?redirect=/pricing");
        return;
      }

      if (checkoutRes.ok && checkoutData.url) {
        window.location.href = checkoutData.url as string;
        return;
      }

      throw new Error(checkoutData.error ?? "Checkout failed");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Purchase failed");
    } finally {
      setLoadingProduct(null);
    }
  }

  async function openBillingPortal() {
    setPortalLoading(true);
    setMessage(null);
    try {
      const res = await fetch("/api/stripe/portal", { method: "POST" });
      const data = await readApiResponse<{ url?: string }>(res);
      if (res.status === 401) {
        router.push("/login?redirect=/pricing");
        return;
      }
      if (!res.ok || !data.url) {
        throw new Error(data.error ?? "Could not open billing portal");
      }
      window.location.href = data.url;
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Could not open billing portal");
    } finally {
      setPortalLoading(false);
    }
  }

  const creditsRemaining = subscription ? analysisCreditsRemaining(subscription) : null;
  const annualActive = subscription ? hasActiveAnnualSubscription(subscription) : false;

  return (
    <div className="min-h-screen">
      {signedIn ? <AppNav /> : <PublicHeader />}
      <main className="mx-auto max-w-4xl px-4 py-8">
        <div className="text-center">
          <h1 className="text-3xl font-semibold">Pricing</h1>
          <p className="mt-2 text-[var(--color-muted)]">
            Pay per swing or go unlimited for the year.
          </p>
          <p className="mt-2 text-xs text-[var(--color-muted)]">
            Secure checkout powered by Stripe
          </p>
          <p className="mt-3 text-sm text-[var(--color-muted)]">
            If analysis cannot be completed after automatic retries, your credit is restored.
          </p>
        </div>

        {message && (
          <div className="mx-auto mt-6 rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] px-4 py-3 text-sm">
            {message}
          </div>
        )}

        {creditsRemaining === "unlimited" && (
          <p className="mx-auto mt-4 text-center text-sm text-[var(--color-accent)]">
            Unlimited analyses active
            {subscription?.period_end
              ? ` until ${new Date(subscription.period_end).toLocaleDateString()}`
              : ""}{" "}
            —{" "}
            <Link href="/upload" className="underline">
              upload now
            </Link>
          </p>
        )}

        {creditsRemaining !== null && creditsRemaining !== "unlimited" && creditsRemaining > 0 && (
          <p className="mx-auto mt-4 text-center text-sm text-[var(--color-accent)]">
            {creditsRemaining} credit{creditsRemaining === 1 ? "" : "s"} ready —{" "}
            <Link href="/upload" className="underline">
              upload now
            </Link>
          </p>
        )}

        {annualActive && (
          <div className="mx-auto mt-4 flex justify-center">
            <Button variant="secondary" disabled={portalLoading} onClick={openBillingPortal}>
              {portalLoading ? "Opening portal..." : "Manage subscription"}
            </Button>
          </div>
        )}

        <div className="mt-10 grid gap-6 md:grid-cols-2">
          <Card className="flex flex-col text-center">
            <h2 className="text-xl font-semibold">Per swing</h2>
            <p className="mt-4 text-5xl font-semibold">{PRICE_PER_ANALYSIS_DISPLAY}</p>
            <p className="mt-1 text-sm text-[var(--color-muted)]">per video upload</p>
            <ul className="mx-auto mt-8 max-w-sm flex-1 space-y-2 text-left text-sm text-[var(--color-muted)]">
              <li>• Full swing, chipping, or putting — same price</li>
              <li>• One priority, feel, drill, and 7-day plan</li>
              <li>• Buy only when you need an analysis</li>
              <li>• Private source video removed after 30 days</li>
            </ul>
            <Button
              className="mt-8 w-full"
              disabled={loadingProduct !== null}
              onClick={() => startCheckout("swing_upload")}
            >
              {loadingProduct === "swing_upload"
                ? "Redirecting to checkout..."
                : `Buy 1 analysis — ${PRICE_PER_ANALYSIS_DISPLAY}`}
            </Button>
          </Card>

          <Card className="flex flex-col border-[var(--color-accent)]/40 text-center">
            <p className="text-xs font-semibold uppercase tracking-wide text-[var(--color-accent)]">
              Best value
            </p>
            <h2 className="mt-2 text-xl font-semibold">Unlimited annual</h2>
            <p className="mt-4 text-5xl font-semibold">{PRICE_ANNUAL_UNLIMITED_DISPLAY}</p>
            <p className="mt-1 text-sm text-[var(--color-muted)]">per year · unlimited uploads</p>
            <ul className="mx-auto mt-8 max-w-sm flex-1 space-y-2 text-left text-sm text-[var(--color-muted)]">
              <li>• Unlimited swing analyses for 12 months</li>
              <li>• Full swing, chipping, and putting included</li>
              <li>• Auto-renews yearly — cancel anytime in Stripe</li>
              <li>• Same coach-style reports every upload</li>
            </ul>
            <Button
              className="mt-8 w-full"
              disabled={loadingProduct !== null || annualActive}
              onClick={() => startCheckout(PRODUCT_ANNUAL_UNLIMITED)}
            >
              {annualActive
                ? "Subscription active"
                : loadingProduct === PRODUCT_ANNUAL_UNLIMITED
                  ? "Redirecting to checkout..."
                  : `Subscribe — ${PRICE_ANNUAL_UNLIMITED_DISPLAY}/year`}
            </Button>
          </Card>
        </div>

        <Link href="/upload" className="mt-6 block text-center text-sm text-[var(--color-accent)] hover:underline">
          Go to upload →
        </Link>

        <p className="mx-auto mt-6 max-w-2xl text-center text-xs leading-relaxed text-[var(--color-muted)]">
          AI-generated coaching guidance is not a guaranteed performance result or a replacement
          for instruction from a certified golf professional. By purchasing, you agree to the{" "}
          <Link href="/terms" className="underline">Terms</Link> and{" "}
          <Link href="/refund-policy" className="underline">Refund Policy</Link>.
        </p>

        <Card className="mt-8">
          <h2 className="text-lg font-semibold">Modes</h2>
          <ul className="mt-4 space-y-3 text-sm text-[var(--color-muted)]">
            {SWING_MODES.map((mode) => (
              <li key={mode}>
                <span className="font-medium text-[var(--color-foreground)]">
                  {SWING_MODE_LABELS[mode]}
                </span>
                {" — "}
                {mode === "full_swing"
                  ? "Driver through wedges — full motion."
                  : mode === "chipping"
                    ? "Short game around the green."
                    : "Stroke mechanics on the green."}
              </li>
            ))}
          </ul>
        </Card>
      </main>
    </div>
  );
}

export default function PricingPage() {
  return (
    <Suspense fallback={<div className="min-h-screen" />}>
      <PricingContent />
    </Suspense>
  );
}
