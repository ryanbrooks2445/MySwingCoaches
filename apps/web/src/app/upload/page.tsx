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
  PRICE_PER_ANALYSIS_DISPLAY,
  SWING_MODE_HINTS,
  SWING_MODE_LABELS,
  SWING_MODES,
  type SwingMode,
} from "@/lib/pricing";
import { cn } from "@/lib/utils";

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [swingMode, setSwingMode] = useState<SwingMode>("full_swing");
  const [credits, setCredits] = useState<number | "unlimited" | null>(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [profileComplete, setProfileComplete] = useState(false);
  const [cameraAngle, setCameraAngle] = useState("unknown");
  const [handedness, setHandedness] = useState("");
  const [clubUsed, setClubUsed] = useState("");
  const [ballFlight, setBallFlight] = useState("");
  const [userGoal, setUserGoal] = useState("");
  const [handicap, setHandicap] = useState("");
  const [practiceAvailability, setPracticeAvailability] = useState("");

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
        return;
      }
      if (sub.plan === "serious" || sub.analyses_limit === -1) {
        setCredits("unlimited");
        return;
      }
      setCredits(Math.max(0, (sub.analyses_limit ?? 0) - (sub.analyses_used ?? 0)));
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

      setStatus("Uploading your video...");
      setProgress(20);

      const formData = new FormData();
      formData.append("file", file);
      formData.append("swingMode", swingMode);
      formData.append("cameraAngle", cameraAngle);
      formData.append("handedness", handedness);
      formData.append("clubUsed", clubUsed);
      formData.append("ballFlight", ballFlight);
      formData.append("userGoal", userGoal);
      formData.append("handicap", handicap);
      formData.append("practiceAvailability", practiceAvailability);

      const uploadRes = await fetch("/api/swings/upload", {
        method: "POST",
        body: formData,
      });

      const uploadData = await uploadRes.json();
      if (!uploadRes.ok) {
        throw new Error(uploadData.error || "Failed to upload swing");
      }

      setProgress(70);
      setStatus(`Analyzing your ${SWING_MODE_LABELS[swingMode].toLowerCase()} (usually 1-3 minutes)...`);

      const analyzeRes = await fetch(`/api/swings/${uploadData.reportId}/analyze`, {
        method: "POST",
      });

      let analyzeData: { error?: string } = {};
      try {
        analyzeData = await analyzeRes.json();
      } catch {
        throw new Error("The analysis service is temporarily unavailable. Please try again in a few minutes.");
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
          "Network error. Please check your connection and try again."
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
          {PRICE_PER_ANALYSIS_DISPLAY} per analysis · pick your mode first
        </p>

        {credits !== null && (
          <p className="mt-2 text-sm">
            {credits === "unlimited" ? (
              <span className="text-[var(--color-accent)]">Unlimited analyses</span>
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

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-sm">
              <span className="font-medium">Camera angle</span>
              <select
                value={cameraAngle}
                disabled={uploading}
                onChange={(e) => setCameraAngle(e.target.value)}
                className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2.5 text-sm outline-none focus:border-[var(--color-accent)]"
              >
                <option value="unknown">Not sure</option>
                <option value="down-the-line">Down the line</option>
                <option value="face-on">Face on</option>
              </select>
            </label>

            <label className="block text-sm">
              <span className="font-medium">Handedness</span>
              <select
                value={handedness}
                disabled={uploading}
                onChange={(e) => setHandedness(e.target.value)}
                className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2.5 text-sm outline-none focus:border-[var(--color-accent)]"
              >
                <option value="">Use profile/default</option>
                <option value="right">Right-handed</option>
                <option value="left">Left-handed</option>
              </select>
            </label>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-sm">
              <span className="font-medium">Club</span>
              <input
                value={clubUsed}
                disabled={uploading}
                maxLength={80}
                onChange={(e) => setClubUsed(e.target.value)}
                className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2.5 text-sm outline-none focus:border-[var(--color-accent)]"
                placeholder="Driver, 7 iron, wedge"
              />
            </label>

            <label className="block text-sm">
              <span className="font-medium">Handicap or scoring level</span>
              <input
                value={handicap}
                disabled={uploading}
                maxLength={80}
                onChange={(e) => setHandicap(e.target.value)}
                className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2.5 text-sm outline-none focus:border-[var(--color-accent)]"
                placeholder="12 handicap, shoots 90s"
              />
            </label>
          </div>

          <label className="block text-sm">
            <span className="font-medium">Typical miss or ball flight</span>
            <input
              value={ballFlight}
              disabled={uploading}
              maxLength={180}
              onChange={(e) => setBallFlight(e.target.value)}
              className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2.5 text-sm outline-none focus:border-[var(--color-accent)]"
              placeholder="Push slice, pull hook, thin contact, chunks"
            />
          </label>

          <label className="block text-sm">
            <span className="font-medium">What do you want fixed first?</span>
            <input
              value={userGoal}
              disabled={uploading}
              maxLength={180}
              onChange={(e) => setUserGoal(e.target.value)}
              className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2.5 text-sm outline-none focus:border-[var(--color-accent)]"
              placeholder="More consistent contact, stop slicing driver"
            />
          </label>

          <label className="block text-sm">
            <span className="font-medium">Practice time this week</span>
            <input
              value={practiceAvailability}
              disabled={uploading}
              maxLength={120}
              onChange={(e) => setPracticeAvailability(e.target.value)}
              className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2.5 text-sm outline-none focus:border-[var(--color-accent)]"
              placeholder="20 minutes a day, one range session"
            />
          </label>

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
              : `Upload & analyze — ${PRICE_PER_ANALYSIS_DISPLAY}`}
          </Button>
        </Card>
      </main>
    </div>
  );
}
