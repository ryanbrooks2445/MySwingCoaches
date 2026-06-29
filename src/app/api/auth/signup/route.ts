import { NextRequest, NextResponse } from "next/server";
import { enforceRateLimit } from "@/lib/rate-limit";
import { createServiceClient } from "@/lib/supabase/admin";
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
  const service = createServiceClient();

  const { error: createError } = await service.auth.admin.createUser({
    email: normalizedEmail,
    password,
    email_confirm: true,
    user_metadata: { display_name: trimmedName },
  });

  if (createError) {
    const message = createError.message.toLowerCase();
    if (message.includes("already") || message.includes("registered")) {
      return NextResponse.json(
        { error: "An account with this email already exists. Try logging in instead." },
        { status: 400 }
      );
    }
    return NextResponse.json({ error: "We could not create that account." }, { status: 400 });
  }

  const supabase = await createClient();
  const { error: signInError } = await supabase.auth.signInWithPassword({
    email: normalizedEmail,
    password,
  });
  if (signInError) {
    return NextResponse.json(
      { error: "Account created, but sign-in failed. Try logging in." },
      { status: 400 }
    );
  }

  const next =
    typeof redirectTo === "string" && redirectTo.startsWith("/") ? redirectTo : "/dashboard";

  return NextResponse.json({ success: true, redirectTo: next });
}
