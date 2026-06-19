import { NextRequest, NextResponse } from "next/server";
import { enforceRateLimit } from "@/lib/rate-limit";
import { createClient } from "@/lib/supabase/server";

export async function POST(request: NextRequest) {
  const limited = await enforceRateLimit(request, {
    scope: "auth-login",
    limit: 10,
    windowSeconds: 15 * 60,
  });
  if (limited) return limited;

  const { email, password } = await request.json();
  if (typeof email !== "string" || typeof password !== "string") {
    return NextResponse.json({ error: "Enter your email and password." }, { status: 400 });
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({
    email: email.trim(),
    password,
  });
  if (error) {
    return NextResponse.json(
      { error: "Email or password is incorrect, or the email is not confirmed." },
      { status: 401 }
    );
  }

  return NextResponse.json({ success: true });
}
