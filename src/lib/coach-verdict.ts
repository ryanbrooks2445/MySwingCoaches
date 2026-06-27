import type { CategoryRating, CoachVerdict } from "@/lib/types";

function normalizeOverallRating(raw: string): string {
  const text = raw.trim();
  if (!text) return "";
  if (/\/\s*10|out of\s*10/i.test(text)) return text;
  if (/^\d+(?:\.\d+)?$/.test(text)) return `${text}/10 overall`;
  return text;
}

function parseCategoryRating(line: string): CategoryRating | null {
  const text = line.trim();
  if (!text) return null;
  const match = text.match(/^(.+?):\s*(\d+(?:\.\d+)?(?:\s*\/\s*10|\s*out of\s*10)?)$/i);
  if (!match) return null;
  const label = match[1].trim();
  let rating = match[2].trim().replace(/\s+/g, "");
  if (!/\/10|outof10/i.test(rating)) {
    rating = `${rating}/10`;
  }
  return { label, rating };
}

function extractLabeledField(text: string, label: string): string {
  const pattern = new RegExp(
    `${label}\\s*:?\\s*(.+?)(?=(?:The big positive|Main issue|Best fix|Power:|Tempo:|Sequence|Overall|I'd rate|$))`,
    "is"
  );
  const match = text.match(pattern);
  return match?.[1]?.replace(/\s+/g, " ").trim().replace(/[.\s]+$/, "") ?? "";
}

function extractCategoryRatings(text: string): CategoryRating[] {
  const ratings: CategoryRating[] = [];
  for (const chunk of text.split(/[\n.]+/)) {
    const parsed = parseCategoryRating(chunk.trim());
    if (parsed) ratings.push(parsed);
  }
  return ratings.slice(0, 6);
}

function extractQuickVerdictSection(analysis: string): string {
  const match = analysis.match(
    /Quick coach verdict\s*([\s\S]*?)(?=\n\s*Full coach-style analysis|\n\s*What's working|\n\s*Main swing fault|\Z)/i
  );
  return match?.[1]?.trim() ?? "";
}

export function parseCoachVerdictFromAnalysis(
  analysis: string,
  fallback?: Partial<CoachVerdict>
): CoachVerdict | null {
  const quickSection = extractQuickVerdictSection(analysis);
  const searchText = quickSection || analysis;

  const ratingMatch = searchText.match(
    /(?:I'd rate this swing|I would rate this swing)\s*([^.\n]+)/i
  );
  const overall_rating = normalizeOverallRating(
    ratingMatch?.[1]?.trim() || fallback?.overall_rating || ""
  );

  const biggest_positive =
    extractLabeledField(searchText, "The big positive") || fallback?.biggest_positive || "";
  const main_issue =
    extractLabeledField(searchText, "Main issue") || fallback?.main_issue || "";
  const best_fix =
    extractLabeledField(searchText, "Best fix") || fallback?.best_fix || "";

  const category_ratings =
    extractCategoryRatings(searchText).length > 0
      ? extractCategoryRatings(searchText)
      : fallback?.category_ratings ?? [];

  if (
    !overall_rating &&
    !biggest_positive &&
    !main_issue &&
    !best_fix &&
    category_ratings.length === 0
  ) {
    return null;
  }

  return {
    overall_rating,
    biggest_positive,
    main_issue,
    best_fix,
    category_ratings,
  };
}

export function resolveCoachVerdict(
  content: { coach_verdict?: CoachVerdict | null; pga_analysis?: string | null; main_fix?: string | null },
  simplified?: { pga_analysis?: string; main_fix?: string }
): CoachVerdict | null {
  if (content.coach_verdict?.overall_rating || content.coach_verdict?.main_issue) {
    return content.coach_verdict;
  }

  const analysis = simplified?.pga_analysis || content.pga_analysis || "";
  return parseCoachVerdictFromAnalysis(analysis, {
    best_fix: simplified?.main_fix || content.main_fix || "",
  });
}

export function overallRatingNumber(rating: string): string | null {
  const match = rating.match(/(\d+(?:\.\d+)?)/);
  return match?.[1] ?? null;
}
