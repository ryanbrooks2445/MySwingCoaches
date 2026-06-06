export interface GolferProfileFields {
  age: number | null;
  years_playing: number | null;
  physical_limitations: string | null;
}

export function isGolferProfileComplete(profile: GolferProfileFields): boolean {
  if (profile.age == null || profile.age < 5 || profile.age > 120) return false;
  if (profile.years_playing == null || profile.years_playing < 0 || profile.years_playing > 100) {
    return false;
  }
  const limits = (profile.physical_limitations ?? "").trim();
  return limits.length >= 3;
}

export function validateGolferProfileInput(input: {
  age: string;
  years_playing: string;
  physical_limitations: string;
  no_physical_limitations: boolean;
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

  return {
    ok: true,
    data: { age, years_playing: years, physical_limitations: limitations },
  };
}
