import { createServiceClient } from "@/lib/supabase/admin";
import { isGolferProfileComplete } from "@/lib/player-profile";

export async function requireGolferProfile(userId: string): Promise<{ ok: true } | { ok: false; error: string }> {
  const supabase = createServiceClient();
  const { data: profile, error } = await supabase
    .from("profiles")
    .select("age, years_playing, physical_limitations, average_9_score, typical_miss, primary_goal")
    .eq("id", userId)
    .single();

  if (error || !profile) {
    return {
      ok: false,
      error: "Complete your golfer profile before uploading.",
    };
  }

  if (
    !isGolferProfileComplete({
      age: profile.age,
      years_playing: profile.years_playing,
      physical_limitations: profile.physical_limitations,
      average_9_score: profile.average_9_score,
      typical_miss: profile.typical_miss,
      primary_goal: profile.primary_goal,
    })
  ) {
    return {
      ok: false,
      error: "Complete your golfer profile before uploading.",
    };
  }

  return { ok: true };
}
