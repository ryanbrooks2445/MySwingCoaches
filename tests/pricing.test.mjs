import assert from "node:assert/strict";
import test from "node:test";
import {
  PRICE_PER_ANALYSIS,
  PRICE_PER_ANALYSIS_DISPLAY,
  PRICE_PER_ANALYSIS_CENTS,
  getNextAnalysisPrice,
  getNextAnalysisPriceDisplay,
} from "../src/lib/pricing.ts";
import { validateGolferProfileInput } from "../src/lib/player-profile.ts";

test("swing analyses use one flat price", () => {
  assert.equal(PRICE_PER_ANALYSIS, 19.99);
  assert.equal(PRICE_PER_ANALYSIS_DISPLAY, "$19.99");
  assert.equal(PRICE_PER_ANALYSIS_CENTS, 1999);
  assert.equal(getNextAnalysisPrice(0, 0), 19.99);
  assert.equal(getNextAnalysisPrice(0, 1), 19.99);
  assert.equal(getNextAnalysisPrice(4, 7), 19.99);
  assert.equal(getNextAnalysisPriceDisplay(4, 7), "$19.99");
});

test("golfer profile requires scoring context and a goal", () => {
  const result = validateGolferProfileInput({
    age: "52",
    years_playing: "5",
    physical_limitations: "",
    no_physical_limitations: true,
    average_9_score: "58",
    typical_miss: "Thin shots",
    primary_goal: "Break 50",
  });
  assert.equal(result.ok, true);
});

test("golfer profile rejects invalid scoring context", () => {
  const result = validateGolferProfileInput({
    age: "52",
    years_playing: "5",
    physical_limitations: "",
    no_physical_limitations: true,
    average_9_score: "120",
    typical_miss: "Thin shots",
    primary_goal: "Break 50",
  });
  assert.equal(result.ok, false);
});
