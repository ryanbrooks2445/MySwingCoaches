import { NextRequest, NextResponse } from "next/server";
import { enforceRateLimit } from "@/lib/rate-limit";
import { createClient } from "@/lib/supabase/server";

export async function POST(request: NextRequest) {
  const limited = await enforceRateLimit(request, {
    scope: "auth-signup",
    limit: 10,
    windowSeconds: 15 * 60,
  });
  if (limited) return limited;

  const { email, password, displayName, redirectTo } = await request.json();
  if (
    typeof email !== "string" ||
    typeof password !== "string" ||
    password.length < 8 ||
    typeof displayName !== "string" ||
    displayName.trim().length > 80
  ) {
    return NextResponse.json(
      { error: "Enter a valid email, display name, and password of at least eight characters." },
      { status: 400 }
    );
  }

  const next =
    typeof redirectTo === "string" && redirectTo.startsWith("/") ? redirectTo : "/dashboard";
  const supabase = await createClient();
  const { data, error } = await supabase.auth.signUp({
    email: email.trim(),
    password,
    options: {
      data: { display_name: displayName.trim() },
      emailRedirectTo: `${request.nextUrl.origin}/auth/callback?next=${encodeURIComponent(next)}`,
    },
  });
  if (error) {
    return NextResponse.json({ error: "We could not create that account." }, { status: 400 });
  }

  return NextResponse.json({ success: true, requiresConfirmation: !data.session });
}
