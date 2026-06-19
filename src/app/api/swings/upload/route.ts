import { NextResponse } from "next/server";

export async function POST() {
  return NextResponse.json(
    { error: "This upload method has been retired. Refresh the page and try again." },
    { status: 410 }
  );
}
