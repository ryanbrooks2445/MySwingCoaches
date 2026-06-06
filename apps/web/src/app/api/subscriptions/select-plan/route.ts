import { NextResponse } from "next/server";

export async function POST() {
  return NextResponse.json(
    { error: "Plan selection is disabled. Purchase analysis credits through Stripe Checkout." },
    { status: 410 }
  );
}
