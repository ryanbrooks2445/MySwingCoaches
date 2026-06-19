"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AppNav } from "@/components/AppNav";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { createClient } from "@/lib/supabase/client";

export default function AccountPage() {
  const router = useRouter();
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  return (
    <div className="min-h-screen">
      <AppNav />
      <main className="mx-auto max-w-2xl px-4 py-10">
        <h1 className="text-3xl font-semibold">Account</h1>
        <Card className="mt-8 border-red-500/30">
          <h2 className="text-lg font-semibold text-red-500">Delete account permanently</h2>
          <p className="mt-2 text-sm text-[var(--color-muted)]">
            This immediately deletes your account, reports, swing videos, and generated frames.
            Payment processors may retain records required by law. This cannot be undone.
          </p>
          <label className="mt-5 block text-sm">
            <span className="font-medium">Type DELETE to confirm</span>
            <input
              value={confirmation}
              onChange={(event) => setConfirmation(event.target.value)}
              className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-3"
            />
          </label>
          {error && <p role="alert" className="mt-3 text-sm text-red-500">{error}</p>}
          <Button
            className="mt-5"
            disabled={confirmation !== "DELETE" || deleting}
            onClick={async () => {
              setDeleting(true);
              setError(null);
              const response = await fetch("/api/account", {
                method: "DELETE",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ confirmation }),
              });
              const data = await response.json();
              if (!response.ok) {
                setError(data.error || "Deletion failed.");
                setDeleting(false);
                return;
              }
              await createClient().auth.signOut();
              router.replace("/");
              router.refresh();
            }}
          >
            {deleting ? "Deleting account..." : "Delete account"}
          </Button>
        </Card>
      </main>
    </div>
  );
}
