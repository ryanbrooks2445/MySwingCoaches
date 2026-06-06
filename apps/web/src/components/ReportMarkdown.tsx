"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

function stripMarkdownHeadings(text: string): string {
  return text.replace(/^#{1,6}\s+/gm, "").replace(/^SECTION:\s*/gim, "");
}

function formatInline(text: string, pillShortBold = false): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      const inner = part.slice(2, -2);
      if (pillShortBold && inner.length <= 28 && !inner.includes("·")) {
        return (
          <span
            key={i}
            className="mr-1.5 mb-1 inline-block rounded-full bg-sky-500/15 px-2.5 py-0.5 text-xs font-semibold text-sky-800 dark:text-sky-200"
          >
            {inner}
          </span>
        );
      }
      return (
        <strong key={i} className="font-semibold text-[var(--color-foreground)]">
          {inner}
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
  /** body = default; phases = pill-style bold labels for setup-to-finish */
  variant?: "body" | "phases";
}

export function ReportMarkdown({ content, className, variant = "body" }: ReportMarkdownProps) {
  const normalized = stripMarkdownHeadings(content);
  const blocks = normalized.split(/\n\n+/);
  const pillShortBold = variant === "phases";

  return (
    <div className={cn("space-y-3 text-sm leading-relaxed text-[var(--color-muted)]", className)}>
      {blocks.map((block, blockIdx) => {
        const lines = block.split("\n").filter((l) => l.trim());
        if (lines.length === 0) return null;

        const allBullets = lines.every(isBullet);
        const allNumbered = lines.every(isNumbered);

        if (allBullets) {
          return (
            <ul key={blockIdx} className="list-disc space-y-2 pl-5 marker:text-[var(--color-accent)]">
              {lines.map((line, i) => (
                <li key={i}>{formatInline(stripBullet(line), pillShortBold)}</li>
              ))}
            </ul>
          );
        }

        if (allNumbered) {
          return (
            <ol key={blockIdx} className="list-decimal space-y-2 pl-5 marker:font-semibold marker:text-[var(--color-accent)]">
              {lines.map((line, i) => (
                <li key={i}>{formatInline(stripBullet(line), pillShortBold)}</li>
              ))}
            </ol>
          );
        }

        if (lines.length === 1 && lines[0].startsWith("**") && lines[0].endsWith("**")) {
          return (
            <p key={blockIdx} className="text-base font-semibold text-[var(--color-foreground)]">
              {formatInline(lines[0], pillShortBold)}
            </p>
          );
        }

        return (
          <p key={blockIdx}>
            {lines.map((line, i) => (
              <span key={i}>
                {i > 0 && <br />}
                {formatInline(line, pillShortBold)}
              </span>
            ))}
          </p>
        );
      })}
    </div>
  );
}
