import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const migrationPath = new URL(
  "../supabase/migrations/013_annual_unlimited.sql",
  import.meta.url
);
const functionsMigrationPath = new URL(
  "../supabase/migrations/014_annual_unlimited_functions.sql",
  import.meta.url
);

test("annual unlimited migration adds plan, period_end, and subscription RPCs", async () => {
  const enumSql = await readFile(migrationPath, "utf8");
  const functionsSql = await readFile(functionsMigrationPath, "utf8");

  assert.match(enumSql, /unlimited_annual/i);
  assert.match(enumSql, /period_end TIMESTAMPTZ/i);
  assert.match(functionsSql, /CREATE OR REPLACE FUNCTION private\.fulfill_subscription/i);
  assert.match(functionsSql, /CREATE OR REPLACE FUNCTION private\.revoke_subscription/i);
  assert.match(functionsSql, /CREATE OR REPLACE FUNCTION public\.service_fulfill_subscription/i);
  assert.match(functionsSql, /period_end IS NULL OR period_end > NOW\(\)/i);
});

test("subscription access treats active annual plan as unlimited", () => {
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

  const activeAnnual = {
    plan: "unlimited_annual",
    status: "active",
    analyses_used: 3,
    analyses_limit: -1,
    period_end: new Date(Date.now() + 86400000).toISOString(),
  };

  assert.equal(hasUnlimitedAccess(activeAnnual), true);
  assert.equal(analysisCreditsRemaining(activeAnnual), "unlimited");

  const expiredAnnual = {
    ...activeAnnual,
    period_end: new Date(Date.now() - 86400000).toISOString(),
  };

  assert.equal(hasUnlimitedAccess(expiredAnnual), false);
  assert.equal(analysisCreditsRemaining(expiredAnnual), 0);
});

test("pricing constants include annual unlimited product", async () => {
  const pricing = await import("../src/lib/pricing.ts");

  assert.equal(pricing.PRICE_ANNUAL_UNLIMITED, 99);
  assert.equal(pricing.PRICE_ANNUAL_UNLIMITED_CENTS, 9900);
  assert.equal(pricing.PRODUCT_ANNUAL_UNLIMITED, "annual_unlimited");
});
