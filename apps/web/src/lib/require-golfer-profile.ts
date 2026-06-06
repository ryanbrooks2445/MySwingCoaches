import { createServiceClient } from "@/lib/supabase/admin";
import { isGolferProfileComplete } from "@/lib/player-profile";

export async function requireGolferProfile(userId: string): Promise<{ ok: true } | { ok: false; error: string }> {
  const supabase = createServiceClient();
  const { data: profile, error } = await supabase
    .from("profiles")
    .select("age, years_playing, physical_limitations")
    .eq("id", userId)
    .single();

  if (error || !profile) {
    return {
      ok: false,
      error: "Complete your golfer profile (age, experience, physical constraints) before uploading.",
    };
  }

  if (
    !isGolferProfileComplete({
      age: profile.age,
      years_playing: profile.years_playing,
      physical_limitations: profile.physical_limitations,
    })
  ) {
    return {
      ok: false,
      error: "Complete your golfer profile (age, experience, physical constraints) before uploading.",
    };
  }

  return { ok: true };
}
