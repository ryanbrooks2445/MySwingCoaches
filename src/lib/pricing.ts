export const PRICE_PER_ANALYSIS = 19.99;
export const PRICE_PER_ANALYSIS_DISPLAY = "$19.99";
export const PRICE_PER_ANALYSIS_CENTS = 1999;

export const PRICE_ANNUAL_UNLIMITED = 99;
export const PRICE_ANNUAL_UNLIMITED_DISPLAY = "$99";
export const PRICE_ANNUAL_UNLIMITED_CENTS = 9900;

export const PRODUCT_SWING_UPLOAD = "swing_upload" as const;
export const PRODUCT_ANNUAL_UNLIMITED = "annual_unlimited" as const;
export type CheckoutProduct = typeof PRODUCT_SWING_UPLOAD | typeof PRODUCT_ANNUAL_UNLIMITED;

/** @deprecated Use PRICE_PER_ANALYSIS — kept for existing imports */
export const PRICE_FIRST_ANALYSIS = PRICE_PER_ANALYSIS;
export const PRICE_FIRST_ANALYSIS_DISPLAY = PRICE_PER_ANALYSIS_DISPLAY;

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

export function getNextAnalysisPrice(
  analysesUsed?: number,
  analysesLimit?: number
): number {
  void analysesUsed;
  void analysesLimit;
  return PRICE_PER_ANALYSIS;
}

export function formatPrice(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

export function getNextAnalysisPriceDisplay(
  analysesUsed?: number,
  analysesLimit?: number
): string {
  return formatPrice(getNextAnalysisPrice(analysesUsed, analysesLimit));
}
