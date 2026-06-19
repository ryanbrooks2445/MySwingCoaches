"use client";

import { useCallback, useState } from "react";
import { Upload } from "lucide-react";
import { cn } from "@/lib/utils";
import { ALLOWED_VIDEO_TYPES, ALLOWED_VIDEO_EXTENSIONS, MAX_VIDEO_SIZE_BYTES } from "@/lib/utils";

interface UploadDropzoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export function UploadDropzone({ onFileSelect, disabled }: UploadDropzoneProps) {
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validate = useCallback((file: File) => {
    const ext = file.name.split(".").pop()?.toLowerCase();
    const typeOk = ALLOWED_VIDEO_TYPES.includes(file.type);
    const extOk = ext ? ALLOWED_VIDEO_EXTENSIONS.includes(ext) : false;
    if (!typeOk && !extOk) {
      return "Only MP4 and MOV files are supported.";
    }
    if (file.size > MAX_VIDEO_SIZE_BYTES) {
      return "File must be under 100MB.";
    }
    return null;
  }, []);

  const handleFile = useCallback(
    (file: File) => {
      const err = validate(file);
      if (err) {
        setError(err);
        return;
      }
      setError(null);
      onFileSelect(file);
    },
    [onFileSelect, validate]
  );

  return (
    <div className="space-y-3">
      <label
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const file = e.dataTransfer.files[0];
          if (file) handleFile(file);
        }}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-8 py-16 transition-colors",
          dragOver
            ? "border-[var(--color-accent)] bg-[var(--color-accent-muted)]/30"
            : "border-[var(--color-border)] hover:border-[var(--color-muted)]",
          disabled && "pointer-events-none opacity-50"
        )}
      >
        <Upload className="mb-4 h-10 w-10 text-[var(--color-muted)]" />
        <p className="text-lg font-medium">Drop your swing video here</p>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          MP4 or MOV · max 100 MB · 30 seconds or shorter
        </p>
        <input
          type="file"
          accept="video/mp4,video/quicktime,.mp4,.mov"
          className="hidden"
          disabled={disabled}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />
      </label>
      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
}
