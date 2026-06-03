"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { AppNav } from "@/components/AppNav";
import { UploadDropzone } from "@/components/UploadDropzone";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [handedness, setHandedness] = useState("right");
  const [skillLevel, setSkillLevel] = useState("intermediate");
  const [cameraAngle, setCameraAngle] = useState("unknown");
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setError(null);
    setStatus("Uploading video...");
    setProgress(10);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("handedness", handedness);
    formData.append("skillLevel", skillLevel);
    formData.append("cameraAngle", cameraAngle);

    try {
      setProgress(30);
      const res = await fetch("/api/swings/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Upload failed");

      setProgress(60);
      setStatus("Analyzing swing...");

      const analyzeRes = await fetch(`/api/swings/${data.reportId}/analyze`, { method: "POST" });
      const analyzeData = await analyzeRes.json();
      if (!analyzeRes.ok) throw new Error(analyzeData.error || "Analysis failed");

      setProgress(100);
      setStatus("Complete!");
      router.push(`/swings/${data.reportId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
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

          <div className="grid gap-4 sm:grid-cols-3">
            <label className="space-y-1 text-sm">
              <span className="text-[var(--color-muted)]">Handedness</span>
              <select
                value={handedness}
                onChange={(e) => setHandedness(e.target.value)}
                className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2"
              >
                <option value="right">Right</option>
                <option value="left">Left</option>
              </select>
            </label>
            <label className="space-y-1 text-sm">
              <span className="text-[var(--color-muted)]">Skill level</span>
              <select
                value={skillLevel}
                onChange={(e) => setSkillLevel(e.target.value)}
                className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2"
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </label>
            <label className="space-y-1 text-sm">
              <span className="text-[var(--color-muted)]">Camera angle</span>
              <select
                value={cameraAngle}
                onChange={(e) => setCameraAngle(e.target.value)}
                className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2"
              >
                <option value="unknown">Unknown</option>
                <option value="face-on">Face-on</option>
                <option value="down-the-line">Down-the-line</option>
              </select>
            </label>
          </div>

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
