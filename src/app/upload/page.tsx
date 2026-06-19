"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { AppNav } from "@/components/AppNav";
import { GolferProfileForm } from "@/components/GolferProfileForm";
import { UploadDropzone } from "@/components/UploadDropzone";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { readApiResponse } from "@/lib/api-response";
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

async function videoDuration(file: File): Promise<number> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const video = document.createElement("video");
    video.preload = "metadata";
    video.onloadedmetadata = () => {
      URL.revokeObjectURL(url);
      resolve(video.duration);
    };
    video.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("This file could not be read as a video."));
    };
    video.src = url;
  });
}

function uploadErrorMessage(message: string): string {
  if (message === "Failed to fetch") {
    return "Your connection was interrupted. Please check your internet connection and try again.";
  }
  if (
    message.includes("Unexpected end of JSON input") ||
    message.includes("Failed to execute 'json'") ||
    message.includes("Request Entity Too Large")
  ) {
    return "The video upload was interrupted. Your credit was restored. Please refresh and try a shorter MP4 or MOV.";
  }
  return message;
}

async function cancelUploadSession(sessionId: string): Promise<void> {
  try {
    await fetch("/api/swings/upload-cancel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId }),
    });
  } catch {
    // The scheduled cleanup job also restores abandoned upload credits.
  }
}

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
    let cancellableSessionId: string | null = null;
    let uploadQueued = false;

    try {
      const supabase = createClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) throw new Error("Not logged in. Please log in and try again.");

      setStatus("Checking video...");
      const duration = await videoDuration(file);
      if (!Number.isFinite(duration) || duration <= 0) {
        throw new Error("This file could not be read as a video.");
      }
      if (duration > 30.5) {
        throw new Error("Video must be 30 seconds or shorter.");
      }

      setStatus("Preparing secure upload...");
      setProgress(15);
      const intentRes = await fetch("/api/swings/upload-intent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          originalFilename: file.name,
          mimeType: file.type,
          sizeBytes: file.size,
          swingMode,
        }),
      });
      const intent = await readApiResponse<{
        sessionId: string;
        reportId: string;
        path: string;
        token: string;
      }>(intentRes);
      if (!intentRes.ok) {
        throw new Error(intent.error || "Could not prepare upload.");
      }
      cancellableSessionId = intent.sessionId;

      setStatus("Uploading directly to private storage...");
      setProgress(35);
      const { error: storageError } = await supabase.storage
        .from("swing-videos")
        .uploadToSignedUrl(intent.path, intent.token, file, {
          contentType: file.type,
          upsert: false,
        });
      if (storageError) {
        throw new Error("The video upload was interrupted. Your credit will be restored.");
      }

      setProgress(80);
      setStatus("Securing your upload and joining the analysis queue...");
      const registerRes = await fetch("/api/swings/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId: intent.sessionId }),
      });
      const registered = await readApiResponse<{ reportId: string }>(registerRes);
      if (!registerRes.ok) {
        throw new Error(registered.error || "Could not queue analysis.");
      }
      uploadQueued = true;

      setProgress(100);
      setStatus("Upload complete. You can leave this page while we analyze it.");
      router.push(`/swings/${registered.reportId}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Something went wrong";
      if (cancellableSessionId && !uploadQueued) {
        await cancelUploadSession(cancellableSessionId);
      }
      setError(uploadErrorMessage(message));
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
        <p className="mt-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] px-3 py-2 text-sm text-[var(--color-muted)]">
          Videos are private and automatically removed after 30 days. Most reports are ready in
          2–5 minutes; free-tier cold starts can take longer.
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
              ? "Uploading..."
              : hasCredit
                ? "Upload securely & analyze"
                : `Buy credit first — ${nextPrice}`}
          </Button>
        </Card>
      </main>
    </div>
  );
}
