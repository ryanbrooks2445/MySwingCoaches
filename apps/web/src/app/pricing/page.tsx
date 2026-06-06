"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { AppNav } from "@/components/AppNav";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { createClient } from "@/lib/supabase/client";
import {
  PRICE_FIRST_ANALYSIS_DISPLAY,
  PRICE_PER_ANALYSIS_DISPLAY,
  SWING_MODE_LABELS,
  SWING_MODES,
  getNextAnalysisPriceDisplay,
  qualifiesForIntroPrice,
} from "@/lib/pricing";

function PricingContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [nextPrice, setNextPrice] = useState(PRICE_FIRST_ANALYSIS_DISPLAY);
  const [introEligible, setIntroEligible] = useState(false);
  const [creditsReady, setCreditsReady] = useState<number | null>(null);

  const refreshPricing = useCallback(async () => {
    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();
    if (!user) {
      setNextPrice(PRICE_FIRST_ANALYSIS_DISPLAY);
      setIntroEligible(true);
      setCreditsReady(null);
      return;
    }
    const { data: sub } = await supabase
      .from("subscriptions")
      .select("analyses_limit, analyses_used")
      .eq("user_id", user.id)
      .single();
    if (!sub) {
      setNextPrice(PRICE_FIRST_ANALYSIS_DISPLAY);
      setIntroEligible(true);
      setCreditsReady(null);
      return;
    }
    const used = sub.analyses_used ?? 0;
    const limit = sub.analyses_limit ?? 0;
    setNextPrice(getNextAnalysisPriceDisplay(used, limit));
    setIntroEligible(qualifiesForIntroPrice(used, limit));
    setCreditsReady(Math.max(0, limit - used));
  }, []);

  useEffect(() => {
    refreshPricing();
  }, [refreshPricing]);

  useEffect(() => {
    const checkout = searchParams.get("checkout");
    if (checkout === "success") {
      setMessage("Payment successful. Your analysis credit is ready — head to upload.");
      refreshPricing();
      router.replace("/pricing");
    } else if (checkout === "cancelled") {
      setMessage("Checkout cancelled. No charge was made.");
      router.replace("/pricing");
    }
  }, [searchParams, refreshPricing, router]);

  async function purchaseAnalysis() {
    setLoading(true);
    setMessage(null);
    try {
      const checkoutRes = await fetch("/api/stripe/checkout", { method: "POST" });
      const checkoutData = await checkoutRes.json();

      if (checkoutRes.status === 401) {
        router.push("/login?redirect=/pricing");
        return;
      }

      if (checkoutRes.ok && checkoutData.url) {
        window.location.href = checkoutData.url as string;
        return;
      }

      if (checkoutRes.status === 503) {
        const stubRes = await fetch("/api/subscriptions/purchase-analysis", { method: "POST" });
        const stubData = await stubRes.json();
        if (!stubRes.ok) throw new Error(stubData.error);
        setMessage(
          `${stubData.message} You have ${stubData.analyses_remaining} upload${stubData.analyses_remaining === 1 ? "" : "s"} ready.`
        );
        setNextPrice(PRICE_PER_ANALYSIS_DISPLAY);
        setIntroEligible(false);
        setCreditsReady(stubData.analyses_remaining);
        return;
      }

      throw new Error(checkoutData.error ?? "Checkout failed");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Purchase failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen">
      <AppNav />
      <main className="mx-auto max-w-2xl px-4 py-8">
        <div className="text-center">
          <h1 className="text-3xl font-semibold">Pricing</h1>
          <p className="mt-2 text-[var(--color-muted)]">
            Pay per upload. No subscription required.
          </p>
          <p className="mt-2 text-xs text-[var(--color-muted)]">
            Secure checkout powered by Stripe
          </p>
        </div>

        {message && (
          <div className="mx-auto mt-6 rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] px-4 py-3 text-sm">
            {message}
          </div>
        )}

        {creditsReady !== null && creditsReady > 0 && (
          <p className="mx-auto mt-4 text-center text-sm text-[var(--color-accent)]">
            {creditsReady} credit{creditsReady === 1 ? "" : "s"} ready —{" "}
            <Link href="/upload" className="underline">
              upload now
            </Link>
          </p>
        )}

        <Card className="mt-10 text-center">
          <h2 className="text-xl font-semibold">One AI coaching blueprint</h2>
          {introEligible ? (
            <>
              <p className="mt-4 text-5xl font-semibold">{PRICE_FIRST_ANALYSIS_DISPLAY}</p>
              <p className="mt-1 text-sm text-[var(--color-muted)]">
                your first swing · then {PRICE_PER_ANALYSIS_DISPLAY} each
              </p>
            </>
          ) : (
            <>
              <p className="mt-4 text-5xl font-semibold">{nextPrice}</p>
              <p className="mt-1 text-sm text-[var(--color-muted)]">per video upload</p>
            </>
          )}
          <ul className="mx-auto mt-8 max-w-sm space-y-2 text-left text-sm text-[var(--color-muted)]">
            <li>• Full swing, chipping, or putting — same price</li>
            <li>• Short diagnostic + feels + 7-day plan</li>
            <li>• YouTube drills matched to your missing piece</li>
            <li>• Personalized to your history in that mode</li>
          </ul>
          <Button
            className="mt-8 w-full"
            disabled={loading}
            onClick={purchaseAnalysis}
          >
            {loading ? "Redirecting to checkout..." : `Buy 1 analysis — ${nextPrice}`}
          </Button>
          <Link href="/upload" className="mt-4 block text-sm text-[var(--color-accent)] hover:underline">
            Go to upload →
          </Link>
        </Card>

        {!introEligible && (
          <p className="mt-6 text-center text-sm text-[var(--color-muted)]">
            Intro pricing ({PRICE_FIRST_ANALYSIS_DISPLAY} first swing) is one-time per account.
          </p>
        )}

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
    <Suspense
      fallback={
        <div className="min-h-screen">
          <AppNav />
          <main className="mx-auto max-w-2xl px-4 py-8 text-center text-[var(--color-muted)]">
            Loading pricing...
          </main>
        </div>
      }
    >
      <PricingContent />
    </Suspense>
  );
}
