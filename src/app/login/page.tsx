"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { useState } from "react";
import { AuthLayout } from "@/components/AuthLayout";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { GoogleSignInButton } from "@/components/GoogleSignInButton";
import { readApiResponse } from "@/lib/api-response";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirect") || "/dashboard";
  const urlError = searchParams.get("error");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(
    urlError === "oauth_failed"
      ? "Google sign-in was cancelled or failed. Please try again."
      : urlError === "expired_link"
        ? "That sign-in link has expired. Please try again."
        : urlError === "invalid_link"
          ? "That sign-in link was invalid. Please try again."
          : null
  );
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await readApiResponse(response);
    setLoading(false);
    if (!response.ok) {
      setError(data.error || "We could not log you in.");
      return;
    }
    router.push(redirectTo.startsWith("/") ? redirectTo : "/dashboard");
    router.refresh();
  }

  return (
    <AuthLayout
      asideTitle="Welcome back to the range"
      asideDescription="Pick up where you left off — your reports and upload history are waiting."
      asideFooter={
        <Link
          href="/example"
          className="inline-flex text-sm font-medium text-[var(--color-lime)] hover:underline"
        >
          See a full example report →
        </Link>
      }
    >
      <Card className="ring-gradient w-full max-w-md rounded-3xl">
        <h1 className="font-display text-2xl font-bold">Log in</h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">Welcome back to ForeFixed</p>

        <div className="mt-6">
          <GoogleSignInButton redirectTo={redirectTo} label="Log in with Google" />
        </div>

        <div className="my-6 flex items-center gap-3 text-xs text-[var(--color-muted)]">
          <span className="h-px flex-1 bg-[var(--color-border)]" />
          or
          <span className="h-px flex-1 bg-[var(--color-border)]" />
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
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
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field"
            />
          </label>
          {error && <p role="alert" className="text-sm text-[var(--color-danger)]">{error}</p>}
          <Button type="submit" variant="cta" className="w-full" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-[var(--color-muted)]">
          No account?{" "}
          <Link
            href={`/signup?redirect=${encodeURIComponent(redirectTo)}`}
            className="font-medium text-[var(--color-accent)] hover:underline"
          >
            Create a new account
          </Link>
        </p>
        <p className="mt-3 text-center text-sm">
          <Link href="/reset-password" className="text-[var(--color-muted)] hover:underline">
            Forgot password?
          </Link>
        </p>
      </Card>
    </AuthLayout>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen" />}>
      <LoginForm />
    </Suspense>
  );
}
