"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { createClient } from "@/lib/supabase/client";
import { PRICE_FIRST_ANALYSIS_DISPLAY, PRICE_PER_ANALYSIS_DISPLAY } from "@/lib/pricing";

export default function SignupPage() {
  const router = useRouter();
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
    const supabase = createClient();
    const { data, error: authError } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { display_name: displayName } },
    });
    setLoading(false);
    if (authError) {
      setError(authError.message);
      return;
    }
    if (data.user && !data.session) {
      setPendingLogin(true);
      return;
    }
    router.push("/dashboard");
    router.refresh();
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <h1 className="text-2xl font-semibold">Create account</h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Free account · first swing {PRICE_FIRST_ANALYSIS_DISPLAY}, then {PRICE_PER_ANALYSIS_DISPLAY} each
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
              Dev tip: Supabase Dashboard → Authentication → Sign In / Providers → Email → turn off{" "}
              <strong>Confirm email</strong> so sign-up logs you in immediately.
            </p>
          </div>
        ) : (
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <input
            type="text"
            placeholder="Display name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm"
          />
          <input
            type="email"
            placeholder="Email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm"
          />
          <input
            type="password"
            placeholder="Password (min 6 characters)"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm"
          />
          {error && <p className="text-sm text-red-500">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Creating account..." : "Create account"}
          </Button>
        </form>
        )}

        <p className="mt-4 text-center text-sm text-[var(--color-muted)]">
          Already have an account?{" "}
          <Link href="/login" className="text-[var(--color-accent)] hover:underline">
            Log in
          </Link>
        </p>
      </Card>
    </div>
  );
}
