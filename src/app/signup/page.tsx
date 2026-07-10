"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { Lock, Mail, ShieldCheck } from "lucide-react";
import { AuthLayout } from "@/components/AuthLayout";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { GoogleSignInButton } from "@/components/GoogleSignInButton";
import { trackEvent } from "@/lib/analytics";
import { readApiResponse } from "@/lib/api-response";
import { PRICE_ANNUAL_UNLIMITED_DISPLAY, PRICE_PER_ANALYSIS_DISPLAY } from "@/lib/pricing";

function SignupForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirect") || "/dashboard";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [pendingEmail, setPendingEmail] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const response = await fetch("/api/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, displayName, redirectTo }),
    });
    const data = await readApiResponse<{
      redirectTo?: string;
      needsEmailConfirmation?: boolean;
      email?: string;
    }>(response);
    setLoading(false);
    if (!response.ok) {
      setError(data.error || "We could not create that account.");
      return;
    }

    if (data.needsEmailConfirmation) {
      trackEvent("signup_confirm_email");
      setPendingEmail(data.email || email);
      return;
    }

    trackEvent("signup_success");
    const destination =
      data.redirectTo?.startsWith("/") ? data.redirectTo : redirectTo.startsWith("/") ? redirectTo : "/dashboard";
    router.push(destination);
    router.refresh();
  }

  if (pendingEmail) {
    return (
      <AuthLayout
        asideTitle="Almost there"
        asideDescription="Confirm your email to unlock upload, checkout, and your swing reports."
      >
        <Card className="ring-gradient w-full max-w-md rounded-3xl text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-accent-muted)] text-[var(--color-accent-deep)]">
            <Mail className="h-6 w-6" />
          </div>
          <h1 className="mt-4 font-display text-2xl font-bold">Check your email</h1>
          <p className="mt-2 text-sm text-[var(--color-muted)]">
            We sent a confirmation link to{" "}
            <span className="font-medium text-[var(--color-foreground)]">{pendingEmail}</span>.
            Open it to finish creating your account.
          </p>
          <p className="mt-4 text-sm text-[var(--color-muted)]">
            Already confirmed?{" "}
            <Link
              href={`/login?redirect=${encodeURIComponent(redirectTo)}`}
              className="font-medium text-[var(--color-accent)] hover:underline"
            >
              Log in
            </Link>
          </p>
        </Card>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      asideTitle="A coach-style plan you can use at the range"
      asideDescription={`Each analysis is ${PRICE_PER_ANALYSIS_DISPLAY} — or go unlimited for ${PRICE_ANNUAL_UNLIMITED_DISPLAY}/year.`}
      asideFooter={
        <div className="space-y-3 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm">
          <p className="flex items-center gap-2 text-white/80">
            <Lock className="h-4 w-4 shrink-0 text-[var(--color-lime)]" />
            Private upload · 30-day video retention · failed-analysis credit guarantee
          </p>
          <p className="flex items-center gap-2 text-white/80">
            <ShieldCheck className="h-4 w-4 shrink-0 text-[var(--color-lime)]" />
            Secure checkout powered by Stripe
          </p>
        </div>
      }
    >
      <Card className="ring-gradient w-full max-w-md rounded-3xl">
        <h1 className="font-display text-2xl font-bold">Create your free account</h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          No charge until you choose a plan. Analyses from {PRICE_PER_ANALYSIS_DISPLAY} each or{" "}
          {PRICE_ANNUAL_UNLIMITED_DISPLAY}/year unlimited.
        </p>

        <div className="mt-6">
          <GoogleSignInButton redirectTo={redirectTo} label="Sign up with Google" />
        </div>

        <div className="my-6 flex items-center gap-3 text-xs text-[var(--color-muted)]">
          <span className="h-px flex-1 bg-[var(--color-border)]" />
          or
          <span className="h-px flex-1 bg-[var(--color-border)]" />
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block text-sm">
            <span className="font-medium">Display name</span>
            <input
              type="text"
              autoComplete="name"
              required
              maxLength={80}
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="input-field"
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
              className="input-field"
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
              className="input-field"
            />
            <span className="mt-1 block text-xs text-[var(--color-muted)]">
              At least eight characters. We will email a confirmation link.
            </span>
          </label>
          {error && <p role="alert" className="text-sm text-[var(--color-danger)]">{error}</p>}
          <Button type="submit" variant="cta" className="w-full" disabled={loading}>
            {loading ? "Creating account..." : "Create account"}
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-[var(--color-muted)]">
          Already have an account?{" "}
          <Link
            href={`/login?redirect=${encodeURIComponent(redirectTo)}`}
            className="font-medium text-[var(--color-accent)] hover:underline"
          >
            Log in
          </Link>
        </p>
      </Card>
    </AuthLayout>
  );
}

export default function SignupPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center text-sm text-[var(--color-muted)]">
          Loading…
        </div>
      }
    >
      <SignupForm />
    </Suspense>
  );
}
