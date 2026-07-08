import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const code = url.searchParams.get("code");
  const oauthError = url.searchParams.get("error");
  const requestedNext = url.searchParams.get("next") || "/dashboard";
  const next = requestedNext.startsWith("/") ? requestedNext : "/dashboard";

  if (oauthError) {
    return NextResponse.redirect(new URL("/login?error=oauth_failed", url.origin));
  }

  if (!code) {
    return NextResponse.redirect(new URL("/login?error=invalid_link", url.origin));
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.exchangeCodeForSession(code);
  if (error) {
    return NextResponse.redirect(new URL("/login?error=expired_link", url.origin));
  }

  return NextResponse.redirect(new URL(next, url.origin));
}
