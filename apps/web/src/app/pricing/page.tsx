"use client";

import { useState } from "react";
import { AppNav } from "@/components/AppNav";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PLAN_PRICES, type SubscriptionPlan } from "@/lib/types";

export default function PricingPage() {
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState<string | null>(null);

  async function selectPlan(plan: SubscriptionPlan) {
    setLoading(plan);
    setMessage(null);
    try {
      const res = await fetch("/api/subscriptions/select-plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      if (plan === "free") {
        setMessage(`Plan updated to ${plan}. Stripe checkout is stubbed — no payment required.`);
      } else {
        setMessage(`Plan selection saved (${plan}). Stripe checkout coming soon — stub only, no charge.`);
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Failed to update plan");
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="min-h-screen">
      <AppNav />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <div className="text-center">
          <h1 className="text-3xl font-semibold">Pricing</h1>
          <p className="mt-2 text-[var(--color-muted)]">
            Choose a plan. Payment integration is stubbed for MVP.
          </p>
          <span className="mt-2 inline-block rounded-full bg-amber-500/15 px-3 py-1 text-xs font-medium text-amber-500">
            Stripe integration — placeholder
          </span>
        </div>

        {message && (
          <div className="mx-auto mt-6 max-w-lg rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] px-4 py-3 text-sm">
            {message}
          </div>
        )}

        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {(Object.entries(PLAN_PRICES) as [SubscriptionPlan, typeof PLAN_PRICES.free][]).map(
            ([plan, info]) => (
              <Card key={plan} className="flex flex-col">
                <h2 className="text-xl font-semibold">{info.name}</h2>
                <p className="mt-2 text-3xl font-semibold">{info.price}</p>
                <ul className="mt-6 flex-1 space-y-2 text-sm text-[var(--color-muted)]">
                  {info.features.map((f) => (
                    <li key={f}>• {f}</li>
                  ))}
                </ul>
                <Button
                  className="mt-6 w-full"
                  variant={plan === "player" ? "primary" : "secondary"}
                  disabled={loading === plan}
                  onClick={() => selectPlan(plan)}
                >
                  {loading === plan ? "Updating..." : plan === "free" ? "Current / Free" : "Subscribe (stub)"}
                </Button>
              </Card>
            )
          )}
        </div>

        <Card className="mt-8">
          <h2 className="text-lg font-semibold">Coach Review add-on</h2>
          <p className="mt-2 text-sm text-[var(--color-muted)]">
            Request a human coach to review your AI report and add personalized notes.
            Available as an add-on when Stripe is integrated.
          </p>
          <Button className="mt-4" variant="secondary" disabled>
            Request coach review (stub)
          </Button>
        </Card>
      </main>
    </div>
  );
}
