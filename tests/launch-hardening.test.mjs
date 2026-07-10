import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const migrationPath = new URL(
  "../supabase/migrations/008_launch_hardening.sql",
  import.meta.url
);
const workflowMigrationPath = new URL(
  "../supabase/migrations/009_upload_job_workflow.sql",
  import.meta.url
);
const retryMigrationPath = new URL(
  "../supabase/migrations/010_analysis_retry.sql",
  import.meta.url
);
const schedulerMigrationPath = new URL(
  "../supabase/migrations/011_analysis_scheduler.sql",
  import.meta.url
);
const privilegeMigrationPath = new URL(
  "../supabase/migrations/20260619143920_private_function_privileges.sql",
  import.meta.url
);

test("launch migration locks sensitive tables and adds atomic RPCs", async () => {
  const sql = await readFile(migrationPath, "utf8");

  assert.match(sql, /REVOKE UPDATE ON TABLE public\.subscriptions FROM authenticated/i);
  assert.match(sql, /REVOKE UPDATE ON TABLE public\.profiles FROM authenticated/i);
  assert.match(sql, /CREATE OR REPLACE FUNCTION private\.fulfill_checkout_session/i);
  assert.match(sql, /CREATE OR REPLACE FUNCTION private\.reserve_analysis_credit/i);
  assert.match(sql, /CREATE OR REPLACE FUNCTION private\.restore_analysis_credit/i);
  assert.match(sql, /CREATE OR REPLACE FUNCTION private\.complete_analysis/i);
});

test("launch migration enforces one analysis job per report", async () => {
  const sql = await readFile(migrationPath, "utf8");

  assert.match(sql, /CREATE TABLE IF NOT EXISTS public\.analysis_jobs/i);
  assert.match(sql, /report_id UUID NOT NULL UNIQUE/i);
  assert.match(sql, /CREATE OR REPLACE FUNCTION private\.claim_analysis_jobs/i);
});

test("launch migration includes upload cleanup and 30-day retention", async () => {
  const sql = await readFile(migrationPath, "utf8");

  assert.match(sql, /CREATE TABLE IF NOT EXISTS public\.upload_sessions/i);
  assert.match(sql, /CREATE OR REPLACE FUNCTION private\.cleanup_expired_uploads/i);
  assert.match(sql, /INTERVAL '30 days'/i);
});

test("upload workflow registers video, report, and job transactionally", async () => {
  const sql = await readFile(workflowMigrationPath, "utf8");

  assert.match(sql, /CREATE OR REPLACE FUNCTION private\.register_uploaded_swing/i);
  assert.match(sql, /INSERT INTO public\.swing_videos/i);
  assert.match(sql, /INSERT INTO public\.swing_reports/i);
  assert.match(sql, /INSERT INTO public\.analysis_jobs/i);
  assert.match(sql, /UPDATE public\.upload_sessions[\s\S]+status = 'registered'/i);
});

test("analysis retry re-reserves exactly one credit and resets the job", async () => {
  const sql = await readFile(retryMigrationPath, "utf8");

  assert.match(sql, /CREATE OR REPLACE FUNCTION private\.requeue_analysis/i);
  assert.match(sql, /status = 'reserved'/i);
  assert.match(sql, /analyses_used = analyses_used \+ 1/i);
  assert.match(sql, /attempts = 0/i);
});

