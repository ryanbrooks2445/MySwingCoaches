import { getNextAnalysisPriceDisplay, PRICE_ANNUAL_UNLIMITED_DISPLAY } from "@/lib/pricing";
import type { Subscription, SubscriptionPlan } from "@/lib/types";

const UNLIMITED_PLANS: SubscriptionPlan[] = ["serious", "unlimited_annual"];

export function hasUnlimitedAccess(sub: Subscription): boolean {
  if (sub.analyses_limit !== -1) return false;
  if (sub.status !== "active") return false;
  if (!UNLIMITED_PLANS.includes(sub.plan)) return false;
  if (sub.period_end) {
    return new Date(sub.period_end).getTime() > Date.now();
  }
  return sub.plan === "serious";
}

export function analysisCreditsRemaining(sub: Subscription): number | "unlimited" {
  if (hasUnlimitedAccess(sub)) return "unlimited";
  return Math.max(0, sub.analyses_limit - sub.analyses_used);
}

export function hasActiveAnnualSubscription(sub: Subscription): boolean {
  return sub.plan === "unlimited_annual" && hasUnlimitedAccess(sub);
}

export function noCreditsMessage(sub: Subscription): string {
  const price = getNextAnalysisPriceDisplay(sub.analyses_used, sub.analyses_limit);
  return `No analyses left. Purchase one for ${price} or subscribe for ${PRICE_ANNUAL_UNLIMITED_DISPLAY}/year on the pricing page.`;
}
