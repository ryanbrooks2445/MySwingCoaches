"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AuthLayout } from "@/components/AuthLayout";
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
    <AuthLayout
      asideTitle={isUpdating ? "Almost there" : "We've got you"}
      asideDescription={
        isUpdating
          ? "Choose a strong password and you'll be back to your swing reports in seconds."
          : "Enter the email on your account and we'll send a secure reset link if it exists."
      }
    >
      <Card className="ring-gradient w-full max-w-md rounded-3xl">
        <h1 className="font-display text-2xl font-bold">
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
              className="input-field"
            />
          </label>
          {status && <p role="status" className="text-sm text-[var(--color-muted)]">{status}</p>}
          <Button type="submit" variant="cta" className="w-full">
            {isUpdating ? "Update password" : "Send reset link"}
          </Button>
        </form>
        <Link
          href="/login"
          className="mt-4 block text-center text-sm font-medium text-[var(--color-accent)] hover:underline"
        >
          Back to login
        </Link>
      </Card>
    </AuthLayout>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="min-h-screen" />}>
      <ResetPasswordForm />
    </Suspense>
  );
}
