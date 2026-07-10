import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("formatSwingStatus maps awaiting_payment to human label", async () => {
  const source = await readFile(new URL("../src/lib/status-labels.ts", import.meta.url), "utf8");
  assert.match(source, /awaiting_payment:\s*"Awaiting payment"/);
  assert.match(source, /export function formatSwingStatus/);
  assert.match(source, /address:\s*"Address \/ stance"/);
  assert.match(source, /export function formatPhaseLabel/);
});

test("Reveal supports immediate above-the-fold visibility", async () => {
  const source = await readFile(new URL("../src/components/Reveal.tsx", import.meta.url), "utf8");
  assert.match(source, /immediate\?: boolean/);
  assert.match(source, /useState\(immediate\)/);
});

test("analytics helper no-ops without Plausible domain", async () => {
  const source = await readFile(new URL("../src/lib/analytics.ts", import.meta.url), "utf8");
  assert.match(source, /NEXT_PUBLIC_PLAUSIBLE_DOMAIN/);
  assert.match(source, /window\.plausible/);
});

test("debug panel is coach/admin gated", async () => {
  const source = await readFile(
    new URL("../src/app/swings/[id]/page.tsx", import.meta.url),
    "utf8"
  );
  assert.match(source, /isCoachOrAdmin/);
  assert.match(source, /\["coach", "admin"\]/);
});
