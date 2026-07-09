import assert from "node:assert/strict";
import test from "node:test";
import { PRICE_ANNUAL_UNLIMITED_DISPLAY, getNextAnalysisPriceDisplay } from "../src/lib/pricing.ts";

// Functions under test (duplicated inline because Node's --experimental-strip-types
// cannot resolve tsconfig path aliases like @/lib/pricing).
// Kept in sync with src/lib/subscription-access.ts.

const UNLIMITED_PLANS = new Set(["serious", "unlimited_annual"]);

function hasUnlimitedAccess(sub) {
  if (sub.analyses_limit !== -1) return false;
  if (sub.status !== "active") return false;
  if (!UNLIMITED_PLANS.has(sub.plan)) return false;
  if (sub.period_end) {
    return new Date(sub.period_end).getTime() > Date.now();
  }
  return sub.plan === "serious";
}

function analysisCreditsRemaining(sub) {
  if (hasUnlimitedAccess(sub)) return "unlimited";
  return Math.max(0, sub.analyses_limit - sub.analyses_used);
}

function hasActiveAnnualSubscription(sub) {
  return sub.plan === "unlimited_annual" && hasUnlimitedAccess(sub);
}

function noCreditsMessage(sub) {
  const price = getNextAnalysisPriceDisplay(sub.analyses_used, sub.analyses_limit);
  return `No analyses left. Purchase one for ${price} or subscribe for ${PRICE_ANNUAL_UNLIMITED_DISPLAY}/year on the pricing page.`;
}

// ---------------------------------------------------------------------------
// Test helpers
// ---------------------------------------------------------------------------