test("password recovery exchanges the auth code before accepting a new password", async () => {
  const callback = await readFile(
    new URL("../src/app/auth/callback/route.ts", import.meta.url),
    "utf8"
  );
  const resetPage = await readFile(
    new URL("../src/app/reset-password/page.tsx", import.meta.url),
    "utf8"
  );

  assert.match(callback, /exchangeCodeForSession/);
  assert.match(callback, /createRouteHandlerClient/);
  assert.match(resetPage, /reset-password\?mode=update/);
  assert.match(resetPage, /updateUser\(\{\s*password/);
});

test("analysis worker scheduler reads secrets from Vault and runs every minute", async () => {
  const sql = await readFile(schedulerMigrationPath, "utf8");

  assert.match(sql, /vault\.decrypted_secrets/i);
  assert.match(sql, /X-Analysis-Secret/i);
  assert.match(sql, /cron\.schedule/i);
  assert.match(sql, /'\* \* \* \* \*'/);
  assert.doesNotMatch(sql, /change-me-in-production/i);
});

test("login and signup run through rate-limited server routes", async () => {
  const loginRoute = await readFile(
    new URL("../src/app/api/auth/login/route.ts", import.meta.url),
    "utf8"
  );
  const signupRoute = await readFile(
    new URL("../src/app/api/auth/signup/route.ts", import.meta.url),
    "utf8"
  );
  const loginPage = await readFile(new URL("../src/app/login/page.tsx", import.meta.url), "utf8");
  const signupPage = await readFile(new URL("../src/app/signup/page.tsx", import.meta.url), "utf8");

  assert.match(loginRoute, /scope:\s*"auth-login"/);
  assert.match(signupRoute, /scope:\s*"auth-signup"/);
  assert.match(signupRoute, /auth\.signUp/);
  assert.match(signupRoute, /needsEmailConfirmation/);
  assert.match(loginPage, /fetch\("\/api\/auth\/login"/);
  assert.match(signupPage, /fetch\("\/api\/auth\/signup"/);
  assert.match(signupPage, /Check your email/);
});

test("production rate limiting prefers Upstash and falls back to memory", async () => {
  const limiter = await readFile(new URL("../src/lib/rate-limit.ts", import.meta.url), "utf8");
  const env = await readFile(new URL("../src/lib/env.ts", import.meta.url), "utf8");

  assert.match(limiter, /enforceMemoryRateLimit/);
  assert.match(limiter, /isProduction/);
  assert.doesNotMatch(limiter, /Service temporarily unavailable/);
  assert.match(env, /RECOMMENDED_SERVER_ENV/);
  assert.match(env, /"UPSTASH_REDIS_REST_URL"/);
  assert.match(env, /"UPSTASH_REDIS_REST_TOKEN"/);
});

test("all private functions revoke inherited public execution", async () => {
  const sql = await readFile(privilegeMigrationPath, "utf8");

  assert.match(sql, /REVOKE ALL ON ALL FUNCTIONS IN SCHEMA private FROM PUBLIC/i);
  assert.match(sql, /ALTER DEFAULT PRIVILEGES IN SCHEMA private/i);
});

test("failed direct uploads cancel the session", async () => {
  const cancelRoute = await readFile(
    new URL("../src/app/api/swings/upload-cancel/route.ts", import.meta.url),
    "utf8"
  );
  const uploadPage = await readFile(new URL("../src/app/upload/page.tsx", import.meta.url), "utf8");

  assert.match(cancelRoute, /service_restore_analysis_credit/);
  assert.match(cancelRoute, /upload_cancelled/);
  assert.match(cancelRoute, /session\.status === "registered"/);
  assert.match(uploadPage, /fetch\("\/api\/swings\/upload-cancel"/);
  assert.match(uploadPage, /Unexpected end of JSON input/);
  assert.doesNotMatch(uploadPage, /Buy credit/);
  assert.match(uploadPage, /Upload securely & analyze/);
  assert.match(uploadPage, /Upload securely — pay to analyze/);
  assert.match(uploadPage, /role="radiogroup"/);
});

test("direct signed uploads do not rely on Supabase storage JSON parsing", async () => {
  const uploadPage = await readFile(new URL("../src/app/upload/page.tsx", import.meta.url), "utf8");
  const apiReader = await readFile(new URL("../src/lib/api-response.ts", import.meta.url), "utf8");

  assert.match(uploadPage, /function uploadToSignedStorageUrl/);
  assert.match(uploadPage, /\/storage\/v1\/object\/upload\/sign\/swing-videos\//);
  assert.match(uploadPage, /if \(response\.ok\) return/);
  assert.doesNotMatch(uploadPage, /uploadToSignedUrl/);
  assert.match(apiReader, /await response\.text\(\)/);
  assert.match(apiReader, /if \(!text\)/);
});

test("customer-facing forms use safe response parsing", async () => {
  const files = [
    "../src/components/GolferProfileForm.tsx",
    "../src/components/SupportForm.tsx",
    "../src/components/DeleteSwingButton.tsx",
    "../src/app/account/page.tsx",
  ];

  for (const file of files) {
    const source = await readFile(new URL(file, import.meta.url), "utf8");
    assert.match(source, /readApiResponse/);
    assert.doesNotMatch(source, /\.json\(\)/);
  }
});

test("missing monitoring DSN does not block core production routes", async () => {
  const env = await readFile(new URL("../src/lib/env.ts", import.meta.url), "utf8");
  const monitoring = await readFile(new URL("../src/lib/monitoring.ts", import.meta.url), "utf8");

  assert.doesNotMatch(env, /"SENTRY_DSN"/);
  assert.match(monitoring, /if \(!dsn\) return/);
});
