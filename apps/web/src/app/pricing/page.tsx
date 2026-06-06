"use client";

import { useState } from "react";
import Link from "next/link";
import { AppNav } from "@/components/AppNav";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import {
  PRICE_PER_ANALYSIS_DISPLAY,
  SWING_MODE_LABELS,
  SWING_MODES,
} from "@/lib/pricing";

export default function PricingPage() {
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function purchaseAnalysis() {
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch("/api/subscriptions/purchase-analysis", {
        method: "POST",
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
        return;
      }
      setMessage(
        `${data.message} You have ${data.analyses_remaining} upload${data.analyses_remaining === 1 ? "" : "s"} ready.`
      );
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
        </div>

        {message && (
          <div className="mx-auto mt-6 rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] px-4 py-3 text-sm">
            {message}
          </div>
        )}

        <Card className="mt-10 text-center">
          <h2 className="text-xl font-semibold">One Golf Swing Analysis</h2>
          <p className="mt-4 text-5xl font-semibold">{PRICE_PER_ANALYSIS_DISPLAY}</p>
          <p className="mt-1 text-sm text-[var(--color-muted)]">per video upload</p>
          <ul className="mx-auto mt-8 max-w-sm space-y-2 text-left text-sm text-[var(--color-muted)]">
            <li>• Full swing, chipping, or putting — same price</li>
            <li>• Clear diagnosis, feels, and a 7-day plan</li>
            <li>• Drill clips matched to your main fault</li>
            <li>• Personalized to your profile and swing history</li>
          </ul>
          <Button
            className="mt-8 w-full"
            disabled={loading}
            onClick={purchaseAnalysis}
          >
            {loading ? "Processing..." : `Buy 1 Analysis — ${PRICE_PER_ANALYSIS_DISPLAY}`}
          </Button>
          <Link href="/upload" className="mt-4 block text-sm text-[var(--color-accent)] hover:underline">
            Go to upload →
          </Link>
        </Card>

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
