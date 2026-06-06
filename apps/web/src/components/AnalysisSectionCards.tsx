"use client";

import { ReportMarkdown } from "@/components/ReportMarkdown";
import { getSectionTheme, parseAnalysisSections } from "@/lib/analysis-sections";
import { cn } from "@/lib/utils";

interface AnalysisSectionCardsProps {
  content: string;
  className?: string;
}

export function AnalysisSectionCards({ content, className }: AnalysisSectionCardsProps) {
  const sections = parseAnalysisSections(content);

  return (
    <div className={cn("space-y-4", className)}>
      {sections.map((section, idx) => {
        const theme = getSectionTheme(section.title);
        const isSetupSection = section.title.toLowerCase().includes("setup");

        return (
          <article
            key={`${section.title}-${idx}`}
            className={cn(
              "overflow-hidden rounded-2xl border bg-gradient-to-br p-[1px] shadow-sm",
              theme.border
            )}
          >
            <div
              className={cn(
                "rounded-[calc(1rem-1px)] bg-[var(--color-card)] bg-gradient-to-br px-5 py-4",
                theme.gradient
              )}
            >
              <header className="mb-3 flex items-center gap-3">
                <span
                  className={cn(
                    "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-base",
                    theme.accentClass
                  )}
                  aria-hidden
                >
                  {theme.emoji}
                </span>
                <h3 className={cn("text-base font-semibold tracking-tight sm:text-lg", theme.titleClass)}>
                  {section.title}
                </h3>
              </header>
              <ReportMarkdown
                content={section.body}
                variant={isSetupSection ? "phases" : "body"}
                className="text-[15px] leading-relaxed text-[var(--color-foreground)]/90"
              />
            </div>
          </article>
        );
      })}
    </div>
  );
}
