-- Dispatch queued analysis jobs without exposing the worker URL or shared secret.
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net WITH SCHEMA extensions;

CREATE OR REPLACE FUNCTION private.dispatch_analysis_worker()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, private, vault, net
AS $$
DECLARE
  worker_url text;
  worker_secret text;
BEGIN
  SELECT decrypted_secret
  INTO worker_url
  FROM vault.decrypted_secrets
  WHERE name = 'analysis_service_url'
  LIMIT 1;

  SELECT decrypted_secret
  INTO worker_secret
  FROM vault.decrypted_secrets
  WHERE name = 'analysis_service_secret'
  LIMIT 1;

  IF worker_url IS NULL OR worker_secret IS NULL THEN
    RAISE WARNING 'Analysis scheduler secrets are not configured in Vault';
    RETURN;
  END IF;

  PERFORM net.http_post(
    url := rtrim(worker_url, '/') || '/jobs/drain?limit=2',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'X-Analysis-Secret', worker_secret
    ),
    body := '{}'::jsonb,
    timeout_milliseconds := 10000
  );
END;
$$;

REVOKE ALL ON FUNCTION private.dispatch_analysis_worker() FROM PUBLIC, anon, authenticated;

DO $$
DECLARE
  existing_job bigint;
BEGIN
  SELECT jobid
  INTO existing_job
  FROM cron.job
  WHERE jobname = 'analysis-worker-every-minute'
  LIMIT 1;

  IF existing_job IS NOT NULL THEN
    PERFORM cron.unschedule(existing_job);
  END IF;
END;
$$;

SELECT cron.schedule(
  'analysis-worker-every-minute',
  '* * * * *',
  'SELECT private.dispatch_analysis_worker();'
);
