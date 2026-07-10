"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AppNav } from "@/components/AppNav";
import { PageHero } from "@/components/PageHero";
import { Reveal } from "@/components/Reveal";
import { GolferProfileForm } from "@/components/GolferProfileForm";
import { UploadDropzone } from "@/components/UploadDropzone";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { readApiResponse } from "@/lib/api-response";
import { trackEvent } from "@/lib/analytics";
import { createClient } from "@/lib/supabase/client";
import {
  SWING_MODE_HINTS,
  SWING_MODE_LABELS,
  SWING_MODES,
  type SwingMode,
} from "@/lib/pricing";
import { analysisCreditsRemaining } from "@/lib/subscription-access";
import type { Subscription } from "@/lib/types";
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
    return "The video upload was interrupted. Please refresh and try a shorter MP4 or MOV.";
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

async function uploadToSignedStorageUrl(args: {
  path: string;
  token: string;
  file: File;
  accessToken?: string;
}): Promise<void> {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!supabaseUrl || !anonKey) {
    throw new Error("Secure upload is not configured.");
  }

  const cleanPath = args.path.replace(/^\/|\/$/g, "").replace(/\/+/g, "/");
  const uploadUrl = new URL(
    `${supabaseUrl.replace(/\/$/, "")}/storage/v1/object/upload/sign/swing-videos/${cleanPath}`
  );
  uploadUrl.searchParams.set("token", args.token);

  const body = new FormData();
  body.append("cacheControl", "3600");
  body.append("", args.file);

  const response = await fetch(uploadUrl.toString(), {
    method: "PUT",
    headers: {
      apikey: anonKey,
      "x-upsert": "false",
      ...(args.accessToken ? { Authorization: `Bearer ${args.accessToken}` } : {}),
    },
    body,
  });

  if (response.ok) return;

  const parsed = await readApiResponse<{ message?: string }>(response);
  throw new Error(parsed.error || parsed.message || "The video upload was interrupted.");
}

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

  useEffect(() => {
    async function loadCredits() {
      const supabase = createClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) return;
      const { data: sub } = await supabase
        .from("subscriptions")
        .select("*")
        .eq("user_id", user.id)
        .single();
      if (!sub) {
        setCredits(0);
        return;
      }
      const remaining = analysisCreditsRemaining(sub as Subscription);
      setCredits(remaining === "unlimited" ? "unlimited" : remaining);
    }
    loadCredits();
  }, []);

  const hasCredit = credits === "unlimited" || (credits !== null && credits > 0);

  async function handleUpload() {
    if (!file || !profileComplete) return;
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
      const {
        data: { session },
      } = await supabase.auth.getSession();

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
      await uploadToSignedStorageUrl({
        path: intent.path,
        token: intent.token,
        file,
        accessToken: session?.access_token,
      });

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
      trackEvent("upload_complete");
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
      <main id="main-content" className="mx-auto max-w-2xl px-4 py-8 sm:py-12">
        <Reveal immediate>
          <PageHero
            eyebrow="Upload"
            title="Send your swing for analysis"
            description="Upload your swing, then pay only when you're ready to analyze."
          />
        </Reveal>

        <Reveal immediate>
          <p className="mt-6 rounded-2xl border border-[var(--color-border)] bg-[var(--color-sand)] px-4 py-3 text-sm text-[var(--color-muted)]">
            Videos are private and automatically removed after 30 days. Most reports are ready in
            2–5 minutes; free-tier cold starts can take longer.
          </p>
        </Reveal>

        {credits !== null && hasCredit && (
          <p className="mt-2 text-sm">
            {credits === "unlimited" ? (
              <span className="text-[var(--color-accent)]">Unlimited analyses</span>
            ) : (
              <span>
                <span className="font-medium text-[var(--color-foreground)]">{credits}</span>{" "}
                credit{credits === 1 ? "" : "s"} available — analysis starts immediately after upload
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
            "mt-8 rounded-3xl space-y-6 transition-opacity",
            !profileComplete && "pointer-events-none opacity-50"
          )}
        >
          {!profileComplete && (
            <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-700 dark:text-amber-400">
              Save your golfer profile above to unlock video upload.
            </p>
          )}

          <div>
            <p className="text-sm font-medium" id="swing-mode-label">
              Mode
            </p>
            <div
              role="radiogroup"
              aria-labelledby="swing-mode-label"
              className="mt-2 grid grid-cols-3 gap-2"
            >
              {SWING_MODES.map((mode) => (
                <button
                  key={mode}
                  type="button"
                  role="radio"
                  aria-checked={swingMode === mode}
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
            disabled={!file || uploading || !profileComplete}
            className="w-full rounded-full"
            variant="cta"
            size="lg"
          >
            {uploading
              ? "Uploading..."
              : hasCredit
                ? "Upload securely & analyze"
                : "Upload securely — pay to analyze"}
          </Button>
        </Card>
      </main>
    </div>
  );
}
