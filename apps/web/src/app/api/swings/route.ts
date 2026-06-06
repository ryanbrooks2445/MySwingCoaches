import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { createServiceClient } from "@/lib/supabase/admin";
import { deleteAllSwingsForUser } from "@/lib/delete-swing";

/** DELETE /api/swings?all=true — remove all swings and history for the signed-in user */
export async function DELETE(request: NextRequest) {
  const all = new URL(request.url).searchParams.get("all") === "true";
  if (!all) {
    return NextResponse.json(
      { error: "Use ?all=true to clear all swing history" },
      { status: 400 }
    );
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const serviceClient = createServiceClient();
  const { deleted, errors } = await deleteAllSwingsForUser(serviceClient, user.id);

  if (errors.length > 0 && deleted === 0) {
    return NextResponse.json({ error: errors[0] }, { status: 500 });
  }

  return NextResponse.json({
    success: true,
    deleted,
    partialErrors: errors.length > 0 ? errors : undefined,
  });
}
