"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { CheckCircle2, Lock, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { readApiResponse } from "@/lib/api-response";
import { PRICE_ANNUAL_UNLIMITED_DISPLAY, PRICE_PER_ANALYSIS_DISPLAY } from "@/lib/pricing";

const deliverables = [
  "One swing priority, not a list of ten fixes",
  "Evidence from visible checkpoints in your video",
  "One feel and one matched practice drill",
  "A seven-day practice plan and next-upload goal",
];

function SignupForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirect") || "/dashboard";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const response = await fetch("/api/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, displayName, redirectTo }),
    });
    const data = await readApiResponse<{ redirectTo?: string }>(response);
    setLoading(false);
    if (!response.ok) {
      setError(data.error || "We could not create that account.");
      return;
    }
    const destination =
      data.redirectTo?.startsWith("/") ? data.redirectTo : redirectTo.startsWith("/") ? redirectTo : "/dashboard";
    router.push(destination);
    router.refresh();
  }

  return (
    <div className="min-h-screen bg-[var(--color-background)]">
      <div className="mx-auto grid min-h-screen max-w-6xl lg:grid-cols-2">
        <div className="flex items-center justify-center px-4 py-12">
          <Card className="w-full max-w-md">
            <h1 className="text-2xl font-semibold">Create your free account</h1>
            <p className="mt-1 text-sm text-[var(--color-muted)]">
              No charge until you choose a plan. Analyses from {PRICE_PER_ANALYSIS_DISPLAY} each or{" "}
              {PRICE_ANNUAL_UNLIMITED_DISPLAY}/year unlimited.
            </p>

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <label className="block text-sm">
                <span className="font-medium">Display name</span>
                <input
                  type="text"
                  autoComplete="name"
                  required
                  maxLength={80}
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3"
                />
              </label>
              <label className="block text-sm">
                <span className="font-medium">Email</span>
                <input
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3"
                />
              </label>
              <label className="block text-sm">
                <span className="font-medium">Password</span>
                <input
                  type="password"
                  autoComplete="new-password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3"
                />
                <span className="mt-1 block text-xs text-[var(--color-muted)]">
                  At least eight characters.
                </span>
              </label>
              {error && <p className="text-sm text-red-500">{error}</p>}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Creating account..." : "Create account & continue"}
              </Button>
            </form>

            <p className="mt-4 text-center text-sm text-[var(--color-muted)]">
              Already have an account?{" "}
              <Link
                href={`/login?redirect=${encodeURIComponent(redirectTo)}`}
                className="text-[var(--color-accent)] hover:underline"
              >
                Log in
              </Link>
            </p>
          </Card>
        </div>

        <aside className="flex flex-col justify-center border-t border-[var(--color-border)] bg-[var(--color-card)] px-6 py-12 lg:border-l lg:border-t-0">
          <p className="text-sm font-semibold uppercase tracking-wide text-[var(--color-accent)]">
            What you get
          </p>
          <h2 className="mt-2 text-2xl font-semibold leading-tight sm:text-3xl">
            A coach-style plan you can use at the range
          </h2>
          <p className="mt-3 text-sm text-[var(--color-muted)]">
            Each analysis is {PRICE_PER_ANALYSIS_DISPLAY} — or go unlimited for{" "}
            {PRICE_ANNUAL_UNLIMITED_DISPLAY}/year.
          </p>

          <ul className="mt-8 space-y-4">
            {deliverables.map((item) => (
              <li key={item} className="flex gap-3 text-sm text-[var(--color-muted)]">
                <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-[var(--color-accent)]" />
                <span>{item}</span>
              </li>
            ))}
          </ul>

          <div className="mt-8 space-y-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] p-4 text-sm">
            <p className="flex items-center gap-2 text-[var(--color-muted)]">
              <Lock className="h-4 w-4 shrink-0 text-[var(--color-accent)]" />
              Private upload · 30-day video retention · failed-analysis credit guarantee
            </p>
            <p className="flex items-center gap-2 text-[var(--color-muted)]">
              <ShieldCheck className="h-4 w-4 shrink-0 text-[var(--color-accent)]" />
              Secure checkout powered by Stripe
            </p>
          </div>

          <Link
            href="/example"
            className="mt-6 inline-flex text-sm font-medium text-[var(--color-accent)] hover:underline"
          >
            See a full example report →
          </Link>
        </aside>
      </div>
    </div>
  );
}

export default function SignupPage() {
  return (
    <Suspense fallback={<div className="min-h-screen" />}>
      <SignupForm />
    </Suspense>
  );
}
