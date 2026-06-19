import assert from "node:assert/strict";
import test from "node:test";
import {
  getNextAnalysisPrice,
  qualifiesForIntroPrice,
} from "../src/lib/pricing.ts";
import { validateGolferProfileInput } from "../src/lib/player-profile.ts";

test("intro price applies only before purchase or completed use", () => {
  assert.equal(qualifiesForIntroPrice(0, 0), true);
  assert.equal(qualifiesForIntroPrice(0, 1), false);
  assert.equal(qualifiesForIntroPrice(1, 1), false);
  assert.equal(getNextAnalysisPrice(0, 0), 9.99);
  assert.equal(getNextAnalysisPrice(0, 1), 19.99);
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
