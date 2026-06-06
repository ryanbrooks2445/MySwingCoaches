export interface AnalysisSection {
  title: string;
  body: string;
}

export interface SectionTheme {
  emoji: string;
  gradient: string;
  border: string;
  titleClass: string;
  accentClass: string;
}

const KNOWN_SECTION_TITLES = [
  "what's working",
  "setup to finish",
  "the missing piece",
  "what changes when you unlock it",
  "what to keep doing",
  "your ceiling at this level",
];

function isKnownSectionTitle(line: string): boolean {
  const t = line.trim().toLowerCase();
  return KNOWN_SECTION_TITLES.some((title) => t === title);
}

function stripHeadingPrefix(line: string): string {
  return line
    .trim()
    .replace(/^#{1,6}\s+/, "")
    .replace(/^SECTION:\s*/i, "")
    .trim();
}

function isSectionHeading(line: string): boolean {
  const t = line.trim();
  return /^#{1,6}\s+/.test(t) || /^SECTION:\s*/i.test(t);
}

/** Split pga_analysis into titled sections (supports ### and legacy plain text). */
export function parseAnalysisSections(content: string): AnalysisSection[] {
  const text = content.trim();
  if (!text) return [{ title: "Your analysis", body: "" }];

  const lines = text.split("\n");
  const sections: AnalysisSection[] = [];
  let currentTitle: string | null = null;
  let currentBody: string[] = [];

  const flush = () => {
    if (currentTitle === null && currentBody.length === 0) return;
    sections.push({
      title: currentTitle ?? "Your analysis",
      body: currentBody.join("\n").trim(),
    });
    currentBody = [];
  };

  for (const line of lines) {
    if (isSectionHeading(line) || isKnownSectionTitle(line)) {
      flush();
      currentTitle = isSectionHeading(line) ? stripHeadingPrefix(line) : line.trim();
    } else {
      currentBody.push(line);
    }
  }
  flush();

  if (sections.length === 0) {
    return [{ title: "Your analysis", body: text.replace(/^#{1,6}\s+/gm, "") }];
  }

  return sections.filter((s) => s.title || s.body);
}

export function normalizeSectionKey(title: string): string {
  const t = title.toLowerCase();
  if (t.includes("working")) return "working";
  if (t.includes("setup") && t.includes("finish")) return "setup";
  if (t.includes("missing piece")) return "missing";
  if (t.includes("unlock") || t.includes("changes when")) return "unlock";
  if (t.includes("keep doing")) return "keep";
  if (t.includes("ceiling")) return "ceiling";
  return "default";
}

const THEMES: Record<string, SectionTheme> = {
  working: {
    emoji: "✓",
    gradient: "from-emerald-500/25 via-emerald-400/10 to-transparent",
    border: "border-emerald-500/45",
    titleClass: "text-emerald-700 dark:text-emerald-300",
    accentClass: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300",
  },
  setup: {
    emoji: "◎",
    gradient: "from-sky-500/20 via-cyan-400/10 to-transparent",
    border: "border-sky-500/40",
    titleClass: "text-sky-700 dark:text-sky-300",
    accentClass: "bg-sky-500/15 text-sky-800 dark:text-sky-200",
  },
  missing: {
    emoji: "🔑",
    gradient: "from-amber-500/25 via-orange-400/10 to-transparent",
    border: "border-amber-500/45",
    titleClass: "text-amber-800 dark:text-amber-300",
    accentClass: "bg-amber-500/15 text-amber-900 dark:text-amber-200",
  },
  unlock: {
    emoji: "🚀",
    gradient: "from-violet-500/25 via-fuchsia-400/10 to-transparent",
    border: "border-violet-500/45",
    titleClass: "text-violet-700 dark:text-violet-300",
    accentClass: "bg-violet-500/15 text-violet-800 dark:text-violet-200",
  },
  keep: {
    emoji: "💪",
    gradient: "from-teal-500/25 via-emerald-400/10 to-transparent",
    border: "border-teal-500/45",
    titleClass: "text-teal-700 dark:text-teal-300",
    accentClass: "bg-teal-500/15 text-teal-800 dark:text-teal-200",
  },
  ceiling: {
    emoji: "⭐",
    gradient: "from-yellow-500/30 via-amber-400/15 to-transparent",
    border: "border-yellow-500/45",
    titleClass: "text-yellow-800 dark:text-yellow-300",
    accentClass: "bg-yellow-500/15 text-yellow-900 dark:text-yellow-200",
  },
  default: {
    emoji: "•",
    gradient: "from-[var(--color-accent)]/15 to-transparent",
    border: "border-[var(--color-accent)]/30",
    titleClass: "text-[var(--color-foreground)]",
    accentClass: "bg-[var(--color-accent)]/10 text-[var(--color-accent)]",
  },
};

export function getSectionTheme(title: string): SectionTheme {
  return THEMES[normalizeSectionKey(title)] ?? THEMES.default;
}

const TIP_ACCENTS = [
  "border-l-emerald-500 bg-emerald-500/5",
  "border-l-sky-500 bg-sky-500/5",
  "border-l-violet-500 bg-violet-500/5",
  "border-l-amber-500 bg-amber-500/5",
];

export function tipAccentClass(index: number): string {
  return TIP_ACCENTS[index % TIP_ACCENTS.length];
}
