"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { AppNav } from "@/components/AppNav";
import { UploadDropzone } from "@/components/UploadDropzone";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { createClient } from "@/lib/supabase/client";

function guessMimeType(file: File): string {
  if (file.type) return file.type;
  const ext = file.name.split(".").pop()?.toLowerCase();
  if (ext === "mov") return "video/quicktime";
  return "video/mp4";
}

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setError(null);
    setProgress(5);

    try {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error("Not logged in. Please log in and try again.");

      const videoId = crypto.randomUUID();
      const reportId = crypto.randomUUID();
      const ext = file.name.split(".").pop()?.toLowerCase() || "mp4";
      const storagePath = `${user.id}/${videoId}/swing.${ext}`;
      const mimeType = guessMimeType(file);

      setStatus("Uploading video to storage...");
      setProgress(20);

      const { error: storageError } = await supabase.storage
        .from("swing-videos")
        .upload(storagePath, file, {
          contentType: mimeType,
          upsert: false,
        });

      if (storageError) {
        throw new Error(`Storage upload failed: ${storageError.message}`);
      }

      setProgress(50);
      setStatus("Registering swing...");

      const registerRes = await fetch("/api/swings/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          videoId,
          reportId,
          storagePath,
          originalFilename: file.name,
          mimeType,
          sizeBytes: file.size,
        }),
      });

      const registerData = await registerRes.json();
      if (!registerRes.ok) {
        throw new Error(registerData.error || "Failed to register swing");
      }

      setProgress(70);
      setStatus("Analyzing swing with AI video coach (1–3 min)...");

      const analyzeRes = await fetch(`/api/swings/${reportId}/analyze`, {
        method: "POST",
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
      router.push(`/swings/${reportId}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Something went wrong";
      if (message === "Failed to fetch") {
        setError(
          "Network error — is the dev server running? Run: cd apps/web && npm run dev"
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
        <h1 className="text-3xl font-semibold">Upload swing</h1>
        <p className="mt-1 text-[var(--color-muted)]">
          Film from face-on or down-the-line with your full body in frame.
        </p>

        <Card className="mt-8 space-y-6">
          <UploadDropzone onFileSelect={setFile} disabled={uploading} />
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
            disabled={!file || uploading}
            className="w-full"
          >
            {uploading ? "Processing..." : "Upload & analyze"}
          </Button>
        </Card>
      </main>
    </div>
  );
}
