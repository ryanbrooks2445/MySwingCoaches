export interface GolferProfileFields {
  age: number | null;
  years_playing: number | null;
  physical_limitations: string | null;
  average_9_score: number | null;
  typical_miss: string | null;
  primary_goal: string | null;
}

export function isGolferProfileComplete(profile: GolferProfileFields): boolean {
  if (profile.age == null || profile.age < 5 || profile.age > 120) return false;
  if (profile.years_playing == null || profile.years_playing < 0 || profile.years_playing > 100) {
    return false;
  }
  const limits = (profile.physical_limitations ?? "").trim();
  if (limits.length < 3) return false;
  if (profile.average_9_score == null || profile.average_9_score < 25 || profile.average_9_score > 90) {
    return false;
  }
  if ((profile.typical_miss ?? "").trim().length < 3) return false;
  if ((profile.primary_goal ?? "").trim().length < 3) return false;
  return true;
}

export function validateGolferProfileInput(input: {
  age: string;
  years_playing: string;
  physical_limitations: string;
  no_physical_limitations: boolean;
  average_9_score: string;
  typical_miss: string;
  primary_goal: string;
}): { ok: true; data: GolferProfileFields } | { ok: false; error: string } {
  const age = parseInt(input.age, 10);
  if (Number.isNaN(age) || age < 5 || age > 120) {
    return { ok: false, error: "Enter your age (5–120)." };
  }

  const years = parseInt(input.years_playing, 10);
  if (Number.isNaN(years) || years < 0 || years > 100) {
    return { ok: false, error: "Enter years playing golf (0–100)." };
  }

  const limitations = input.no_physical_limitations
    ? "None reported"
    : input.physical_limitations.trim();

  if (!input.no_physical_limitations && limitations.length < 3) {
    return {
      ok: false,
      error: "Describe physical constraints (injuries, pain, mobility) or check “no major limitations.”",
    };
  }

  const average9 = parseInt(input.average_9_score, 10);
  if (Number.isNaN(average9) || average9 < 25 || average9 > 90) {
    return { ok: false, error: "Enter your average 9-hole score (25–90)." };
  }

  const typicalMiss = input.typical_miss.trim();
  if (typicalMiss.length < 3 || typicalMiss.length > 160) {
    return { ok: false, error: "Describe your typical miss in 3–160 characters." };
  }

  const primaryGoal = input.primary_goal.trim();
  if (primaryGoal.length < 3 || primaryGoal.length > 160) {
    return { ok: false, error: "Describe your main goal in 3–160 characters." };
  }

  return {
    ok: true,
    data: {
      age,
      years_playing: years,
      physical_limitations: limitations,
      average_9_score: average9,
      typical_miss: typicalMiss,
      primary_goal: primaryGoal,
    },
  };
}
