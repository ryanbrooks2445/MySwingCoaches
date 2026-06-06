"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

type DeleteSwingButtonProps = {
  reportId: string;
  label?: string;
  variant?: "ghost" | "secondary";
  className?: string;
  confirmMessage?: string;
  redirectTo?: string;
  onDeleted?: () => void;
};

export function DeleteSwingButton({
  reportId,
  label = "Delete",
  variant = "ghost",
  className,
  confirmMessage = "Delete this swing and its analysis? This cannot be undone.",
  redirectTo,
  onDeleted,
}: DeleteSwingButtonProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm(confirmMessage)) return;

    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/swings/${reportId}`, { method: "DELETE" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Delete failed");
      onDeleted?.();
      if (redirectTo) router.push(redirectTo);
      else router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <span className={cn("inline-flex flex-col items-end gap-1", className)}>
      <Button
        type="button"
        variant={variant}
        size="sm"
        disabled={loading}
        onClick={handleClick}
        className="text-red-500 hover:text-red-600"
      >
        {loading ? "Deleting…" : label}
      </Button>
      {error && <span className="text-xs text-red-500">{error}</span>}
    </span>
  );
}

export function ClearSwingHistoryButton({ className }: { className?: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    if (
      !confirm(
        "Delete ALL swings and training history? Videos and analyses will be permanently removed. This cannot be undone."
      )
    ) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/swings?all=true", { method: "DELETE" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Clear failed");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Clear failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <span className={cn("inline-flex flex-col items-end gap-1", className)}>
      <Button
        type="button"
        variant="secondary"
        size="sm"
        disabled={loading}
        onClick={handleClick}
        className="text-red-500 hover:text-red-600"
      >
        {loading ? "Clearing…" : "Clear all history"}
      </Button>
      {error && <span className="text-xs text-red-500">{error}</span>}
    </span>
  );
}
