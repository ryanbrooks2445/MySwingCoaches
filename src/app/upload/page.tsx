"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { AppNav } from "@/components/AppNav";
import { GolferProfileForm } from "@/components/GolferProfileForm";
import { UploadDropzone } from "@/components/UploadDropzone";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { createClient } from "@/lib/supabase/client";
import {
  PRICE_FIRST_ANALYSIS_DISPLAY,
  PRICE_PER_ANALYSIS_DISPLAY,
  SWING_MODE_HINTS,
  SWING_MODE_LABELS,
  SWING_MODES,
  getNextAnalysisPriceDisplay,
  type SwingMode,
} from "@/lib/pricing";
import { cn } from "@/lib/utils";

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [swingMode, setSwingMode] = useState<SwingMode>("full_swing");
  const [credits, setCredits] = useState<number | "unlimited" | null>(null);
  const [nextPrice, setNextPrice] = useState(PRICE_FIRST_ANALYSIS_DISPLAY);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [profileComplete, setProfileComplete] = useState(false);

  useEffect(() => {
    async function loadCredits() {
      const supabase = createClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) return;
      const { data: sub } = await supabase
        .from("subscriptions")
        .select("analyses_limit, analyses_used, plan")
        .eq("user_id", user.id)
        .single();
      if (!sub) {
        setCredits(0);
        setNextPrice(PRICE_FIRST_ANALYSIS_DISPLAY);
        return;
      }
      const used = sub.analyses_used ?? 0;
      const limit = sub.analyses_limit ?? 0;
      setNextPrice(getNextAnalysisPriceDisplay(used, limit));
      if (sub.plan === "serious" || limit === -1) {
        setCredits("unlimited");
        return;
      }
      setCredits(Math.max(0, limit - used));
    }
    loadCredits();
  }, []);

  const hasCredit = credits === "unlimited" || (credits !== null && credits > 0);

  async function handleUpload() {
    if (!file || !hasCredit || !profileComplete) return;
    setUploading(true);
    setError(null);
    setProgress(5);

    try {
      const supabase = createClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) throw new Error("Not logged in. Please log in and try again.");

      setStatus("Uploading video to storage...");
      setProgress(20);

      const formData = new FormData();
      formData.append("file", file);
      formData.append("swingMode", swingMode);

      const uploadRes = await fetch("/api/swings/upload", {
        method: "POST",
        body: formData,
      });

      const uploadData = await uploadRes.json();
      if (!uploadRes.ok) {
        throw new Error(uploadData.error || "Failed to upload swing");
      }

      setProgress(70);
      setStatus(`Analyzing your ${SWING_MODE_LABELS[swingMode].toLowerCase()} (1–3 min)...`);

      const analyzeRes = await fetch(`/api/swings/${uploadData.reportId}/analyze`, {
        method: "POST",
        headers: uploadData.traceId
          ? { "X-Trace-Id": uploadData.traceId }
          : undefined,
      });

      let analyzeData: { error?: string } = {};
      try {
        analyzeData = await analyzeRes.json();
      } catch {
        throw new Error(
          "Analysis service unreachable. Start it with: cd analysis-service && uvicorn app.main:app --reload --port 8001"
        );
      }

      if (!analyzeRes.ok) {
        throw new Error(analyzeData.error || "Analysis failed");
      }

      setProgress(100);
      setStatus("Complete!");
      router.push(`/swings/${uploadData.reportId}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Something went wrong";
      if (message === "Failed to fetch") {
        setError(
          "Network error — is the dev server running? Run: npm run dev"
        );
      } else {
        setError(message);
      }
      setStatus(null);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="min-h-screen">
      <AppNav />
      <main className="mx-auto max-w-2xl px-4 py-8">
        <h1 className="text-3xl font-semibold">Upload</h1>
        <p className="mt-1 text-[var(--color-muted)]">
          {nextPrice} per analysis · pick your mode first
          {nextPrice === PRICE_FIRST_ANALYSIS_DISPLAY && (
            <span> · then {PRICE_PER_ANALYSIS_DISPLAY} each</span>
          )}
        </p>

        {credits !== null && (
          <p className="mt-2 text-sm">
            {credits === "unlimited" ? (
              <span className="text-[var(--color-accent)]">Unlimited analyses (dev)</span>
            ) : credits > 0 ? (
              <span>
                <span className="font-medium text-[var(--color-foreground)]">{credits}</span>{" "}
                credit{credits === 1 ? "" : "s"} available
              </span>
            ) : (
              <span className="text-red-500">
                No credits.{" "}
                <Link href="/pricing" className="underline">
                  Buy an analysis
                </Link>
              </span>
            )}
          </p>
        )}

        <GolferProfileForm
          className="mt-8"
          onCompleteChange={setProfileComplete}
        />

        <Card
          className={cn(
            "mt-8 space-y-6 transition-opacity",
            !profileComplete && "pointer-events-none opacity-50"
          )}
        >
          {!profileComplete && (
            <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-700 dark:text-amber-400">
              Save your golfer profile above to unlock video upload.
            </p>
          )}

          <div>
            <p className="text-sm font-medium">Mode</p>
            <div className="mt-2 grid grid-cols-3 gap-2">
              {SWING_MODES.map((mode) => (
                <button
                  key={mode}
                  type="button"
                  disabled={uploading}
                  onClick={() => setSwingMode(mode)}
                  className={cn(
                    "rounded-xl border px-3 py-3 text-sm font-medium transition-colors",
                    swingMode === mode
                      ? "border-[var(--color-accent)] bg-[var(--color-accent)]/10 text-[var(--color-foreground)]"
                      : "border-[var(--color-border)] text-[var(--color-muted)] hover:border-[var(--color-accent)]/50"
                  )}
                >
                  {SWING_MODE_LABELS[mode]}
                </button>
              ))}
            </div>
            <p className="mt-2 text-sm text-[var(--color-muted)]">{SWING_MODE_HINTS[swingMode]}</p>
          </div>

          <UploadDropzone
            onFileSelect={setFile}
            disabled={uploading || !profileComplete}
          />
          {file && (
            <p className="text-sm text-[var(--color-muted)]">
              Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(1)} MB)
            </p>
          )}

          {uploading && (
            <div className="space-y-2">
              <div className="h-2 overflow-hidden rounded-full bg-[var(--color-border)]">
                <div
                  className="h-full bg-[var(--color-accent)] transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-sm text-[var(--color-muted)]">{status}</p>
            </div>
          )}

          {error && <p className="text-sm text-red-500">{error}</p>}

          <Button
            onClick={handleUpload}
            disabled={!file || uploading || !hasCredit || !profileComplete}
            className="w-full"
            size="lg"
          >
            {uploading
              ? "Processing..."
              : hasCredit
                ? "Upload & analyze"
                : `Buy credit first — ${nextPrice}`}
          </Button>
        </Card>
      </main>
    </div>
  );
}
