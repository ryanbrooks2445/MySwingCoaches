"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { readApiResponse } from "@/lib/api-response";
import { PRICE_PER_ANALYSIS_DISPLAY } from "@/lib/pricing";

function SignupForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirect") || "/dashboard";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pendingLogin, setPendingLogin] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setPendingLogin(false);
    const response = await fetch("/api/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, displayName, redirectTo }),
    });
    const data = await readApiResponse<{ requiresConfirmation?: boolean }>(response);
    setLoading(false);
    if (!response.ok) {
      setError(data.error || "We could not create that account.");
      return;
    }
    if (data.requiresConfirmation) {
      setPendingLogin(true);
      return;
    }
    router.push(redirectTo.startsWith("/") ? redirectTo : "/dashboard");
    router.refresh();
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <h1 className="text-2xl font-semibold">Create account</h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Free account · swing analyses are {PRICE_PER_ANALYSIS_DISPLAY} each
        </p>

        {pendingLogin ? (
          <div className="mt-6 space-y-4 rounded-xl border border-[var(--color-accent)]/30 bg-[var(--color-accent)]/10 p-4">
            <p className="text-sm font-medium">Account created</p>
            <p className="text-sm text-[var(--color-muted)]">
              If email confirmation is on, check your inbox first. Otherwise go straight to log in.
            </p>
            <Link href="/login">
              <Button className="w-full">Log in</Button>
            </Link>
            <p className="text-xs text-[var(--color-muted)]">
              The confirmation link protects your account and private swing videos.
            </p>
          </div>
        ) : (
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
            {loading ? "Creating account..." : "Create account"}
          </Button>
        </form>
        )}

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
  );
}

export default function SignupPage() {
  return (
    <Suspense fallback={<div className="min-h-screen" />}>
      <SignupForm />
    </Suspense>
  );
}
