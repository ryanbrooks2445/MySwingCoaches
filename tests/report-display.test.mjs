import assert from "node:assert/strict";
import test from "node:test";
import {
  cameraVerifiedSummary,
  filterVisibleEvidence,
  isVisibleEvidenceLine,
  resolveBestFix,
} from "../src/lib/report-display.ts";

const baseAdvanced = {
  evidence_metrics: [],
  root_cause: "",
  symptom: "Pull-hook ball flight.",
  foundational_missing_piece: "",
  secondary_fix: "",
  optional_fix: "",
  chain_reaction: "",
  why_it_caused_the_miss: "",
  confidence_score: 0.8,
};

test("filters not-visible evidence lines", () => {
  assert.equal(isVisibleEvidenceLine("address: Not visible"), false);
  assert.equal(isVisibleEvidenceLine("takeaway: not visible"), false);
  assert.equal(
    isVisibleEvidenceLine("Lead arm is visibly bent at the top of the backswing."),
    true
  );
  assert.deepEqual(
    filterVisibleEvidence([
      "address: Not visible",
      "top: Not visible",
      "Lead arm bent at the top, pulling hands too close.",
    ]),
    ["Lead arm bent at the top, pulling hands too close."]
  );
});

test("resolves best fix from coach verdict first", () => {
  const report = {
    pga_analysis: "What's working\nSolid posture.",
    main_fix: "Fallback fix",
    tips_and_feels: [],
    drills: [],
    next_swing_check: "Film face-on.",
    coach_verdict: {
      overall_rating: "7/10",
      category_ratings: [],
      biggest_positive: "Excellent posture at address.",
      main_issue: "Lead arm collapses at the top.",
      best_fix: "Keep your lead arm straighter during the backswing.",
    },
    advanced_details: baseAdvanced,
  };

  assert.equal(resolveBestFix(report), "Keep your lead arm straighter during the backswing.");

  const summary = cameraVerifiedSummary(report, resolveBestFix(report));
  assert.equal(summary.flaw, "Lead arm collapses at the top.");
  assert.equal(summary.working, "Excellent posture at address.");
  assert.equal(summary.impact, "Pull-hook ball flight.");
});
