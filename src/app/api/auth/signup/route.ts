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

  const normalizedEmail = email.trim();
  const trimmedName = displayName.trim();
  const next =
    typeof redirectTo === "string" && redirectTo.startsWith("/") ? redirectTo : "/dashboard";

  const appUrl = (process.env.NEXT_PUBLIC_APP_URL || request.nextUrl.origin).replace(/\/$/, "");
  const emailRedirectTo = `${appUrl}/auth/callback?next=${encodeURIComponent(next)}`;

  const supabase = await createClient();
  const { data, error: signUpError } = await supabase.auth.signUp({
    email: normalizedEmail,
    password,
    options: {
      data: { display_name: trimmedName },
      emailRedirectTo,
    },
  });

  if (signUpError) {
    const message = signUpError.message.toLowerCase();
    if (message.includes("already") || message.includes("registered")) {
      return NextResponse.json(
        { error: "An account with this email already exists. Try logging in instead." },
        { status: 400 }
      );
    }
    return NextResponse.json({ error: "We could not create that account." }, { status: 400 });
  }

  // Supabase returns a user with empty identities when the email is already registered
  // and email confirmation is enabled (anti-enumeration). Treat as existing account.
  if (data.user && Array.isArray(data.user.identities) && data.user.identities.length === 0) {
    return NextResponse.json(
      { error: "An account with this email already exists. Try logging in instead." },
      { status: 400 }
    );
  }

  // Session present means email confirmation is disabled in the project — user is signed in.
  if (data.session) {
    return NextResponse.json({ success: true, redirectTo: next });
  }

  return NextResponse.json({
    success: true,
    needsEmailConfirmation: true,
    email: normalizedEmail,
  });
}