function makeSub(overrides = {}) {
  return {
    id: "test-id",
    user_id: "test-user",
    plan: "free",
    status: "active",
    analyses_used: 0,
    analyses_limit: 5,
    period_start: null,
    period_end: null,
    stripe_customer_id: null,
    stripe_subscription_id: null,
    coach_review_addon: false,
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// hasUnlimitedAccess
// ---------------------------------------------------------------------------

test("hasUnlimitedAccess — returns false when analyses_limit is not -1", () => {
  const sub = makeSub({ plan: "unlimited_annual", analyses_limit: 10, status: "active" });
  assert.equal(hasUnlimitedAccess(sub), false);
});

test("hasUnlimitedAccess — returns false when status is not active", () => {
  const sub = makeSub({ plan: "unlimited_annual", analyses_limit: -1, status: "canceled" });
  assert.equal(hasUnlimitedAccess(sub), false);
});

test("hasUnlimitedAccess — returns false when plan is not in unlimited plans", () => {
  const sub = makeSub({ plan: "free", analyses_limit: -1, status: "active" });
  assert.equal(hasUnlimitedAccess(sub), false);
});

test("hasUnlimitedAccess — returns false for player plan", () => {
  const sub = makeSub({ plan: "player", analyses_limit: -1, status: "active" });
  assert.equal(hasUnlimitedAccess(sub), false);
});

test("hasUnlimitedAccess — returns true for unlimited_annual with future period_end", () => {
  const sub = makeSub({
    plan: "unlimited_annual",
    analyses_limit: -1,
    status: "active",
    period_end: new Date(Date.now() + 86400000).toISOString(),
  });
  assert.equal(hasUnlimitedAccess(sub), true);
});

test("hasUnlimitedAccess — returns false for unlimited_annual with past period_end", () => {
  const sub = makeSub({
    plan: "unlimited_annual",
    analyses_limit: -1,
    status: "active",
    period_end: new Date(Date.now() - 86400000).toISOString(),
  });
  assert.equal(hasUnlimitedAccess(sub), false);
});

test("hasUnlimitedAccess — returns false for unlimited_annual with no period_end", () => {
  // Falls through to sub.plan === "serious" check, which is false for unlimited_annual
  const sub = makeSub({
    plan: "unlimited_annual",
    analyses_limit: -1,
    status: "active",
    period_end: null,
  });
  assert.equal(hasUnlimitedAccess(sub), false);
});

test("hasUnlimitedAccess — returns true for serious plan with no period_end", () => {
  const sub = makeSub({
    plan: "serious",
    analyses_limit: -1,
    status: "active",
    period_end: null,
  });
  assert.equal(hasUnlimitedAccess(sub), true);
});

test("hasUnlimitedAccess — returns true for serious plan with future period_end", () => {
  const sub = makeSub({
    plan: "serious",
    analyses_limit: -1,
    status: "active",
    period_end: new Date(Date.now() + 86400000).toISOString(),
  });
  assert.equal(hasUnlimitedAccess(sub), true);
});

test("hasUnlimitedAccess — returns false for serious plan with past period_end", () => {
  const sub = makeSub({
    plan: "serious",
    analyses_limit: -1,
    status: "active",
    period_end: new Date(Date.now() - 86400000).toISOString(),
  });
  assert.equal(hasUnlimitedAccess(sub), false);
});

// ---------------------------------------------------------------------------
// analysisCreditsRemaining
// ---------------------------------------------------------------------------

test("analysisCreditsRemaining — returns 'unlimited' for unlimited access", () => {
  const sub = makeSub({
    plan: "unlimited_annual",
    analyses_limit: -1,
    status: "active",
    period_end: new Date(Date.now() + 86400000).toISOString(),
  });
  assert.equal(analysisCreditsRemaining(sub), "unlimited");
});

test("analysisCreditsRemaining — returns positive remaining credits", () => {
  const sub = makeSub({ analyses_limit: 10, analyses_used: 3 });
  assert.equal(analysisCreditsRemaining(sub), 7);
});

test("analysisCreditsRemaining — returns 0 when credits are exactly used up", () => {
  const sub = makeSub({ analyses_limit: 5, analyses_used: 5 });
  assert.equal(analysisCreditsRemaining(sub), 0);
});

test("analysisCreditsRemaining — returns 0 when credits are overused (Math.max floor)", () => {
  const sub = makeSub({ analyses_limit: 5, analyses_used: 8 });
  assert.equal(analysisCreditsRemaining(sub), 0);
});

test("analysisCreditsRemaining — returns 0 when limit is 0", () => {
  const sub = makeSub({ analyses_limit: 0, analyses_used: 0 });
  assert.equal(analysisCreditsRemaining(sub), 0);
});

// ---------------------------------------------------------------------------
// hasActiveAnnualSubscription
// ---------------------------------------------------------------------------

test("hasActiveAnnualSubscription — returns true for active unlimited_annual", () => {
  const sub = makeSub({
    plan: "unlimited_annual",
    analyses_limit: -1,
    status: "active",
    period_end: new Date(Date.now() + 86400000).toISOString(),
  });
  assert.equal(hasActiveAnnualSubscription(sub), true);
});

test("hasActiveAnnualSubscription — returns false for expired unlimited_annual", () => {
  const sub = makeSub({
    plan: "unlimited_annual",
    analyses_limit: -1,
    status: "active",
    period_end: new Date(Date.now() - 86400000).toISOString(),
  });
  assert.equal(hasActiveAnnualSubscription(sub), false);
});

test("hasActiveAnnualSubscription — returns false for serious plan (not annual)", () => {
  const sub = makeSub({
    plan: "serious",
    analyses_limit: -1,
    status: "active",
    period_end: null,
  });
  assert.equal(hasActiveAnnualSubscription(sub), false);
});

test("hasActiveAnnualSubscription — returns false for free plan", () => {
  const sub = makeSub({ plan: "free", analyses_limit: 5, status: "active" });
  assert.equal(hasActiveAnnualSubscription(sub), false);
});

test("hasActiveAnnualSubscription — returns false for canceled unlimited_annual", () => {
  const sub = makeSub({
    plan: "unlimited_annual",
    analyses_limit: -1,
    status: "canceled",
    period_end: new Date(Date.now() + 86400000).toISOString(),
  });
  assert.equal(hasActiveAnnualSubscription(sub), false);
});

// ---------------------------------------------------------------------------
// noCreditsMessage
// ---------------------------------------------------------------------------

test("noCreditsMessage — returns expected message format", () => {
  const sub = makeSub({ analyses_used: 5, analyses_limit: 5 });
  const msg = noCreditsMessage(sub);
  assert.match(msg, /No analyses left/);
  assert.match(msg, /\$19\.99/);
  assert.match(msg, /\$99\/year/);
  assert.match(msg, /pricing page/);
});

test("noCreditsMessage — shows correct price even when limit is 0", () => {
  const sub = makeSub({ analyses_used: 0, analyses_limit: 0 });
  const msg = noCreditsMessage(sub);
  assert.match(msg, /\$19\.99/);
});

test("noCreditsMessage — shows correct price when over limit", () => {
  const sub = makeSub({ analyses_used: 10, analyses_limit: 5 });
  const msg = noCreditsMessage(sub);
  assert.match(msg, /\$19\.99/);
});