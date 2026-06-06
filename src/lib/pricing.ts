export const PRICE_FIRST_ANALYSIS = 9.99;
export const PRICE_PER_ANALYSIS = 19.99;
export const PRICE_FIRST_ANALYSIS_DISPLAY = "$9.99";
export const PRICE_PER_ANALYSIS_DISPLAY = "$19.99";

export const SWING_MODES = ["full_swing", "chipping", "putting"] as const;
export type SwingMode = (typeof SWING_MODES)[number];

export const SWING_MODE_LABELS: Record<SwingMode, string> = {
  full_swing: "Full swing",
  chipping: "Chipping",
  putting: "Putting",
};

export const SWING_MODE_HINTS: Record<SwingMode, string> = {
  full_swing: "Face-on or down-the-line. Full body in frame.",
  chipping: "Film the strike zone — ball, club, hands. 10–30 yard chip.",
  putting: "Down-the-line or face-on. Ball, putter, and stroke in frame.",
};

/** Intro price only before any purchase or completed analysis. */
export function qualifiesForIntroPrice(analysesUsed: number, analysesLimit: number): boolean {
  return analysesUsed === 0 && analysesLimit === 0;
}

export function getNextAnalysisPrice(analysesUsed: number, analysesLimit: number): number {
  return qualifiesForIntroPrice(analysesUsed, analysesLimit)
    ? PRICE_FIRST_ANALYSIS
    : PRICE_PER_ANALYSIS;
}

export function formatPrice(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

export function getNextAnalysisPriceDisplay(analysesUsed: number, analysesLimit: number): string {
  return formatPrice(getNextAnalysisPrice(analysesUsed, analysesLimit));
}
