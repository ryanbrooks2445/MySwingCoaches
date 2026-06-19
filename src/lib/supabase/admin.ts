import { createClient } from "@supabase/supabase-js";
import { assertServerEnvironment } from "@/lib/env";

export function createServiceClient() {
  assertServerEnvironment();
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { persistSession: false, autoRefreshToken: false } }
  );
}
