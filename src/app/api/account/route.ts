import { createHash } from "crypto";
import { NextRequest, NextResponse } from "next/server";
import { createServiceClient } from "@/lib/supabase/admin";
import { enforceRateLimit } from "@/lib/rate-limit";
import { createClient } from "@/lib/supabase/server";

async function removeUserStorage(bucket: string, userId: string) {
  const service = createServiceClient();
  const { data: folders } = await service.storage.from(bucket).list(userId, { limit: 1000 });
  for (const folder of folders ?? []) {
    const prefix = `${userId}/${folder.name}`;
    const { data: files } = await service.storage.from(bucket).list(prefix, { limit: 1000 });
    const paths = (files ?? []).map((file) => `${prefix}/${file.name}`);
    if (paths.length > 0) await service.storage.from(bucket).remove(paths);
  }
}

export async function DELETE(request: NextRequest) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const limited = await enforceRateLimit(request, {
    scope: "account-delete",
    identifier: user.id,
    limit: 3,
    windowSeconds: 3600,
  });
  if (limited) return limited;

  const { confirmation } = await request.json();
  if (confirmation !== "DELETE") {
    return NextResponse.json({ error: "Type DELETE to confirm permanent deletion." }, { status: 400 });
  }

  const lastSignIn = user.last_sign_in_at ? new Date(user.last_sign_in_at).getTime() : 0;
  if (!lastSignIn || Date.now() - lastSignIn > 15 * 60 * 1000) {
    return NextResponse.json(
      { error: "For security, log out and sign in again before deleting your account." },
      { status: 403 }
    );
  }

  const service = createServiceClient();
  const userHash = createHash("sha256").update(user.id).digest("hex");
  const { data: audit } = await service
    .from("account_deletion_audit")
    .insert({ user_id_hash: userHash })
    .select("id")
    .single();

  try {
    await Promise.all([
      removeUserStorage("swing-videos", user.id),
      removeUserStorage("swing-frames", user.id),
    ]);
    const { error } = await service.auth.admin.deleteUser(user.id);
    if (error) throw error;
    if (audit?.id) {
      await service
        .from("account_deletion_audit")
        .update({ status: "completed", completed_at: new Date().toISOString() })
        .eq("id", audit.id);
    }
    return NextResponse.json({ deleted: true });
  } catch (error) {
    if (audit?.id) {
      await service
        .from("account_deletion_audit")
        .update({
          status: "failed",
          error_message: error instanceof Error ? error.message.slice(0, 500) : "Deletion failed",
        })
        .eq("id", audit.id);
    }
    return NextResponse.json(
      { error: "Account deletion could not be completed. Contact support." },
      { status: 500 }
    );
  }
}
