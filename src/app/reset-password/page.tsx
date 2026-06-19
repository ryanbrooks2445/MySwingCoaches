"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { createClient } from "@/lib/supabase/client";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const isUpdating = searchParams.get("mode") === "update";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<string | null>(null);

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <h1 className="text-2xl font-semibold">
          {isUpdating ? "Choose a new password" : "Reset password"}
        </h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          {isUpdating
            ? "Use at least eight characters."
            : "We’ll send a secure password-reset link if the account exists."}
        </p>
        <form
          className="mt-6 space-y-4"
          onSubmit={async (event) => {
            event.preventDefault();
            const supabase = createClient();
            if (isUpdating) {
              const { error } = await supabase.auth.updateUser({ password });
              setStatus(error ? error.message : "Password updated. You can now log in.");
              return;
            }
            await supabase.auth.resetPasswordForEmail(email, {
              redirectTo: `${window.location.origin}/auth/callback?next=${encodeURIComponent(
                "/reset-password?mode=update"
              )}`,
            });
            setStatus("Check your inbox for a password-reset link.");
          }}
        >
          <label className="block text-sm">
            <span className="font-medium">{isUpdating ? "New password" : "Email"}</span>
            <input
              type={isUpdating ? "password" : "email"}
              required
              minLength={isUpdating ? 8 : undefined}
              autoComplete={isUpdating ? "new-password" : "email"}
              value={isUpdating ? password : email}
              onChange={(event) =>
                isUpdating ? setPassword(event.target.value) : setEmail(event.target.value)
              }
              className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3"
            />
          </label>
          {status && <p role="status" className="text-sm text-[var(--color-muted)]">{status}</p>}
          <Button type="submit" className="w-full">
            {isUpdating ? "Update password" : "Send reset link"}
          </Button>
        </form>
        <Link href="/login" className="mt-4 block text-center text-sm text-[var(--color-accent)]">
          Back to login
        </Link>
      </Card>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="min-h-screen" />}>
      <ResetPasswordForm />
    </Suspense>
  );
}
