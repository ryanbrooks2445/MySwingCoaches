"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

function formatInline(text: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-[var(--color-foreground)]">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
}

function isBullet(line: string): boolean {
  return /^[-*•]\s+/.test(line.trim());
}

function isNumbered(line: string): boolean {
  return /^\d+\.\s+/.test(line.trim());
}

function stripBullet(line: string): string {
  return line.trim().replace(/^[-*•]\s+/, "").replace(/^\d+\.\s+/, "");
}

interface ReportMarkdownProps {
  content: string;
  className?: string;
}

export function ReportMarkdown({ content, className }: ReportMarkdownProps) {
  const blocks = content.split(/\n\n+/);

  return (
    <div className={cn("space-y-3 text-sm leading-relaxed text-[var(--color-muted)]", className)}>
      {blocks.map((block, blockIdx) => {
        const lines = block.split("\n").filter((l) => l.trim());
        if (lines.length === 0) return null;

        const allBullets = lines.every(isBullet);
        const allNumbered = lines.every(isNumbered);

        if (allBullets) {
          return (
            <ul key={blockIdx} className="list-disc space-y-1.5 pl-5">
              {lines.map((line, i) => (
                <li key={i}>{formatInline(stripBullet(line))}</li>
              ))}
            </ul>
          );
        }

        if (allNumbered) {
          return (
            <ol key={blockIdx} className="list-decimal space-y-1.5 pl-5">
              {lines.map((line, i) => (
                <li key={i}>{formatInline(stripBullet(line))}</li>
              ))}
            </ol>
          );
        }

        if (lines.length === 1 && lines[0].startsWith("**") && lines[0].endsWith("**")) {
          return (
            <p key={blockIdx} className="text-base font-semibold text-[var(--color-foreground)]">
              {formatInline(lines[0])}
            </p>
          );
        }

        return (
          <p key={blockIdx}>
            {lines.map((line, i) => (
              <span key={i}>
                {i > 0 && <br />}
                {formatInline(line)}
              </span>
            ))}
          </p>
        );
      })}
    </div>
  );
}
