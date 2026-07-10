import { NextRequest, NextResponse } from "next/server";
import { Resend } from "resend";
import { createServiceClient } from "@/lib/supabase/admin";
import { enforceRateLimit } from "@/lib/rate-limit";
import { createClient } from "@/lib/supabase/server";
import { captureServerError } from "@/lib/monitoring";
import { APP_NAME } from "@/lib/brand";

async function notifySupportInbox(args: {
  email: string;
  subject: string;
  message: string;
  userId: string | null;
}): Promise<void> {
  const apiKey = process.env.RESEND_API_KEY?.trim();
  const inbox = process.env.SUPPORT_INBOX_EMAIL?.trim();
  const from = process.env.RESEND_FROM_EMAIL?.trim();
  if (!apiKey || !inbox || !from) {
    console.warn("support_email_not_configured");
    return;
  }

  const resend = new Resend(apiKey);
  const { error } = await resend.emails.send({
    from,
    to: inbox,
    replyTo: args.email,
    subject: `[${APP_NAME} support] ${args.subject}`,
    text: [
      `From: ${args.email}`,
      args.userId ? `User ID: ${args.userId}` : "User ID: (anonymous)",
      "",
      args.message,
    ].join("\n"),
  });

  if (error) {
    throw new Error(error.message || "Resend send failed");
  }
}

export async function POST(request: NextRequest) {
  const limited = await enforceRateLimit(request, {
    scope: "support",
    limit: 5,
    windowSeconds: 3600,
  });
  if (limited) return limited;

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const body = await request.json();
  const email = String(body.email || user?.email || "").trim().toLowerCase();
  const subject = String(body.subject || "").trim();
  const message = String(body.message || "").trim();

  if (!email.includes("@") || email.length > 320) {
    return NextResponse.json({ error: "Enter a valid email address." }, { status: 400 });
  }
  if (subject.length < 3 || subject.length > 160) {
    return NextResponse.json({ error: "Subject must be 3–160 characters." }, { status: 400 });
  }
  if (message.length < 10 || message.length > 4000) {
    return NextResponse.json({ error: "Message must be 10–4,000 characters." }, { status: 400 });
  }

  const service = createServiceClient();
  const { error } = await service.from("support_requests").insert({
    user_id: user?.id ?? null,
    email,
    subject,
    message,
  });
  if (error) {
    console.error("support_request_failed", { code: error.code });
    return NextResponse.json(
      { error: "We could not submit your request. Please try again shortly." },
      { status: 500 }
    );
  }

  try {
    await notifySupportInbox({
      email,
      subject,
      message,
      userId: user?.id ?? null,
    });
  } catch (err) {
    await captureServerError(err, { path: "/api/support", method: "POST" });
  }

  return NextResponse.json({ success: true });
}
