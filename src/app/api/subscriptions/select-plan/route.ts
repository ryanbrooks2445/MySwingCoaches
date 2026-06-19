import { NextResponse } from "next/server";

export async function POST() {
  return NextResponse.json({ error: "Subscription plans are not offered." }, { status: 410 });
}
