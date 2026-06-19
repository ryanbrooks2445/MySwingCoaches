import { NextRequest, NextResponse } from "next/server";
import { createServiceClient } from "@/lib/supabase/admin";
import { createClient } from "@/lib/supabase/server";
import {
  isGolferProfileComplete,
  validateGolferProfileInput,
  type GolferProfileFields,
} from "@/lib/player-profile";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { data: profile, error } = await supabase
    .from("profiles")
    .select("age, years_playing, physical_limitations, average_9_score, typical_miss, primary_goal")
    .eq("id", user.id)
    .single();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  const fields: GolferProfileFields = {
    age: profile?.age ?? null,
    years_playing: profile?.years_playing ?? null,
    physical_limitations: profile?.physical_limitations ?? null,
    average_9_score: profile?.average_9_score ?? null,
    typical_miss: profile?.typical_miss ?? null,
    primary_goal: profile?.primary_goal ?? null,
  };

  return NextResponse.json({
    profile: fields,
    complete: isGolferProfileComplete(fields),
  });
}

export async function PATCH(request: NextRequest) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await request.json();
  const validated = validateGolferProfileInput({
    age: String(body.age ?? ""),
    years_playing: String(body.years_playing ?? ""),
    physical_limitations: String(body.physical_limitations ?? ""),
    no_physical_limitations: Boolean(body.no_physical_limitations),
    average_9_score: String(body.average_9_score ?? ""),
    typical_miss: String(body.typical_miss ?? ""),
    primary_goal: String(body.primary_goal ?? ""),
  });

  if (!validated.ok) {
    return NextResponse.json({ error: validated.error }, { status: 400 });
  }

  const service = createServiceClient();
  const { error } = await service
    .from("profiles")
    .update({
      age: validated.data.age,
      years_playing: validated.data.years_playing,
      physical_limitations: validated.data.physical_limitations,
      average_9_score: validated.data.average_9_score,
      typical_miss: validated.data.typical_miss,
      primary_goal: validated.data.primary_goal,
    })
    .eq("id", user.id);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({
    profile: validated.data,
    complete: isGolferProfileComplete(validated.data),
  });
}
